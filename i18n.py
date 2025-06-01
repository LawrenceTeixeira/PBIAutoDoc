"""
Internationalization (i18n) module for the Streamlit application.
Provides multi-language support with persistent language selection.
"""

import json
import os
import streamlit as st
from typing import Dict, Any, Optional
from pathlib import Path


class TranslationManager:
    """
    Manages translations for the application with support for multiple languages.
    
    Features:
    - Dynamic language switching
    - Session state persistence    - Fallback to default language
    - Easy extensibility for new languages
    """
    
    def __init__(self, locales_dir: str = "locales", default_language: str = "en"):
        """
        Initialize the translation manager.
        
        Args:
            locales_dir: Directory containing translation files
            default_language: Default language code (ISO 639-1)
        """
        self.locales_dir = Path(locales_dir)
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.available_languages: Dict[str, str] = {}
        
        # Initialize session state for language
        if 'language' not in st.session_state:
            st.session_state.language = default_language
            
        self._load_available_languages()
        self._load_translations()
    
    def _load_available_languages(self) -> None:
        """Load available languages from the locales directory."""
        if not self.locales_dir.exists():
            st.error(f"Locales directory '{self.locales_dir}' not found!")
            return
            
        for lang_dir in self.locales_dir.iterdir():
            if lang_dir.is_dir():
                translation_file = lang_dir / "translation.json"
                if translation_file.exists():
                    try:
                        with open(translation_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Get language display name from translation file
                            lang_name = data.get('language_name', lang_dir.name)
                            self.available_languages[lang_dir.name] = lang_name
                    except json.JSONDecodeError as e:
                        st.warning(f"Error loading language {lang_dir.name}: {e}")
    
    def _load_translations(self) -> None:
        """Load all translation files into memory."""
        for lang_code in self.available_languages.keys():
            translation_file = self.locales_dir / lang_code / "translation.json"
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                st.warning(f"Error loading translations for {lang_code}: {e}")
    
    def get_current_language(self) -> str:
        """Get the current language from session state."""
        return st.session_state.get('language', self.default_language)
    
    def set_language(self, language_code: str) -> None:
        """
        Set the current language.
        
        Args:
            language_code: Language code to set
        """
        if language_code in self.available_languages:
            st.session_state.language = language_code
            st.rerun()
        else:
            st.error(f"Language '{language_code}' not available!")
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.
        
        Args:
            key: Translation key (supports nested keys with dot notation)
            **kwargs: Variables for string formatting
            
        Returns:
            Translated string or the key if translation not found
        """
        current_lang = self.get_current_language()
        
        # Try current language first
        translation = self._get_nested_value(
            self.translations.get(current_lang, {}), key
        )
        
        # Fallback to default language if translation not found
        if translation is None and current_lang != self.default_language:
            translation = self._get_nested_value(
                self.translations.get(self.default_language, {}), key
            )
        
        # Return key if no translation found
        if translation is None:
            translation = key
            
        # Format string with provided variables
        try:
            return translation.format(**kwargs) if kwargs else translation
        except (KeyError, ValueError) as e:
            st.warning(f"Translation formatting error for key '{key}': {e}")
            return translation
    
    def translate_for_language(self, key: str, language: str, **kwargs) -> str:
        """
        Translate a key to a specific language.
        
        Args:
            key: Translation key (supports nested keys with dot notation)
            language: Language code to translate to
            **kwargs: Variables for string formatting
            
        Returns:
            Translated string or the key if translation not found
        """
        # Try specified language first
        translation = self._get_nested_value(
            self.translations.get(language, {}), key
        )
        
        # Fallback to default language if translation not found
        if translation is None and language != self.default_language:
            translation = self._get_nested_value(
                self.translations.get(self.default_language, {}), key
            )
        
        # Return key if no translation found
        if translation is None:
            translation = key
            
        # Format string with provided variables
        try:
            return translation.format(**kwargs) if kwargs else translation
        except (KeyError, ValueError) as e:
            # Note: Can't use st.warning here as this might be called outside Streamlit context
            return translation
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """
        Get a nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search in
            key: Dot-separated key path
            
        Returns:
            Value if found, None otherwise
        """
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
                
        return current if isinstance(current, str) else None
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get available languages.
          Returns:
            Dictionary mapping language codes to display names
        """
        return self.available_languages.copy()
    
    def language_selector(self, key: str = "language_selector", use_flags: bool = True, flag_style: str = "emoji") -> None:
        """
        Display a language selector widget with optional flag support.
        
        Args:
            key: Unique key for the selectbox widget
            use_flags: Whether to show flags in the selector
            flag_style: Either "emoji" for flag emojis or "image" for custom flag images
        """
        if not self.available_languages:
            st.error("No languages available!")
            return
            
        current_lang = self.get_current_language()
        
        if flag_style == "image" and use_flags:
            # Use custom HTML/CSS for image-based flags
            self._render_image_flag_selector(key, current_lang)
        else:            # Use standard selectbox (with emoji flags if enabled)
            languages = list(self.available_languages.keys())
            
            try:
                current_index = languages.index(current_lang)
            except ValueError:
                current_index = 0
                
            if use_flags and flag_style == "emoji":
                # Display names already include emoji flags
                display_func = lambda x: self.available_languages[x]
            else:
                # Remove flags from display names if flags are disabled
                display_func = lambda x: self.available_languages[x].split(' ', 1)[-1] if ' ' in self.available_languages[x] else self.available_languages[x]
                
            selected_lang = st.selectbox(
                label=self.translate("ui.language_selector"),
                options=languages,
                format_func=display_func,
                index=current_index,
                key=key
            )
            
            if selected_lang != current_lang:
                self.set_language(selected_lang)
    
    def _render_image_flag_selector(self, key: str, current_lang: str) -> None:
        """
        Render a custom language selector with flag images.
        
        Args:
            key: Unique key for the selector
            current_lang: Currently selected language
        """
        # Flag mapping for custom images
        flag_mapping = {
            "en": {"flag": "🇺🇸", "image": "us.png"},
            "pt-BR": {"flag": "🇧🇷", "image": "br.png"}, 
            "es": {"flag": "🇪🇸", "image": "es.png"}
        }
          # st.markdown("**" + self.translate("ui.language_selector") + "**")
        
        # Add CSS for consistent language selector button sizing
        st.markdown(f"""
        <style>
        /* Target language selector buttons specifically using the key pattern */
        [data-testid="stColumns"] div[data-testid="column"] button[key*="{key}"] {{
            width: 100% !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: center !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Create columns for language options
        cols = st.columns(len(self.available_languages))
        
        for i, (lang_code, lang_name) in enumerate(self.available_languages.items()):
            with cols[i]:
                flag_info = flag_mapping.get(lang_code, {"flag": "🌐", "image": None})
                  # Check if custom flag image exists
                flag_path = Path("assets/flags") / flag_info["image"] if flag_info["image"] else None
                
                if flag_path and flag_path.exists():
                    # Use custom image
                    clean_name = lang_name.split(' ', 1)[-1] if ' ' in lang_name else lang_name
                    # Standardize button text length for consistent sizing
                    if clean_name == "Portuguese":
                        clean_name = "Brazil"  # Shorter Portuguese name
                    button_label = f"![flag](data:image/png;base64,{self._get_base64_image(flag_path)}) {clean_name}"
                else:
                    # Fallback to emoji
                    clean_name = lang_name.split(' ', 1)[-1] if ' ' in lang_name else lang_name
                    # Standardize button text length for consistent sizing
                    if clean_name == "Portuguese":
                        clean_name = "Português"  # Shorter Portuguese name
                    button_label = f"{flag_info['flag']} {clean_name}"
                
                if st.button(
                    button_label,
                    key=f"{key}_{lang_code}",
                    use_container_width=True,
                    type="primary" if lang_code == current_lang else "secondary"
                ):
                    self.set_language(lang_code)
                    st.rerun()
    
    def _get_base64_image(self, image_path: Path) -> str:
        """
        Convert image to base64 string for inline display.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        import base64
        
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except Exception:
            return ""


# Global translation manager instance
_translation_manager: Optional[TranslationManager] = None


def init_i18n(locales_dir: str = "locales", default_language: str = "en") -> TranslationManager:
    """
    Initialize the global translation manager.
    
    Args:
        locales_dir: Directory containing translation files
        default_language: Default language code
        
    Returns:
        TranslationManager instance
    """
    global _translation_manager
    _translation_manager = TranslationManager(locales_dir, default_language)
    return _translation_manager


def get_translation_manager() -> TranslationManager:
    """
    Get the global translation manager instance.
    
    Returns:
        TranslationManager instance
        
    Raises:
        RuntimeError: If translation manager not initialized
    """
    if _translation_manager is None:
        raise RuntimeError("Translation manager not initialized. Call init_i18n() first.")
    return _translation_manager


def t(key: str, **kwargs) -> str:
    """
    Convenient shorthand for translation.
    
    Args:
        key: Translation key
        **kwargs: Variables for string formatting
        
    Returns:
        Translated string
    """
    return get_translation_manager().translate(key, **kwargs)


def set_language(language_code: str) -> None:
    """
    Set the current language.
    
    Args:
        language_code: Language code to set
    """
    get_translation_manager().set_language(language_code)


def language_selector(key: str = "language_selector", use_flags: bool = True, flag_style: str = "emoji") -> None:
    """
    Display a language selector widget with optional flag support.
    
    Args:
        key: Unique key for the selectbox widget
        use_flags: Whether to show flags in the selector
        flag_style: Either "emoji" for flag emojis or "image" for custom flag images
    """
    get_translation_manager().language_selector(key, use_flags, flag_style)


def get_current_language() -> str:
    """Get the current language code."""
    return get_translation_manager().get_current_language()


def get_available_languages() -> Dict[str, str]:
    """Get available languages."""
    return get_translation_manager().get_available_languages()


def translate_to_language(key: str, language: str, **kwargs) -> str:
    """
    Translate a key to a specific language.
    
    Args:
        key: Translation key
        language: Language code
        **kwargs: Variables for string formatting
        
    Returns:
        Translated string
    """
    return get_translation_manager().translate_for_language(key, language, **kwargs)

#!/usr/bin/env python3
"""
Demo script to test different language selector flag styles.
Run this to see how the language selector looks with different configurations.
"""

import streamlit as st
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from i18n import init_i18n, language_selector, t

def main():
    st.set_page_config(
        page_title="Language Selector Demo", 
        page_icon="🌍",
        layout="wide"
    )
    
    # Initialize i18n
    init_i18n()
    
    st.title("🌍 Language Selector Demo")
    st.write("This demo shows different styles of the language selector with flags.")
    
    st.markdown("---")
    
    # Style 1: Default with emoji flags
    st.subheader("Style 1: Selectbox with Emoji Flags (Default)")
    st.write("This uses the standard Streamlit selectbox with flag emojis in the language names.")
    language_selector("demo_emoji", use_flags=True, flag_style="emoji")
    
    st.markdown("---")
    
    # Style 2: Without flags
    st.subheader("Style 2: Selectbox without Flags")
    st.write("This shows language names only, without any flag indicators.")
    language_selector("demo_no_flags", use_flags=False)
    
    st.markdown("---")
    
    # Style 3: Button-based with image flags (if available)
    st.subheader("Style 3: Button-based with Image Flags")
    st.write("This uses custom buttons with flag images (falls back to emojis if images not available).")
    language_selector("demo_image", use_flags=True, flag_style="image")
    
    st.markdown("---")
    
    # Show current language selection
    st.subheader("Current Selection")
    current_lang = st.session_state.get('language', 'en')
    st.info(f"**Current Language:** {current_lang}")
    st.success(f"**Translated Text:** {t('ui.app_title')}")
    
    # Instructions
    st.markdown("---")
    st.subheader("🛠️ Implementation Guide")
    
    with st.expander("How to use in your app.py"):
        st.code("""
# Option 1: Default emoji flags (recommended)
language_selector("main_language_selector")

# Option 2: Explicitly use emoji flags  
language_selector("main_language_selector", use_flags=True, flag_style="emoji")

# Option 3: No flags
language_selector("main_language_selector", use_flags=False)

# Option 4: Custom image flags (requires flag images in assets/flags/)
language_selector("main_language_selector", use_flags=True, flag_style="image")
        """, language="python")
    
    with st.expander("How to add flag images"):
        st.markdown("""
        1. **Download the utility script result:**
           ```bash
           python download_flags.py
           ```
        
        2. **Or manually download flags to `assets/flags/`:**
           - `us.png` - for English
           - `br.png` - for Portuguese (Brazil)  
           - `es.png` - for Spanish
        
        3. **Use image style:**
           ```python
           language_selector("selector_key", flag_style="image")
           ```
        """)

if __name__ == "__main__":
    main()

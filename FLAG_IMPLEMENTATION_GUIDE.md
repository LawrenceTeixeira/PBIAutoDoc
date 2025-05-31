# Language Selector with Flags - Implementation Guide

You now have a language selector with flag support! Here are the different ways you can implement it:

## Quick Start (Recommended)

The easiest way is to use flag emojis, which are already implemented:

```python
# In your app.py, the current call:
language_selector("main_language_selector")
```

This will now show:
- 🇺🇸 English  
- 🇪🇸 Español
- 🇧🇷 Português (Brasil)

## Available Options

### 1. Emoji Flags (Default - Already Working!)
```python
language_selector("main_language_selector", use_flags=True, flag_style="emoji")
```
- ✅ Works immediately
- ✅ No additional files needed
- ✅ Cross-platform compatible
- ✅ Lightweight

### 2. No Flags
```python
language_selector("main_language_selector", use_flags=False)
```
Shows only text: "English", "Español", "Português (Brasil)"

### 3. Custom Image Flags
```python
language_selector("main_language_selector", use_flags=True, flag_style="image")
```
- Requires flag images in `assets/flags/` directory
- Falls back to emoji flags if images not found
- More customizable appearance

## Adding Custom Flag Images (Optional)

If you want to use custom flag images instead of emojis:

### Step 1: Download flag images
```bash
# Run the automatic downloader
python download_flags.py
```

### Step 2: Update your app.py
```python
# Change this line in configure_app():
language_selector("main_language_selector", flag_style="image")
```

### Manual flag download
If the automatic downloader doesn't work, manually download these files to `assets/flags/`:
- [US Flag](https://flagcdn.com/32x24/us.png) → `assets/flags/us.png`
- [Brazil Flag](https://flagcdn.com/32x24/br.png) → `assets/flags/br.png` 
- [Spain Flag](https://flagcdn.com/32x24/es.png) → `assets/flags/es.png`

## Testing

Run the demo to see all flag styles:
```bash
streamlit run language_selector_demo.py
```

## Current Status

✅ **Emoji flags are already working!** Just restart your Streamlit app to see them.

The language selector now shows:
- 🇺🇸 English
- 🇪🇸 Español  
- 🇧🇷 Português (Brasil)

## Adding More Languages

To add a new language with flags:

1. Create the translation directory: `locales/[language-code]/`
2. Add `translation.json` with all required keys
3. Include the flag emoji in the `language_name` field:
   ```json
   {
     "language_name": "🇫🇷 Français",
     "ui": {
       // ... translations
     }
   }
   ```

The i18n system will automatically detect and include the new language!

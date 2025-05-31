# Flag Images Setup

This directory should contain flag images for the language selector.

## Required Images:

- `us.png` - United States flag for English
- `br.png` - Brazil flag for Portuguese  
- `es.png` - Spain flag for Spanish

## Recommended Specifications:

- **Size**: 32x24 pixels or 64x48 pixels
- **Format**: PNG with transparency
- **Style**: Consistent flat design or realistic

## Where to get flag images:

1. **Free sources:**
   - [Flaticon](https://www.flaticon.com/free-icons/flags)
   - [IconFinder](https://www.iconfinder.com/icon-sets/flags)
   - [FlagCDN](https://flagcdn.com/) - Direct links to flag images

2. **Using FlagCDN (recommended):**
   ```
   US Flag: https://flagcdn.com/32x24/us.png
   Brazil Flag: https://flagcdn.com/32x24/br.png
   Spain Flag: https://flagcdn.com/32x24/es.png
   ```

## Usage in code:

The language selector will automatically detect these images and use them when `flag_style="image"` is set:

```python
# In app.py
language_selector("main_language_selector", use_flags=True, flag_style="image")
```

If images are not found, it will automatically fallback to emoji flags.

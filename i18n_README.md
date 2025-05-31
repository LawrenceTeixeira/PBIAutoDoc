# Internationalization (i18n) System

This Power BI Documentation application now supports multiple languages through a comprehensive internationalization system.

## Supported Languages

- **English** - `en` (Default)
- **Portuguese (Brazil)** - `pt-BR`
- **Spanish** - `es`

## Features

- **Persistent Language Selection**: Language preference is saved in Streamlit session state
- **Dynamic Language Switching**: Users can change language at any time using the language selector
- **Fallback System**: Missing translations automatically fall back to Portuguese (default language)
- **Variable Substitution**: Support for dynamic content insertion using `{variable}` syntax
- **Nested Key Support**: Translations are organized hierarchically with dot notation access

## File Structure

```
locales/
├── en/
│   └── translation.json    # English translations (default)
├── pt-BR/
│   └── translation.json    # Portuguese translations  
└── es/
    └── translation.json    # Spanish translations
i18n.py                     # Translation system core
```

## Usage

### Initializing the System

```python
from i18n import init_i18n, t, language_selector

# Initialize the i18n system (call once at app startup)
init_i18n()
```

### Using Translations

```python
# Simple translation
title = t('ui.app_title')

# Translation with variable substitution
message = t('messages.error_loading_file', error="File not found")

# Translation with fallback
description = t('ui.some_key')  # Falls back to Portuguese if key not found
```

### Language Selector Component

```python
# Add language selector to your interface
language_selector("unique_key")
```

## Translation Keys Organization

### UI Elements (`ui.*`)
- Application titles, labels, buttons, form elements
- Navigation and interface components

### Messages (`messages.*`)
- Success, error, and informational messages
- Processing status messages

### Documentation (`documentation.*`)
- Content related to report documentation
- Table headers, field labels

### Detailed Description (`detailed_description.*`)
- Application description and help text
- Feature explanations

### Chat (`chat.*`)
- Chat interface labels and messages
- System prompts and responses

### Errors (`errors.*`)
- Error messages for different failure scenarios
- Validation messages

## Adding New Languages

The i18n system automatically detects new languages by scanning the `locales/` directory. To add a new language:

1. **Create language directory**: Create a new folder in `locales/` with the appropriate language code:
   - Use ISO 639-1 codes when possible (e.g., `fr` for French, `de` for German)
   - Use extended codes for regional variants (e.g., `pt-BR` for Brazilian Portuguese, `es-MX` for Mexican Spanish)

2. **Create translation file**: Copy an existing `translation.json` file to your new language folder:
   ```bash
   cp locales/en/translation.json locales/fr/translation.json
   ```

3. **Translate content**: Update all the values in your new `translation.json` file while keeping the keys unchanged:
   - Set `language_name` to the native name of the language
   - Translate all UI text, messages, and documentation strings
   - Maintain the same JSON structure and key hierarchy

4. **Test translations**: The language will automatically appear in the language selector when you restart the application

Example for French (`locales/fr/translation.json`):
```json
{
  "language_name": "Français",
  "ui": {
    "app_title": "Documenteur Power BI - Mes Feuilles de Calcul - 2025",
    "generate_doc": "Générer la Documentation",
    ...
  },
  ...
}
```

### Language Detection
The system automatically:
- Scans the `locales/` directory for subdirectories
- Loads `translation.json` from each valid language directory  
- Extracts the display name from the `language_name` key
- Makes all detected languages available in the language selector
    "app_title": "Documenteur Power BI - Mes Feuilles de Calcul - 2025",
    ...
  }
}
```

## Adding New Translation Keys

1. Add the key to all language files
2. Use the key in your code with `t('category.key_name')`

Example:
```json
// In translation.json files
{
  "ui": {
    "new_button": "New Button Text"
  }
}
```

```python
# In Python code
button_text = t('ui.new_button')
```

## Best Practices

1. **Consistent Key Naming**: Use descriptive, hierarchical key names
2. **Variable Placeholders**: Use clear variable names in `{variable}` format
3. **Complete Translations**: Ensure all languages have the same keys
4. **Context**: Group related translations under appropriate categories
5. **Testing**: Test language switching thoroughly

## Implementation Details

### TranslationManager Class
- Manages language state and translation loading
- Handles fallback logic
- Provides thread-safe translation access

### Session State Integration
- Language preference stored in `st.session_state['language']`
- Automatic persistence across page reloads
- Independent language selection per session

### Error Handling
- Graceful fallback for missing translation files
- Warning logs for missing keys
- Default language fallback for missing translations

## Maintenance

To maintain the i18n system:

1. **Keep translations synchronized** - when adding new keys, update all language files
2. **Test language switching** - ensure all interface elements translate correctly
3. **Review translation quality** - periodically review translations for accuracy
4. **Monitor logs** - check for missing translation warnings

## Troubleshooting

### Common Issues

1. **Missing translations**: Check console for warning messages about missing keys
2. **Language not switching**: Ensure `init_i18n()` is called before any `t()` calls
3. **Variables not substituting**: Check variable names match exactly between code and JSON

### Debug Mode

Enable debug logging by checking the console for translation warnings and missing key messages.

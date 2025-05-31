#!/usr/bin/env python3
"""
Translation validation script for PBIAutoDoc i18n system.
This script checks for missing translations and validates the translation files.
"""

import json
import os
from pathlib import Path

def load_translation_file(file_path):
    """Load a translation JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_all_keys(data, prefix=''):
    """Recursively get all translation keys from a nested dictionary."""
    keys = set()
    for key, value in data.items():
        if isinstance(value, dict):
            keys.update(get_all_keys(value, f"{prefix}{key}."))
        else:
            keys.add(f"{prefix}{key}")
    return keys

def validate_translations():
    """Validate translation files for consistency."""
    locales_dir = Path(__file__).parent / 'locales'
    
    if not locales_dir.exists():
        print("❌ Locales directory not found!")
        return False
    
    # Find all language directories
    language_dirs = [d for d in locales_dir.iterdir() if d.is_dir()]
    
    if not language_dirs:
        print("❌ No language directories found!")
        return False
    
    print(f"🔍 Found {len(language_dirs)} language(s): {[d.name for d in language_dirs]}")
    
    # Load all translation files
    translations = {}
    all_keys = set()
    
    for lang_dir in language_dirs:
        translation_file = lang_dir / 'translation.json'
        if translation_file.exists():
            data = load_translation_file(translation_file)
            if data:
                translations[lang_dir.name] = data
                keys = get_all_keys(data)
                all_keys.update(keys)
                print(f"✅ {lang_dir.name}: {len(keys)} keys loaded")
            else:
                print(f"❌ {lang_dir.name}: Failed to load translation file")
        else:
            print(f"❌ {lang_dir.name}: translation.json not found")
    
    if not translations:
        print("❌ No valid translation files found!")
        return False
    
    # Check for missing keys across languages
    print(f"\n🔍 Validating {len(all_keys)} total keys across all languages...")
    
    missing_keys = {}
    for lang, data in translations.items():
        lang_keys = get_all_keys(data)
        missing = all_keys - lang_keys
        if missing:
            missing_keys[lang] = missing
    
    # Report results
    if missing_keys:
        print("\n❌ Missing translations found:")
        for lang, keys in missing_keys.items():
            print(f"  {lang}: {len(keys)} missing keys")
            for key in sorted(keys)[:5]:  # Show first 5 missing keys
                print(f"    - {key}")
            if len(keys) > 5:
                print(f"    ... and {len(keys) - 5} more")
        return False
    else:
        print("\n✅ All languages have complete translations!")
        
    # Check for unused keys (keys that might be in translations but not used in code)
    print("\n🔍 Checking for potentially unused keys...")
    app_file = Path(__file__).parent / 'app.py'
    if app_file.exists():
        with open(app_file, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        unused_keys = []
        for key in sorted(all_keys):
            # Simple check - look for the key in the app file
            if f"'{key}'" not in app_content and f'"{key}"' not in app_content:
                unused_keys.append(key)
        
        if unused_keys:
            print(f"⚠️  Found {len(unused_keys)} potentially unused keys:")
            for key in unused_keys[:10]:  # Show first 10
                print(f"    - {key}")
            if len(unused_keys) > 10:
                print(f"    ... and {len(unused_keys) - 10} more")
        else:
            print("✅ All keys appear to be used in the application")
    
    print(f"\n📊 Translation Summary:")
    print(f"  Languages: {len(translations)}")
    print(f"  Total keys: {len(all_keys)}")
    print(f"  Status: {'✅ Valid' if not missing_keys else '❌ Issues found'}")
    
    return len(missing_keys) == 0

if __name__ == "__main__":
    print("🌐 PBIAutoDoc Translation Validator")
    print("=" * 40)
    
    if validate_translations():
        print("\n🎉 Translation validation passed!")
        exit(0)
    else:
        print("\n💥 Translation validation failed!")
        exit(1)

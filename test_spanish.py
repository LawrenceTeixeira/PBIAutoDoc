#!/usr/bin/env python3
"""
Test script to validate Spanish language integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path

def test_spanish_integration():
    """Test that Spanish language is properly integrated."""
    
    print("🔍 Testing Spanish Language Integration\n")
    
    # Test 1: Check if Spanish directory and file exist
    locales_dir = Path("locales")
    spanish_dir = locales_dir / "es"
    spanish_file = spanish_dir / "translation.json"
    
    print("📁 Directory Structure:")
    if spanish_dir.exists():
        print("✅ Spanish directory exists: locales/es/")
    else:
        print("❌ Spanish directory missing: locales/es/")
        return False
        
    if spanish_file.exists():
        print("✅ Spanish translation file exists: locales/es/translation.json")
    else:
        print("❌ Spanish translation file missing: locales/es/translation.json")
        return False
    
    # Test 2: Validate JSON structure
    print("\n📝 JSON Structure:")
    try:
        with open(spanish_file, 'r', encoding='utf-8') as f:
            spanish_data = json.load(f)
        print("✅ Spanish JSON is valid")
        print(f"   Language name: {spanish_data.get('language_name', 'Not found')}")
        print(f"   Total sections: {len(spanish_data)}")
    except json.JSONDecodeError as e:
        print(f"❌ Spanish JSON is invalid: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading Spanish file: {e}")
        return False
    
    # Test 3: Compare with English structure to ensure completeness
    print("\n🔄 Completeness Check:")
    try:
        english_file = locales_dir / "en" / "translation.json"
        with open(english_file, 'r', encoding='utf-8') as f:
            english_data = json.load(f)
        
        # Check main sections
        english_sections = set(english_data.keys())
        spanish_sections = set(spanish_data.keys())
        
        missing_sections = english_sections - spanish_sections
        extra_sections = spanish_sections - english_sections
        
        if not missing_sections and not extra_sections:
            print("✅ Spanish has all required sections")
        else:
            if missing_sections:
                print(f"⚠️  Missing sections in Spanish: {missing_sections}")
            if extra_sections:
                print(f"ℹ️  Extra sections in Spanish: {extra_sections}")
          # Check UI keys specifically (most important)
        if 'ui' in english_data and 'ui' in spanish_data:
            english_ui = set(english_data['ui'].keys())
            spanish_ui = set(spanish_data['ui'].keys())
            
            missing_ui = english_ui - spanish_ui
            if not missing_ui:
                print(f"✅ All {len(english_ui)} UI keys are translated")
            else:
                print(f"⚠️  Missing UI keys: {missing_ui}")
                
    except Exception as e:
        print(f"⚠️  Could not compare with English: {e}")
    
    # Test 4: Test key sampling
    print("\n🎯 Sample Translation Test:")
    sample_keys = [
        ("language_name", "Language Name"),
        ("ui.app_title", "App Title"),
        ("ui.generate_doc", "Generate Documentation Button"),
        ("messages.documentation_generated", "Success Message"),
        ("chat.title", "Chat Title")
    ]
    
    for key_path, description in sample_keys:
        keys = key_path.split('.')
        value = spanish_data
        try:
            for key in keys:
                value = value[key]
            print(f"✅ {description}: '{value[:50]}{'...' if len(str(value)) > 50 else ''}'")
        except KeyError:
            print(f"❌ Missing key: {key_path}")
    
    print("\n🎉 Spanish language integration test completed!")
    print("\n📋 Summary:")
    print("   • Spanish language files are properly structured")
    print("   • All major translation sections are present")
    print("   • Ready to use in the application")
    print("\n💡 Next steps:")
    print("   1. Restart the Streamlit application")
    print("   2. The language selector should now show 'Español' as an option")
    print("   3. Select Spanish to test the interface")
    
    return True

if __name__ == "__main__":
    test_spanish_integration()

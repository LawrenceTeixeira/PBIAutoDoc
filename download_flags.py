#!/usr/bin/env python3
"""
Utility script to download flag images for the language selector.
Run this script to automatically download flag images from FlagCDN.
"""

import requests
import os
from pathlib import Path

def download_flag_images():
    """Download flag images for all supported languages."""
    
    # Create flags directory if it doesn't exist
    flags_dir = Path("assets/flags")
    flags_dir.mkdir(parents=True, exist_ok=True)
    
    # Flag mapping: country code -> filename
    flags = {
        "us": "us.png",    # English
        "br": "br.png",    # Portuguese (Brazil)
        "es": "es.png"     # Spanish
    }
    
    print("🏳️ Downloading flag images...")
    
    for country_code, filename in flags.items():
        file_path = flags_dir / filename
        
        if file_path.exists():
            print(f"✅ {filename} already exists, skipping...")
            continue
            
        # Download from FlagCDN (32x24 size)
        url = f"https://flagcdn.com/32x24/{country_code}.png"
        
        try:
            print(f"📥 Downloading {filename}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            print(f"✅ Successfully downloaded {filename}")
            
        except requests.RequestException as e:
            print(f"❌ Failed to download {filename}: {e}")
            print(f"   You can manually download from: {url}")
    
    print("\n🎉 Flag image setup completed!")
    print("\n📋 Next steps:")
    print("1. Check the assets/flags/ directory for downloaded images")
    print("2. Update your app.py to use image flags:")
    print("   language_selector('main_language_selector', flag_style='image')")

if __name__ == "__main__":
    # Check if requests is available
    try:
        import requests
    except ImportError:
        print("❌ 'requests' library not found.")
        print("💡 Install it with: pip install requests")
        print("   Or download flags manually from:")
        print("   https://flagcdn.com/32x24/us.png")
        print("   https://flagcdn.com/32x24/br.png") 
        print("   https://flagcdn.com/32x24/es.png")
        exit(1)
    
    download_flag_images()

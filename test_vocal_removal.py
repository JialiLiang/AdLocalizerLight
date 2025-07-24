#!/usr/bin/env python3
"""
Test script for vocal removal functionality
Run this to verify Demucs installation and functionality
"""

import os
import sys
from pathlib import Path
import tempfile
import requests

def test_demucs_installation():
    """Test if Demucs is properly installed"""
    try:
        import demucs
        import torch
        print("✅ Demucs and PyTorch installed successfully")
        return True
    except ImportError as e:
        print(f"❌ Installation error: {e}")
        return False

def download_test_audio():
    """Download a short test audio file"""
    test_audio_url = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"  # 3-second bell sound
    temp_dir = Path(tempfile.gettempdir()) / "vocal_removal_test"
    temp_dir.mkdir(exist_ok=True)
    
    test_file = temp_dir / "test_audio.wav"
    
    if test_file.exists():
        print(f"✅ Test audio file already exists: {test_file}")
        return str(test_file)
    
    try:
        print("📥 Downloading test audio file...")
        response = requests.get(test_audio_url, timeout=10)
        if response.status_code == 200:
            with open(test_file, 'wb') as f:
                f.write(response.content)
            print(f"✅ Test audio downloaded: {test_file}")
            return str(test_file)
        else:
            print("❌ Failed to download test audio")
            return None
    except Exception as e:
        print(f"❌ Error downloading test audio: {e}")
        return None

def test_vocal_separation(audio_file):
    """Test vocal separation functionality"""
    try:
        from app import separate_vocals_demucs
        
        output_dir = Path(tempfile.gettempdir()) / "vocal_removal_test" / "output"
        output_dir.mkdir(exist_ok=True)
        
        print("🎵 Testing vocal separation...")
        result = separate_vocals_demucs(audio_file, str(output_dir))
        
        if result and os.path.exists(result):
            print(f"✅ Vocal separation successful: {result}")
            print(f"📂 File size: {os.path.getsize(result)} bytes")
            return True
        else:
            print("❌ Vocal separation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in vocal separation: {e}")
        return False

def main():
    print("🧪 Testing Vocal Removal Functionality")
    print("=" * 50)
    
    # Test 1: Installation
    if not test_demucs_installation():
        print("\n❌ Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    
    # Test 2: Download test audio
    test_audio = download_test_audio()
    if not test_audio:
        print("\n❌ Could not get test audio file")
        sys.exit(1)
    
    # Test 3: Vocal separation
    if test_vocal_separation(test_audio):
        print("\n🎉 All tests passed! Vocal removal is working correctly.")
        print("\n📋 Next steps:")
        print("1. Deploy your app to Render")
        print("2. Upload a video with vocals")
        print("3. Use the 'AI Vocal Removal' feature")
    else:
        print("\n❌ Vocal separation test failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 
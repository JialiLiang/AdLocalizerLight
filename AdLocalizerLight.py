import streamlit as st
import os
import sys
from pathlib import Path
import time
import re
import asyncio
import aiofiles
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import requests
import unicodedata
import subprocess
import shutil
from elevenlabs.client import ElevenLabs
import logging
import zipfile
import io

# Load environment variables - try local .env first, then fall back to Streamlit secrets
load_dotenv()

# Debug: Print all available secrets
st.write("Debug: Available secrets:", st.secrets)

# Get API keys from either .env or Streamlit secrets
def get_secret(key):
    """Get secret from environment variable or Streamlit secrets"""
    value = os.getenv(key)
    if value:
        st.write(f"Debug: Found {key} in environment variables")
        return value
    try:
        value = st.secrets[key]
        st.write(f"Debug: Found {key} in Streamlit secrets")
        return value
    except KeyError:
        st.error(f"""
        ⚠️ Missing API Key: {key}
        
        Please add your API key in one of these ways:
        1. Create a .env file locally with {key}=your_api_key
        2. Add it to Streamlit Cloud secrets in the format:
        ```toml
        [secrets]
        {key} = "your_api_key"
        ```
        
        Debug Info:
        - Available secrets: {list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else 'No secrets found'}
        - Environment variable value: {os.getenv(key)}
        """)
        st.stop()

# Get API keys
openai_api_key = get_secret("OPENAI_API_KEY")
elevenlabs_api_key = get_secret("ELEVENLABS_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize API clients
openai_client = OpenAI(api_key=openai_api_key)
eleven_labs_client = ElevenLabs(api_key=elevenlabs_api_key)

# Voice options
VOICES = {
    "1": {"name": "Tom Cruise", "id": "g60FwKJuhCJqbDCeuXjm"},
    "2": {"name": "Doja Cat", "id": "E1c1pVuZVvPrme6B9ryw"}
}

# Language codes and names
LANGUAGES = {
    "JP": "Japanese",
    "CN": "Traditional Chinese",
    "DE": "German",
    "IN": "Hindi",
    "FR": "French",
    "KR": "Korean",
    "BR": "Brazilian Portuguese",
    "IT": "Italian",
    "ES": "Spanish",
    "ID": "Indonesian",
    "TR": "Turkish",
    "PH": "Filipino",
    "PL": "Polish",
    "SA": "Arabic",
    "MY": "Malay",
    "VN": "Vietnamese",
    "TH": "Thai"
}

def get_enhanced_system_message(target_language, mode="faithful"):
    """Get enhanced system message for more localized translations
    
    Args:
        target_language (str): The target language for translation
        mode (str): Translation mode - 'faithful' (more literal) or 'creative' (more localized)
    """
    if mode == "faithful":
        base_message = f"""You are a professional translator and localization expert for {target_language}, specializing in video scripts and voiceovers. Follow these guidelines carefully:

1. Translate the text super naturally, as a native speaker from the target region would.
2. Adapt idioms, expressions, and cultural references to suit the local audience authentically.
3. Use appropriate tone and formality for the cultural and situational context.
4. Keep brand names, product names, and proper nouns in English.
5. Keep the translation concise and natural-sounding to avoid significantly longer delivery times than the original.
6. Return the translation as a single, continuous paragraph—no line breaks or multiple paragraphs.
7. Provide only the translated text, with no explanations, annotations, or formatting.

Important: The translation should read fluidly in {target_language}, feel culturally localized, and be reasonably aligned in pacing for video or audio use."""
    
    elif mode == "creative":
        base_message = f"""You are a creative translator and cultural expert for {target_language} who specializes in highly engaging, localized content. Your goal is to make the translation sound EXTREMELY NATIVE, as if originally created by a local for locals. Follow these guidelines:

1. Focus on capturing the core message and emotional impact rather than literal translation.
2. Use popular slang, colloquial expressions, and regional phrases that are currently trendy in {target_language}-speaking regions.
3. Transform cultural references to local equivalents that will resonate deeply with native speakers.
4. Maintain the hook/key message of the first sentence, but feel free to creatively adapt the rest.
5. Match the speaking style of a native influencer or content creator from the region.
6. Use the exact tone, rhythm, and speech patterns that are distinctly characteristic of the culture.
7. Keep brand names in English but adapt surrounding language to sound natural.
8. Return only the translated text as a single paragraph with no explanations.

Important: The translation should sound completely authentic to native speakers, as if it was originally conceived in their language and culture - NOT like a translation at all. Use expressions only locals would know and appreciate."""
    
    # Add language-specific instructions for certain languages
    language_specific = {
        "Japanese": " Use appropriate honorifics (敬語) and particles.",
        "Korean": " Use appropriate speech levels (존댓말/반말) and honorifics.",
        "Chinese": " Use appropriate measure words and consider regional variations.",
        "Arabic": " Use appropriate formality levels and consider regional dialects.",
        "Hindi": " Use appropriate formality levels and consider regional variations.",
        "Thai": " Use appropriate politeness particles and consider social context."
    }
    
    # Additional creative mode language-specific instructions
    creative_language_specific = {
        "Japanese": """ Use slang and casual expressions popular among Japanese natives. Incorporate uniquely Japanese expressions (like わかる！, マジ?, なるほど) and cultural references that would be instantly recognized by locals. Adjust the rhythm to match natural Japanese speech patterns.""",
        
        "Korean": """ Use trendy Korean expressions and internet slang popular with locals. Incorporate Korean-specific emotional expressions and reaction phrases. Consider using some Konglish (Korean-English hybrid words) where appropriate as natives would.""",
        
        "Chinese": """ Use region-specific internet slang and expressions that are trending in Chinese social media. Adapt rhythm to match natural Chinese speech patterns. Consider incorporating popular sayings, internet catchphrases (网络热词), and expressions that are uniquely Chinese.""",
        
        "Spanish": """ Use country-specific slang and expressions based on the target region (Spain vs Latin America). Incorporate local humor styles, informal contractions, and region-specific idioms that would immediately feel familiar to natives.""",
        
        "French": """ Use contemporary French expressions and slang (argot) that natives use in casual conversation. Incorporate cultural references specific to French society and adjust rhythm to match natural French cadence.""",
        
        "German": """ Use modern German colloquialisms and expressions popular in daily speech. Consider regional variations and incorporate popular German sayings and expressions that would resonate with local audiences.""",
        
        "Hindi": """ Use Hinglish (Hindi-English mix) where appropriate as it's common in everyday speech. Incorporate popular Bollywood references or trending expressions from Indian social media that would immediately connect with local audiences.""",
        
        "Arabic": """ Adapt to regional Arabic dialect expressions rather than formal MSA where appropriate. Use culturally specific greetings and expressions that vary by region, incorporating local cultural references that would resonate deeply.""",
        
        "Vietnamese": """ Use contemporary Vietnamese slang and expressions popular among natives. Incorporate trending phrases from Vietnamese social media and adjust rhythm to match natural Vietnamese speech patterns.""",
        
        "Thai": """ Use Thai-specific expressions and slang words popular in everyday conversations. Consider incorporating playful particles and ending words that Thai speakers naturally use to express emotions and attitudes."""
    }
    
    message = base_message
    
    if mode == "faithful" and target_language in language_specific:
        message += language_specific[target_language]
    elif mode == "creative" and target_language in creative_language_specific:
        message += creative_language_specific[target_language]
    
    return message

def translate_text(text, target_language, translation_mode="faithful"):
    """Translation using OpenAI (non-async)"""
    try:
        system_message = get_enhanced_system_message(target_language, translation_mode)
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error translating to {target_language}: {str(e)}")
        return None

def generate_elevenlabs_voice(text, language_code, output_directory, english_identifier, voice_id):
    """Generate voice using ElevenLabs API"""
    try:
        voice_name = next((v["name"] for v in VOICES.values() if v["id"] == voice_id), "Unknown")
        safe_name = f"{voice_name}_{language_code}_{english_identifier}"
        output_file = f"{output_directory}/{safe_name}.mp3"
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            return output_file
        else:
            st.error(f"Error from ElevenLabs API: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error generating voice: {str(e)}")
        return None

def mix_audio_with_video(audio_file, video_file, output_file, original_volume=0.8, voiceover_volume=1.3):
    """Mix audio with video using FFmpeg"""
    try:
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i", str(video_file),
            "-i", str(audio_file),
            "-filter_complex",
            f"[0:a]volume={original_volume}[a1];[1:a]volume={voiceover_volume}[a2];[a1][a2]amix=inputs=2:duration=first",
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            str(output_file)
        ]
        
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"Error mixing audio: {result.stderr}")
            return False
            
        return True
    except Exception as e:
        st.error(f"Error in audio mixing: {str(e)}")
        return False

def create_zip_file(file_paths):
    """Create a zip file containing multiple files"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
    zip_buffer.seek(0)
    return zip_buffer

def main():
    st.title("🎥 Photoroom Adlocalizer (Light)")
    st.markdown("Made with ❤️ by Jiali")
    
    # Initialize session state variables
    if 'translations' not in st.session_state:
        st.session_state.translations = {}
    if 'audio_files' not in st.session_state:
        st.session_state.audio_files = {}
    if 'mixed_videos' not in st.session_state:
        st.session_state.mixed_videos = {}
    if 'video_path' not in st.session_state:
        st.session_state.video_path = None
    if 'selected_languages' not in st.session_state:
        st.session_state.selected_languages = ["JP", "CN", "DE", "FR", "KR", "ES"]
    
    # Create necessary directories
    base_dir = Path("New clean ones 2025")
    audio_dir = base_dir / "audio"
    video_dir = base_dir / "video"
    export_dir = base_dir / "export"
    
    for directory in [audio_dir, video_dir, export_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Text input
    st.header("📝 1. Enter Text to Translate")
    text = st.text_area(
        "Enter your text here:",
        height=150,
        placeholder="Photoroom is the best app in the world.",
        help="Enter the text you want to translate. The placeholder text will disappear when you start typing."
    )
    
    # Language selection
    st.header("🌍 2. Select Languages")
    
    # Language code info
    with st.expander("ℹ️ Language Codes Reference"):
        cols = st.columns(3)
        for i, (code, name) in enumerate(LANGUAGES.items()):
            col = cols[i % 3]
            col.write(f"**{code}**: {name}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_languages = st.multiselect(
            "Choose languages to translate to:",
            options=list(LANGUAGES.keys()),
            default=st.session_state.selected_languages
        )
        st.session_state.selected_languages = selected_languages
    with col2:
        if st.button("Select All"):
            st.session_state.selected_languages = list(LANGUAGES.keys())
            st.experimental_rerun()
        if st.button("Clear All"):
            st.session_state.selected_languages = []
            st.experimental_rerun()
    
    # Translation mode
    st.header("🔄 3. Translation Mode")
    translation_mode = st.radio(
        "Select translation mode:",
        ["faithful", "creative"],
        horizontal=True,
        help="Faithful: More literal translation, keeping close to original meaning. Creative: More localized, using native expressions and cultural references."
    )
    
    # Voice selection
    st.header("🎙️ 4. Voice Settings")
    voice_options = {f"{v['name']}": v['id'] for v in VOICES.values()}
    selected_voice = st.selectbox(
        "Choose a voice:",
        options=list(voice_options.keys()),
        format_func=lambda x: x
    )
    voice_id = voice_options[selected_voice]
    
    # Translate button
    if st.button("Translate Text"):
        if not text or not st.session_state.selected_languages:
            st.warning("Please enter text and select at least one language")
        else:
            st.session_state.translations = {}
            with st.spinner("Translating..."):
                for lang_code in st.session_state.selected_languages:
                    lang_name = LANGUAGES[lang_code]
                    translation = translate_text(text, lang_name, translation_mode)
                    if translation:
                        st.session_state.translations[lang_code] = translation
                        st.success(f"Translated to {lang_name}")
    
    # Display translations
    if st.session_state.translations:
        st.header("📚 Translations")
        cols = st.columns(2)
        
        for i, (lang_code, translation) in enumerate(st.session_state.translations.items()):
            col = cols[i % 2]
            with col:
                with st.expander(f"{LANGUAGES[lang_code]} ({lang_code})"):
                    st.write(translation)
        
        # Generate voiceovers button right after translations
        if st.button("🎤 Generate Voiceovers"):
            with st.spinner("Generating voiceovers..."):
                st.session_state.audio_files = {}
                english_identifier = re.sub(r'[^a-zA-Z0-9]', '_', text[:20])
                
                for lang_code, translation in st.session_state.translations.items():
                    output_file = generate_elevenlabs_voice(
                        translation, lang_code, audio_dir, english_identifier, voice_id
                    )
                    if output_file:
                        st.session_state.audio_files[lang_code] = output_file
                        st.success(f"Generated voice for {LANGUAGES[lang_code]}")
    
    # Display audio previews
    if st.session_state.audio_files:
        st.header("🔊 Generated Voiceovers")
        cols = st.columns(2)
        
        for i, (lang_code, audio_file) in enumerate(st.session_state.audio_files.items()):
            col = cols[i % 2]
            with col:
                with st.expander(f"{LANGUAGES[lang_code]} ({lang_code})"):
                    st.audio(audio_file)
    
    # Volume settings
    st.header("🎚️ 5. Audio Settings")
    col1, col2 = st.columns(2)
    with col1:
        original_volume = st.slider("Original Audio Volume", 0.0, 2.0, 0.8, 0.1)
    with col2:
        voiceover_volume = st.slider("Voiceover Volume", 0.0, 2.0, 1.3, 0.1)
    
    # Video upload
    st.header("🎬 6. Upload Video")
    st.info("Please upload a video without voiceover (SFX version) - containing only music and sound effects.")
    video_file = st.file_uploader("Upload your SFX video file", type=["mp4", "mov"])
    
    if video_file:
        video_path = video_dir / video_file.name
        with open(video_path, "wb") as f:
            f.write(video_file.getbuffer())
        st.success(f"Video uploaded: {video_file.name}")
        st.session_state.video_path = video_path
    
    # Mix audio with video button
    if st.button("🎵 Mix Audio with Video"):
        if not st.session_state.audio_files or not st.session_state.video_path:
            st.warning("Please generate voiceovers and upload a video first")
        else:
            with st.spinner("Mixing audio with video..."):
                st.session_state.mixed_videos = {}
                
                for lang_code, audio_file in st.session_state.audio_files.items():
                    output_file = export_dir / f"{video_file.name.split('.')[0]}_{lang_code}.mp4"
                    if mix_audio_with_video(audio_file, st.session_state.video_path, output_file, original_volume, voiceover_volume):
                        st.session_state.mixed_videos[lang_code] = str(output_file)
                        st.success(f"Created video for {LANGUAGES[lang_code]}")
    
    # Display videos
    if st.session_state.mixed_videos:
        st.header("🎥 Final Videos")
        
        # Batch download button
        if st.button("📦 Download All Videos"):
            zip_buffer = create_zip_file(list(st.session_state.mixed_videos.values()))
            st.download_button(
                "📥 Download All Videos (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="localized_videos.zip",
                mime="application/zip"
            )
        
        cols = st.columns(2)
        for i, (lang_code, video_file) in enumerate(st.session_state.mixed_videos.items()):
            col = cols[i % 2]
            with col:
                with st.expander(f"{LANGUAGES[lang_code]} ({lang_code})"):
                    st.video(video_file)
                    with open(video_file, "rb") as f:
                        st.download_button(
                            f"📥 Download {LANGUAGES[lang_code]} Video",
                            data=f.read(),
                            file_name=os.path.basename(video_file),
                            mime="video/mp4"
                        )

if __name__ == "__main__":
    main() 
from flask import Flask, render_template, request, jsonify, send_file, session
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
import ffmpeg
from datetime import datetime
import tempfile
import uuid
import json
from tools_config import get_active_tools

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get API keys
def get_secret(key):
    """Get secret from environment variable"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing API Key: {key}")
    return value

try:
    openai_api_key = get_secret("OPENAI_API_KEY")
    elevenlabs_api_key = get_secret("ELEVENLABS_API_KEY")
except ValueError as e:
    print(f"Error: {e}")
    print("Please set your API keys in environment variables or .env file")
    sys.exit(1)

# Initialize API clients
openai_client = OpenAI(api_key=openai_api_key)
eleven_labs_client = ElevenLabs(api_key=elevenlabs_api_key)

# Voice options
VOICES = {
    "1": {"name": "Tom Cruise", "id": "g60FwKJuhCJqbDCeuXjm"},
    "2": {"name": "Doja Cat", "id": "E1c1pVuZVvPrme6B9ryw"},
    "3": {"name": "Chris", "id": "iP95p4xoKVk53GoZ742B"}
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
    """Get enhanced system message for more localized translations"""
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
    
    # Add language-specific instructions
    language_specific = {
        "Japanese": " Use appropriate honorifics (敬語) and particles.",
        "Korean": " Use appropriate speech levels (존댓말/반말) and honorifics.",
        "Chinese": " Use appropriate measure words and consider regional variations.",
        "Arabic": " Use appropriate formality levels and consider regional dialects.",
        "Hindi": " Use appropriate formality levels and consider regional variations.",
        "Thai": " Use appropriate politeness particles and consider social context."
    }
    
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
    """Translation using OpenAI"""
    try:
        system_message = get_enhanced_system_message(target_language, translation_mode)
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error translating to {target_language}: {str(e)}")
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
            "xi-api-key": elevenlabs_api_key
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
            logging.error(f"Error from ElevenLabs API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error generating voice: {str(e)}")
        return None

def mix_audio_with_video(audio_file, video_file, output_file, original_volume=0.8, voiceover_volume=1.3):
    """Mix audio with video using ffmpeg-python"""
    try:
        video = ffmpeg.input(str(video_file))
        audio = ffmpeg.input(str(audio_file))
        
        mixed_audio = ffmpeg.filter([
            ffmpeg.filter(video.audio, 'volume', original_volume),
            ffmpeg.filter(audio, 'volume', voiceover_volume)
        ], 'amix', inputs=2, duration='first')
        
        ffmpeg.output(
            video.video,
            mixed_audio,
            str(output_file),
            acodec='aac',
            vcodec='copy'
        ).overwrite_output().run(capture_stdout=True, capture_stderr=True)
        
        return True
    except ffmpeg.Error as e:
        logging.error(f"Error in audio mixing: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error in audio mixing: {str(e)}")
        return False

def extract_audio_from_video(video_path, output_audio_path):
    """Extract audio from video using ffmpeg"""
    try:
        (
            ffmpeg
            .input(str(video_path))
            .output(str(output_audio_path), acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        logging.error(f"Error extracting audio: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error extracting audio: {str(e)}")
        return False

def transcribe_audio(audio_file_path):
    """Transcribe audio using OpenAI Whisper"""
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="text",
                prompt="This is a marketing video or advertisement. Please transcribe accurately."
            )
        return transcription
    except Exception as e:
        logging.error(f"Error transcribing audio: {str(e)}")
        return None

def transcribe_video(video_file_path):
    """Complete transcription workflow for video file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        temp_dir = Path("temp_transcription")
        temp_dir.mkdir(exist_ok=True)
        
        temp_audio_path = temp_dir / f"temp_audio_{timestamp}.wav"
        
        if not extract_audio_from_video(video_file_path, temp_audio_path):
            return None
        
        transcription = transcribe_audio(temp_audio_path)
        
        # Clean up temporary files
        try:
            os.remove(temp_audio_path)
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception as e:
            logging.warning(f"Error cleaning up temp files: {str(e)}")
        
        return transcription
        
    except Exception as e:
        logging.error(f"Error in transcribe_video function: {str(e)}")
        return None

@app.route('/')
def index():
    tools = get_active_tools()
    return render_template('index.html', languages=LANGUAGES, voices=VOICES, tools=tools)

@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        languages = data.get('languages', [])
        translation_mode = data.get('translation_mode', 'faithful')
        
        if not text or not languages:
            return jsonify({'error': 'Text and languages are required'}), 400
        
        translations = {}
        for lang_code in languages:
            if lang_code in LANGUAGES:
                lang_name = LANGUAGES[lang_code]
                translation = translate_text(text, lang_name, translation_mode)
                if translation:
                    translations[lang_code] = translation
        
        return jsonify({'translations': translations})
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-voice', methods=['POST'])
def generate_voice():
    try:
        data = request.get_json()
        translations = data.get('translations', {})
        voice_id = data.get('voice_id')
        
        if not translations or not voice_id:
            return jsonify({'error': 'Translations and voice_id are required'}), 400
        
        # Create session-specific directories
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        base_dir = Path(f"temp_files/{session_id}")
        audio_dir = base_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_files = {}
        english_identifier = re.sub(r'[^a-zA-Z0-9]', '_', list(translations.values())[0][:20])
        
        for lang_code, translation in translations.items():
            output_file = generate_elevenlabs_voice(
                translation, lang_code, str(audio_dir), english_identifier, voice_id
            )
            if output_file:
                audio_files[lang_code] = output_file
        
        session['audio_files'] = audio_files
        return jsonify({'audio_files': audio_files})
    except Exception as e:
        logging.error(f"Voice generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Create session-specific directories
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        base_dir = Path(f"temp_files/{session_id}")
        video_dir = base_dir / "video"
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Save video file
        video_path = video_dir / video_file.filename
        video_file.save(str(video_path))
        
        session['video_path'] = str(video_path)
        return jsonify({'success': True, 'filename': video_file.filename})
    except Exception as e:
        logging.error(f"Video upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mix-audio', methods=['POST'])
def mix_audio():
    try:
        data = request.get_json()
        original_volume = data.get('original_volume', 0.8)
        voiceover_volume = data.get('voiceover_volume', 1.3)
        
        audio_files = session.get('audio_files', {})
        video_path = session.get('video_path')
        
        if not audio_files or not video_path:
            return jsonify({'error': 'Audio files and video path are required'}), 400
        
        # Create export directory
        session_id = session.get('session_id')
        base_dir = Path(f"temp_files/{session_id}")
        export_dir = base_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        mixed_videos = {}
        video_filename = Path(video_path).name
        
        for lang_code, audio_file in audio_files.items():
            output_file = export_dir / f"{video_filename.split('.')[0]}_{lang_code}.mp4"
            if mix_audio_with_video(audio_file, video_path, str(output_file), original_volume, voiceover_volume):
                mixed_videos[lang_code] = str(output_file)
        
        session['mixed_videos'] = mixed_videos
        return jsonify({'mixed_videos': mixed_videos})
    except Exception as e:
        logging.error(f"Audio mixing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Save video temporarily
        temp_dir = Path("temp_transcription")
        temp_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_video_path = temp_dir / f"temp_video_{timestamp}_{video_file.filename}"
        video_file.save(str(temp_video_path))
        
        # Transcribe
        transcription = transcribe_video(temp_video_path)
        
        # Clean up
        try:
            os.remove(temp_video_path)
        except:
            pass
        
        if transcription:
            return jsonify({'transcription': transcription})
        else:
            return jsonify({'error': 'Failed to transcribe video'}), 500
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        file_path = Path(f"temp_files/{session_id}/export/{filename}")
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(str(file_path), as_attachment=True)
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<path:filepath>')
def serve_audio(filepath):
    """Serve audio files for preview"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        # Remove any directory traversal attempts
        safe_path = Path(filepath).name
        file_path = Path(f"temp_files/{session_id}/audio/{safe_path}")
        
        if not file_path.exists():
            return jsonify({'error': 'Audio file not found'}), 404
        
        return send_file(str(file_path), mimetype='audio/mpeg')
    except Exception as e:
        logging.error(f"Audio serve error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/<path:filepath>')
def serve_video(filepath):
    """Serve video files for preview"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        # Remove any directory traversal attempts
        safe_path = Path(filepath).name
        file_path = Path(f"temp_files/{session_id}/export/{safe_path}")
        
        if not file_path.exists():
            return jsonify({'error': 'Video file not found'}), 404
        
        return send_file(str(file_path), mimetype='video/mp4')
    except Exception as e:
        logging.error(f"Video serve error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-all')
def download_all():
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        mixed_videos = session.get('mixed_videos', {})
        if not mixed_videos:
            return jsonify({'error': 'No videos to download'}), 404
        
        # Create zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for lang_code, video_path in mixed_videos.items():
                if os.path.exists(video_path):
                    zip_file.write(video_path, os.path.basename(video_path))
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='localized_videos.zip'
        )
    except Exception as e:
        logging.error(f"Download all error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    Path("temp_files").mkdir(exist_ok=True)
    Path("temp_transcription").mkdir(exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
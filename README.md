# 🎥 Photoroom Adlocalizer (Light)

A modern web application for translating and localizing video content with AI-powered voice generation. Convert your marketing videos into multiple languages with natural-sounding voiceovers.

## ✨ Features

- **AI-Powered Translation**: High-quality translations using OpenAI GPT-4
- **Voice Generation**: Natural-sounding voiceovers using ElevenLabs
- **Video Transcription**: Automatic audio transcription from uploaded videos
- **Multi-Language Support**: 17+ languages including Japanese, Korean, Spanish, French, and more
- **Translation Modes**: Faithful (literal) and Creative (localized) translation options
- **Audio Mixing**: Blend voiceovers with original video audio
- **Modern UI**: Responsive web interface with drag-and-drop file uploads
- **Batch Processing**: Generate multiple language versions simultaneously
- **Integrated Workflow**: Seamless integration with [Video Format Converter](https://photoroomvideoformatconverter.onrender.com/)

## 🚀 Quick Deploy on Render

### Option 1: Deploy from GitHub (Recommended)

1. **Fork this repository** to your GitHub account
2. **Connect to Render**:
   - Go to [Render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select your repository
3. **Configure the service**:
   - **Name**: `photoroom-adlocalizer`
   - **Environment**: `Python`
   - **Build Command**: `pip install --no-cache-dir -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Set Environment Variables**:
   - Add `OPENAI_API_KEY` with your OpenAI API key
   - Add `ELEVENLABS_API_KEY` with your ElevenLabs API key
   - Add `SECRET_KEY` with a random secret string
5. **Deploy**: Render will automatically build and deploy your app

### Option 2: Use render.yaml (Automatic)

The repository includes a `render.yaml` file that automatically configures the deployment. Simply:
1. Connect your GitHub repo to Render
2. Render will detect the `render.yaml` and configure everything automatically
3. Just add your environment variables and deploy!

## 🔧 Local Development

### Prerequisites

- Python 3.11+
- FFmpeg installed on your system
- OpenAI API key
- ElevenLabs API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd AdLocalizerNew
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

4. **Install FFmpeg**:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Open your browser** and go to `http://localhost:5000`

## 🌍 Supported Languages

| Code | Language | Code | Language |
|------|----------|------|----------|
| JP | Japanese | CN | Traditional Chinese |
| DE | German | IN | Hindi |
| FR | French | KR | Korean |
| BR | Brazilian Portuguese | IT | Italian |
| ES | Spanish | ID | Indonesian |
| TR | Turkish | PH | Filipino |
| PL | Polish | SA | Arabic |
| MY | Malay | VN | Vietnamese |
| TH | Thai | | |

## 🎙️ Available Voices

- **Tom Cruise**: Professional, authoritative voice
- **Doja Cat**: Energetic, engaging voice  
- **Chris**: Clear, professional voice

### Adding Custom Voices

You can add custom voices by:
1. **Using ElevenLabs Website**: Visit [ElevenLabs Voice Library](https://elevenlabs.io/voice-library) to browse and clone voices
2. **Voice Cloning**: Upload audio samples to create custom voices
3. **API Integration**: Use ElevenLabs API to programmatically add voices

To add a new voice, update the `VOICES` dictionary in `app.py`:
```python
VOICES = {
    "1": {"name": "Tom Cruise", "id": "g60FwKJuhCJqbDCeuXjm"},
    "2": {"name": "Doja Cat", "id": "E1c1pVuZVvPrme6B9ryw"},
    "3": {"name": "Chris", "id": "iP95p4xoKVk53GoZ742B"},
    "4": {"name": "Your Custom Voice", "id": "your_voice_id_here"}
}
```

## 📁 Project Structure

```
AdLocalizerNew/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Main web interface
├── requirements.txt      # Python dependencies
├── Procfile             # Railway deployment config
├── railway.json         # Railway-specific settings
├── runtime.txt          # Python version specification
├── .env.example         # Example environment variables
├── .gitignore           # Git ignore patterns
└── README.md           # This file
```

## 🔑 API Keys Required

### OpenAI API Key
- Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- Used for text translation and video transcription

### ElevenLabs API Key
- Get your API key from [ElevenLabs](https://elevenlabs.io/)
- Used for voice generation

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key | Yes |
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `PORT` | Port for the application (Railway sets this) | No |

### Translation Modes

- **Faithful**: Word-by-word translation - keeps original English context
- **Creative**: Localized with slang and cultural expressions

## 📱 Usage

### Complete Workflow

1. **Video Format Conversion** (Optional): Use our [Video Format Converter](https://photoroomvideoformatconverter.onrender.com/) to convert your video to the right format (square, landscape, vertical)
2. **Upload Video** (Optional): Upload a video to transcribe its audio content
3. **Enter Text**: Type or paste the text you want to translate
4. **Select Languages**: Choose target languages for translation
5. **Choose Translation Mode**: Select faithful or creative translation
6. **Translate**: Generate translations for all selected languages
7. **Select Voice**: Choose from available voice options
8. **Generate Voiceovers**: Create audio files for each translation
9. **Upload SFX Video**: Upload your video without voiceover
10. **Mix Audio**: Combine voiceovers with your video
11. **Download**: Download individual videos or all as a ZIP file

## 🔧 Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and in your system PATH
2. **API key errors**: Verify your API keys are correctly set in environment variables
3. **File upload issues**: Check file size limits and supported formats
4. **Memory issues**: Large video files may require more memory allocation

### Railway-Specific

1. **Build failures**: Check the build logs in Railway dashboard
2. **Environment variables**: Ensure all required variables are set in Railway
3. **Port issues**: Railway automatically sets the PORT environment variable

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Made with ❤️ by Jiali
- Powered by OpenAI GPT-4 for translations
- Voice generation by ElevenLabs
- Built with Flask and Bootstrap

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review Railway deployment logs
3. Open an issue on GitHub

---

**Note**: This application requires API keys for OpenAI and ElevenLabs services. Please ensure you have valid API keys and sufficient credits for these services. 
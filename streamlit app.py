import streamlit as st
import os
import sys
from pathlib import Path
import time
import re
import asyncio
import aiofiles
from openai import OpenAI, AsyncOpenAI
import requests
import unicodedata
import subprocess
import shutil
from elevenlabs.client import ElevenLabs
import logging
import zipfile
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize API clients using Streamlit secrets
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
eleven_labs_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])

# Voice options
VOICES = {
    "1": {"name": "Tom Cruise", "id": "g60FwKJuhCJqbDCeuXjm"},
    "2": {"name": "Doja Cat", "id": "E1c1pVuZVvPrme6B9ryw"}
}

# Rest of your code remains the same... 
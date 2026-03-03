#!/bin/bash

# Setup script for lightweight voice models (<100MB total)
# This script downloads and configures Whisper Tiny and Piper TTS models

echo "========================================="
echo "Q-Trace Pro Voice Assistant Setup"
echo "Installing lightweight models (<100MB)"
echo "========================================="

# Create models directory
mkdir -p /home/user/webapp/models
cd /home/user/webapp

echo ""
echo "📦 Installing Python dependencies for voice..."
pip install -q openai-whisper soundfile gtts librosa

echo ""
echo "📦 Downloading Whisper Tiny model (39MB)..."
python3 -c "
import whisper
import os
os.makedirs('/home/user/webapp/models', exist_ok=True)
print('Loading Whisper Tiny model...')
model = whisper.load_model('tiny', download_root='/home/user/webapp/models')
print('✅ Whisper Tiny model downloaded (39MB)')
"

echo ""
echo "📦 Installing Piper TTS (optional, for offline TTS)..."
# Try to install piper-tts if available
pip install -q piper-tts 2>/dev/null || echo "ℹ️  Piper TTS not available, using gTTS fallback"

echo ""
echo "📦 Downloading a lightweight Piper voice model (25MB)..."
# Download a small Piper voice model
if command -v wget &> /dev/null; then
    mkdir -p /home/user/webapp/models/piper
    cd /home/user/webapp/models/piper
    
    # Download Amy voice (low quality = smaller size ~25MB)
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx 2>/dev/null || echo "ℹ️  Could not download Piper model"
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx.json 2>/dev/null
    
    if [ -f "en_US-amy-low.onnx" ]; then
        echo "✅ Piper TTS model downloaded (25MB)"
    else
        echo "ℹ️  Piper model download skipped, will use gTTS"
    fi
fi

echo ""
echo "========================================="
echo "✅ Voice Assistant Setup Complete!"
echo "========================================="
echo ""
echo "Models installed:"
echo "  • Whisper Tiny (STT): 39MB"
echo "  • Piper/gTTS (TTS): 25MB or cloud-based"
echo "  • Total size: <100MB"
echo ""
echo "The voice assistant is now ready to use!"
echo "Access the app and click the microphone button to start."
echo ""
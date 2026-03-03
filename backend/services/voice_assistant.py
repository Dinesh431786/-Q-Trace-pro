"""
Lightweight Voice Assistant Module
Uses Whisper Tiny (39MB) for STT and Piper TTS (25-65MB) for synthesis
Total model size: ~100MB max
"""

import asyncio
import json
import base64
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

import numpy as np
import torch
import soundfile as sf
from fastapi import WebSocket
import whisper

# Optional: Use faster-whisper for better performance
try:
    from faster_whisper import WhisperModel
    USE_FASTER_WHISPER = True
except ImportError:
    USE_FASTER_WHISPER = False

logger = logging.getLogger(__name__)

class LightweightVoiceAssistant:
    """
    Lightweight voice assistant using:
    - Whisper Tiny: 39MB model for speech recognition
    - Piper TTS: 25-65MB models for voice synthesis
    """
    
    def __init__(self):
        self.whisper_model = None
        self.piper_process = None
        self.models_loaded = False
        self.model_dir = Path("/home/user/webapp/models")
        self.model_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize lightweight voice models"""
        try:
            # Load Whisper Tiny model (39MB)
            if USE_FASTER_WHISPER:
                self.whisper_model = WhisperModel(
                    "tiny",
                    device="cpu",
                    compute_type="int8",  # Use quantization for speed
                    download_root=str(self.model_dir)
                )
                logger.info("Loaded faster-whisper tiny model (39MB)")
            else:
                self.whisper_model = whisper.load_model(
                    "tiny",
                    download_root=str(self.model_dir)
                )
                logger.info("Loaded whisper tiny model (39MB)")
            
            # Initialize Piper TTS (will download on first use)
            await self._setup_piper_tts()
            
            self.models_loaded = True
            logger.info("Voice assistant initialized with <100MB models")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice models: {e}")
            self.models_loaded = False
    
    async def _setup_piper_tts(self):
        """Setup Piper TTS with a lightweight voice model"""
        try:
            # Install piper-tts if not already installed
            import subprocess
            
            # Download a lightweight Piper voice model (~25MB)
            voice_model = "en_US-amy-low"  # Low quality = smaller size
            model_path = self.model_dir / f"{voice_model}.onnx"
            
            if not model_path.exists():
                # Download the model (using wget or curl)
                model_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx"
                config_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx.json"
                
                subprocess.run([
                    "wget", "-q", "-O", str(model_path), model_url
                ], check=True)
                
                subprocess.run([
                    "wget", "-q", "-O", str(model_path) + ".json", config_url
                ], check=True)
                
                logger.info(f"Downloaded Piper voice model: {voice_model} (~25MB)")
            
            self.piper_model_path = model_path
            
        except Exception as e:
            logger.warning(f"Piper TTS setup failed, using fallback: {e}")
            self.piper_model_path = None
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text using Whisper Tiny
        
        Args:
            audio_data: Audio bytes (WAV format preferred)
            
        Returns:
            Transcribed text
        """
        if not self.models_loaded:
            await self.initialize()
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            # Transcribe using Whisper
            if USE_FASTER_WHISPER:
                segments, _ = self.whisper_model.transcribe(
                    tmp_path,
                    language="en",
                    beam_size=1,  # Faster with smaller beam
                    vad_filter=True  # Voice activity detection
                )
                text = " ".join([seg.text for seg in segments])
            else:
                result = self.whisper_model.transcribe(
                    tmp_path,
                    language="en",
                    fp16=False  # Use FP32 for CPU
                )
                text = result["text"]
            
            # Clean up
            os.unlink(tmp_path)
            
            logger.info(f"Transcribed: {text[:100]}...")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    async def synthesize_speech(self, text: str) -> bytes:
        """
        Convert text to speech using Piper TTS
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio bytes (WAV format)
        """
        try:
            if self.piper_model_path and self.piper_model_path.exists():
                # Use Piper TTS
                import subprocess
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    output_path = tmp_file.name
                
                # Run Piper TTS
                process = subprocess.Popen(
                    [
                        "echo", text, "|",
                        "piper", "--model", str(self.piper_model_path),
                        "--output_file", output_path
                    ],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                await asyncio.create_subprocess_shell(
                    f'echo "{text}" | piper --model {self.piper_model_path} --output_file {output_path}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Read the generated audio
                with open(output_path, "rb") as f:
                    audio_data = f.read()
                
                os.unlink(output_path)
                logger.info(f"Synthesized {len(text)} chars using Piper")
                return audio_data
                
            else:
                # Fallback: Use gTTS (requires internet but very lightweight)
                from gtts import gTTS
                
                tts = gTTS(text=text, lang='en', slow=False)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                
                tts.save(tmp_path)
                
                # Convert MP3 to WAV
                audio_data, _ = sf.read(tmp_path)
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                    sf.write(wav_file.name, audio_data, 22050)
                    with open(wav_file.name, "rb") as f:
                        wav_data = f.read()
                
                os.unlink(tmp_path)
                logger.info("Used gTTS fallback for speech synthesis")
                return wav_data
                
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            return b""
    
    async def process_voice_command(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process a voice command and return analysis results
        
        Args:
            audio_data: Audio input from user
            
        Returns:
            Dict with transcription, analysis results, and response audio
        """
        # Step 1: Transcribe audio to text
        command_text = await self.transcribe_audio(audio_data)
        
        if not command_text:
            error_response = "Sorry, I couldn't understand that. Please try again."
            error_audio = await self.synthesize_speech(error_response)
            return {
                "transcription": "",
                "response_text": error_response,
                "response_audio": base64.b64encode(error_audio).decode(),
                "error": True
            }
        
        # Step 2: Process the command (integrate with code analysis)
        analysis_result = await self._process_command(command_text)
        
        # Step 3: Generate spoken response
        response_text = self._generate_response(analysis_result)
        response_audio = await self.synthesize_speech(response_text)
        
        return {
            "transcription": command_text,
            "analysis": analysis_result,
            "response_text": response_text,
            "response_audio": base64.b64encode(response_audio).decode(),
            "error": False
        }
    
    async def _process_command(self, command: str) -> Dict[str, Any]:
        """Process voice command and trigger appropriate analysis"""
        command_lower = command.lower()
        
        # Parse different command types
        if "analyze" in command_lower or "check" in command_lower:
            # Trigger code analysis
            return {
                "action": "analyze_code",
                "status": "initiated",
                "command": command
            }
        elif "explain" in command_lower:
            return {
                "action": "explain_vulnerability",
                "status": "initiated",
                "command": command
            }
        elif "status" in command_lower or "progress" in command_lower:
            return {
                "action": "check_status",
                "status": "checking",
                "command": command
            }
        else:
            return {
                "action": "unknown",
                "status": "help",
                "command": command
            }
    
    def _generate_response(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a spoken response based on analysis results"""
        action = analysis_result.get("action", "unknown")
        
        if action == "analyze_code":
            return "Code analysis initiated. I'll scan for security vulnerabilities and provide a detailed report."
        elif action == "explain_vulnerability":
            return "I'll explain the vulnerability details and suggest remediation steps."
        elif action == "check_status":
            return "Checking analysis status. The scan is currently in progress."
        else:
            return ("I can help you analyze code for security issues. "
                   "Try saying 'analyze my code' or 'check for vulnerabilities'.")


class VoiceWebSocketHandler:
    """WebSocket handler for real-time voice interactions"""
    
    def __init__(self):
        self.assistant = LightweightVoiceAssistant()
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Initialize voice assistant if needed
        if not self.assistant.models_loaded:
            await self.assistant.initialize()
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Voice assistant ready (Whisper Tiny + Piper TTS)",
            "model_size": "< 100MB total"
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def handle_audio_stream(self, websocket: WebSocket, audio_chunk: bytes):
        """Handle incoming audio stream from client"""
        try:
            # Process the audio chunk
            result = await self.assistant.process_voice_command(audio_chunk)
            
            # Send results back to client
            await websocket.send_json({
                "type": "voice_response",
                **result
            })
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })


# Singleton instance
voice_assistant = LightweightVoiceAssistant()
voice_ws_handler = VoiceWebSocketHandler()
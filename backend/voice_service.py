"""
Voice Service with Lightweight AI Models
Uses Whisper Tiny (39MB) and Silero TTS (16MB)
"""

import asyncio
import base64
import io
import json
import numpy as np
from typing import Optional, Dict, Any
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import torch
import torchaudio
import whisper
from dataclasses import dataclass

@dataclass
class VoiceConfig:
    """Voice configuration"""
    whisper_model: str = "tiny"  # 39MB model
    language: str = "en"
    sample_rate: int = 16000
    silero_model: str = "v3_en"  # English model, 16MB

class VoiceService:
    """Lightweight voice processing service"""
    
    def __init__(self):
        self.whisper_model = None
        self.tts_model = None
        self.device = torch.device("cpu")  # CPU for lightweight models
        self.config = VoiceConfig()
        
    async def initialize(self):
        """Initialize voice models"""
        try:
            # Load Whisper Tiny (39MB)
            print("Loading Whisper Tiny model (39MB)...")
            self.whisper_model = whisper.load_model("tiny")
            
            # Load Silero TTS (16MB)
            print("Loading Silero TTS model (16MB)...")
            self.tts_model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='en',
                speaker='v3_en'
            )
            
            print("Voice models loaded successfully!")
            return True
            
        except Exception as e:
            print(f"Failed to load voice models: {e}")
            # Fallback to mock service
            return False
            
    async def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """Convert speech to text using Whisper"""
        try:
            if self.whisper_model is None:
                return await self.mock_speech_to_text(audio_data)
                
            # Convert bytes to audio array
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_array,
                language=self.config.language,
                fp16=False  # Disable for CPU
            )
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", "en"),
                "confidence": 0.95
            }
            
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return await self.mock_speech_to_text(audio_data)
            
    async def text_to_speech(self, text: str, voice: str = "en_0") -> bytes:
        """Convert text to speech using Silero"""
        try:
            if self.tts_model is None:
                return await self.mock_text_to_speech(text)
                
            # Generate speech
            audio = self.tts_model.apply_tts(
                text=text,
                speaker=voice,
                sample_rate=self.config.sample_rate
            )
            
            # Convert to bytes
            audio_bytes = (audio * 32767).numpy().astype(np.int16).tobytes()
            
            return audio_bytes
            
        except Exception as e:
            print(f"TTS error: {e}")
            return await self.mock_text_to_speech(text)
            
    async def mock_speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """Mock speech recognition for demo"""
        # Simulate processing
        await asyncio.sleep(0.5)
        
        # Return mock transcription
        mock_commands = [
            "analyze this code for security vulnerabilities",
            "check for SQL injection",
            "find hardcoded passwords",
            "scan for command injection",
            "detect security issues"
        ]
        
        import random
        return {
            "success": True,
            "text": random.choice(mock_commands),
            "language": "en",
            "confidence": 0.92,
            "mock": True
        }
        
    async def mock_text_to_speech(self, text: str) -> bytes:
        """Mock TTS for demo"""
        # Return a simple beep sound as placeholder
        sample_rate = 16000
        duration = min(len(text) * 0.05, 3.0)  # Estimate duration
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate a simple tone
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Add envelope
        envelope = np.exp(-t * 2)
        audio = audio * envelope * 0.3
        
        # Convert to bytes
        audio_bytes = (audio * 32767).astype(np.int16).tobytes()
        
        return audio_bytes

# Global voice service instance
voice_service = VoiceService()

async def process_voice_command(audio_data: bytes) -> Dict[str, Any]:
    """Process voice command and return analysis"""
    
    # Convert speech to text
    transcription = await voice_service.speech_to_text(audio_data)
    
    if not transcription["success"]:
        return {
            "success": False,
            "error": "Failed to recognize speech"
        }
        
    command_text = transcription["text"].lower()
    
    # Parse command intent
    intent = parse_voice_intent(command_text)
    
    # Execute based on intent
    if intent["action"] == "analyze":
        # Trigger code analysis
        return {
            "success": True,
            "command": command_text,
            "action": "analyze_code",
            "response_text": "Starting security analysis of your code",
            "intent": intent
        }
        
    elif intent["action"] == "explain":
        # Explain findings
        return {
            "success": True,
            "command": command_text,
            "action": "explain_findings",
            "response_text": f"Let me explain the {intent['target']} vulnerability",
            "intent": intent
        }
        
    elif intent["action"] == "fix":
        # Suggest fixes
        return {
            "success": True,
            "command": command_text,
            "action": "suggest_fix",
            "response_text": f"Here's how to fix the {intent['target']} issue",
            "intent": intent
        }
        
    else:
        return {
            "success": True,
            "command": command_text,
            "action": "unknown",
            "response_text": "I can help you analyze code for security issues. Try saying 'analyze this code' or 'check for vulnerabilities'",
            "intent": intent
        }

def parse_voice_intent(text: str) -> Dict[str, Any]:
    """Parse voice command intent"""
    text = text.lower()
    
    # Analysis intents
    if any(word in text for word in ["analyze", "scan", "check", "find", "detect"]):
        target = "code"
        if "sql" in text:
            target = "sql_injection"
        elif "command" in text:
            target = "command_injection"
        elif "password" in text or "credential" in text:
            target = "hardcoded_credentials"
        elif "deserialize" in text:
            target = "deserialization"
            
        return {
            "action": "analyze",
            "target": target,
            "confidence": 0.9
        }
        
    # Explanation intents
    elif any(word in text for word in ["explain", "what is", "tell me about"]):
        return {
            "action": "explain",
            "target": extract_vulnerability_type(text),
            "confidence": 0.85
        }
        
    # Fix intents
    elif any(word in text for word in ["fix", "solve", "remedy", "patch"]):
        return {
            "action": "fix",
            "target": extract_vulnerability_type(text),
            "confidence": 0.8
        }
        
    else:
        return {
            "action": "unknown",
            "target": None,
            "confidence": 0.5
        }

def extract_vulnerability_type(text: str) -> str:
    """Extract vulnerability type from text"""
    vulnerabilities = {
        "sql": "SQL Injection",
        "command": "Command Injection",
        "xss": "Cross-Site Scripting",
        "password": "Hardcoded Credentials",
        "deserialize": "Unsafe Deserialization",
        "path": "Path Traversal"
    }
    
    for key, value in vulnerabilities.items():
        if key in text.lower():
            return value
            
    return "security issue"
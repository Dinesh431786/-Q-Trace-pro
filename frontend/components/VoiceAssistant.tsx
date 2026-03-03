import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Mic,
  MicOff,
  VolumeUp,
  Settings,
  Download,
  Upload,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface VoiceAssistantProps {
  onTranscription?: (text: string) => void;
  onAnalysisRequest?: (command: string) => void;
  wsUrl?: string;
}

export const VoiceAssistant: React.FC<VoiceAssistantProps> = ({
  onTranscription,
  onAnalysisRequest,
  wsUrl = 'ws://localhost:8000/ws/voice'
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [responseText, setResponseText] = useState('');
  const [modelInfo, setModelInfo] = useState<{ stt: string; tts: string } | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Voice WebSocket connected');
        setIsConnected(true);
        setModelInfo({
          stt: 'Whisper Tiny (39MB)',
          tts: 'Piper TTS (25MB)'
        });
      };
      
      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'voice_response') {
          setTranscript(data.transcription);
          setResponseText(data.response_text);
          
          // Play response audio
          if (data.response_audio) {
            await playAudio(data.response_audio);
          }
          
          // Trigger analysis if requested
          if (data.analysis?.action === 'analyze_code') {
            onAnalysisRequest?.(data.transcription);
          }
          
          onTranscription?.(data.transcription);
          setIsProcessing(false);
        }
      };
      
      ws.onerror = (error) => {
        console.error('Voice WebSocket error:', error);
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('Voice WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current = ws;
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [wsUrl, onTranscription, onAnalysisRequest]);

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      audioContextRef.current?.close();
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioToServer(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendAudioToServer = async (audioBlob: Blob) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      setIsProcessing(false);
      return;
    }
    
    // Convert blob to array buffer and send
    const arrayBuffer = await audioBlob.arrayBuffer();
    wsRef.current.send(arrayBuffer);
  };

  const playAudio = async (base64Audio: string) => {
    try {
      const audioData = atob(base64Audio);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
      }
      
      const audioContext = audioContextRef.current;
      if (!audioContext) return;
      
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();
      
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="voice-assistant-container">
      <style>{`
        .voice-assistant-container {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 1000;
          background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
          border-radius: 20px;
          padding: 20px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.1);
          max-width: 400px;
        }
        
        .voice-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }
        
        .voice-title {
          color: #fff;
          font-size: 16px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .connection-status {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 12px;
          color: #aaa;
        }
        
        .model-info {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 10px;
          padding: 10px;
          margin-bottom: 15px;
          font-size: 12px;
          color: #888;
        }
        
        .voice-controls {
          display: flex;
          justify-content: center;
          margin-bottom: 20px;
        }
        
        .record-button {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .record-button:hover {
          transform: scale(1.05);
        }
        
        .record-button.recording {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          animation: pulse 1.5s infinite;
        }
        
        .record-button.processing {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          animation: spin 1s linear infinite;
        }
        
        @keyframes pulse {
          0% { box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4); }
          50% { box-shadow: 0 5px 25px rgba(245, 87, 108, 0.6); }
          100% { box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4); }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .transcript-area {
          background: rgba(0, 0, 0, 0.3);
          border-radius: 10px;
          padding: 15px;
          margin-bottom: 15px;
          min-height: 60px;
        }
        
        .transcript-label {
          color: #888;
          font-size: 12px;
          margin-bottom: 5px;
        }
        
        .transcript-text {
          color: #fff;
          font-size: 14px;
          line-height: 1.5;
        }
        
        .response-area {
          background: rgba(102, 126, 234, 0.1);
          border-radius: 10px;
          padding: 15px;
          min-height: 60px;
        }
        
        .response-label {
          color: #667eea;
          font-size: 12px;
          margin-bottom: 5px;
        }
        
        .response-text {
          color: #fff;
          font-size: 14px;
          line-height: 1.5;
        }
        
        .voice-hint {
          text-align: center;
          color: #888;
          font-size: 12px;
          margin-top: 10px;
        }
      `}</style>
      
      <div className="voice-header">
        <div className="voice-title">
          <VolumeUp size={20} />
          Voice Assistant
        </div>
        <div className="connection-status">
          {isConnected ? (
            <>
              <CheckCircle size={14} color="#4ade80" />
              <span style={{ color: '#4ade80' }}>Connected</span>
            </>
          ) : (
            <>
              <XCircle size={14} color="#f87171" />
              <span style={{ color: '#f87171' }}>Disconnected</span>
            </>
          )}
        </div>
      </div>
      
      {modelInfo && (
        <div className="model-info">
          <div>STT: {modelInfo.stt}</div>
          <div>TTS: {modelInfo.tts}</div>
          <div>Total: &lt;100MB Models</div>
        </div>
      )}
      
      <div className="voice-controls">
        <button
          className={`record-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
          onClick={toggleRecording}
          disabled={!isConnected || isProcessing}
        >
          {isRecording ? (
            <MicOff size={30} color="#fff" />
          ) : isProcessing ? (
            <Settings size={30} color="#fff" />
          ) : (
            <Mic size={30} color="#fff" />
          )}
        </button>
      </div>
      
      {transcript && (
        <div className="transcript-area">
          <div className="transcript-label">You said:</div>
          <div className="transcript-text">{transcript}</div>
        </div>
      )}
      
      {responseText && (
        <div className="response-area">
          <div className="response-label">Assistant:</div>
          <div className="response-text">{responseText}</div>
        </div>
      )}
      
      <div className="voice-hint">
        {isRecording ? 'Listening... Click to stop' : 
         isProcessing ? 'Processing...' : 
         'Click microphone to start voice command'}
      </div>
    </div>
  );
};
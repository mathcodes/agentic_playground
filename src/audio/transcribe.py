"""
Speech-to-Text using OpenAI Whisper.
Transcribes audio files or numpy arrays to text.
"""

import os
import sys
import numpy as np
from typing import Optional, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config

# Lazy load whisper to speed up imports
_whisper_model = None


def get_model():
    """Lazy load the Whisper model."""
    global _whisper_model
    
    if _whisper_model is None:
        import whisper
        print(f"Loading Whisper model '{config.WHISPER_MODEL}'...")
        _whisper_model = whisper.load_model(config.WHISPER_MODEL)
        print("Whisper model loaded.")
    
    return _whisper_model


def transcribe_file(audio_path: str) -> dict:
    """
    Transcribe an audio file.
    
    Args:
        audio_path: Path to audio file (wav, mp3, etc.)
        
    Returns:
        dict with keys:
            - success: bool
            - text: str (transcribed text)
            - language: str (detected language)
            - error: str (if failed)
    """
    if not os.path.exists(audio_path):
        return {
            'success': False,
            'text': None,
            'language': None,
            'error': f'File not found: {audio_path}'
        }
    
    try:
        model = get_model()
        
        # Transcribe with Whisper
        result = model.transcribe(
            audio_path,
            language='en',  # Force English for better accuracy
            fp16=False  # Use FP32 for compatibility
        )
        
        return {
            'success': True,
            'text': result['text'].strip(),
            'language': result.get('language', 'en'),
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'language': None,
            'error': f'Transcription failed: {str(e)}'
        }


def transcribe_audio(audio_data: np.ndarray, sample_rate: int = 16000) -> dict:
    """
    Transcribe audio from numpy array.
    
    Args:
        audio_data: Numpy array of audio samples (float32, mono)
        sample_rate: Sample rate of the audio (default 16000 for Whisper)
        
    Returns:
        dict with transcription results
    """
    import tempfile
    import soundfile as sf
    
    try:
        # Write to temporary file (Whisper works best with files)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        # Ensure audio is in correct format
        audio_data = audio_data.astype(np.float32)
        
        # Normalize if needed
        if audio_data.max() > 1.0 or audio_data.min() < -1.0:
            audio_data = audio_data / max(abs(audio_data.max()), abs(audio_data.min()))
        
        # Save to temp file
        sf.write(temp_path, audio_data, sample_rate)
        
        # Transcribe
        result = transcribe_file(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'language': None,
            'error': f'Audio processing failed: {str(e)}'
        }


# Optional: Simple API-based transcription as an alternative
def transcribe_with_api(audio_path: str, api_key: str = None) -> dict:
    """
    Alternative: Use OpenAI's Whisper API instead of local model.
    Requires OpenAI API key.
    
    Note: This is optional and not used by default.
    """
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        
        with open(audio_path, 'rb') as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        return {
            'success': True,
            'text': result.text,
            'language': 'en',
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'language': None,
            'error': f'API transcription failed: {str(e)}'
        }


if __name__ == "__main__":
    # Test transcription
    print("Whisper Transcription Test")
    print("=" * 50)
    
    # Test with a sample file if it exists
    test_file = "test_audio.wav"
    
    if os.path.exists(test_file):
        result = transcribe_file(test_file)
        if result['success']:
            print(f"Transcription: {result['text']}")
        else:
            print(f"Error: {result['error']}")
    else:
        print(f"No test file '{test_file}' found.")
        print("Create a test recording to verify transcription.")
        print("\nModel loading test:")
        
        # Just test model loading
        model = get_model()
        print(f"Model loaded successfully: {config.WHISPER_MODEL}")

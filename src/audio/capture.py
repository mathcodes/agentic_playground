"""
Audio Capture Module.
Handles microphone input for voice queries.
"""

import os
import sys
import numpy as np
from typing import Optional, Callable
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config


def list_audio_devices() -> list:
    """List available audio input devices."""
    import sounddevice as sd
    
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({
                'index': i,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            })
    
    return input_devices


def record_audio(
    output_path: Optional[str] = None,
    duration: float = 5.0,
    sample_rate: int = None,
    device: int = None
) -> dict:
    """
    Record audio for a fixed duration.
    
    Args:
        output_path: Path to save WAV file (optional)
        duration: Recording duration in seconds
        sample_rate: Sample rate (default from config)
        device: Audio device index (optional)
        
    Returns:
        dict with:
            - success: bool
            - audio_data: numpy array of samples
            - sample_rate: int
            - duration: float
            - path: str (if saved)
            - error: str (if failed)
    """
    import sounddevice as sd
    import soundfile as sf
    
    sample_rate = sample_rate or config.SAMPLE_RATE
    
    try:
        print(f"Recording for {duration} seconds...")
        
        # Record audio
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32',
            device=device
        )
        sd.wait()  # Wait for recording to complete
        
        # Flatten to 1D
        audio_data = audio_data.flatten()
        
        print("Recording complete.")
        
        result = {
            'success': True,
            'audio_data': audio_data,
            'sample_rate': sample_rate,
            'duration': duration,
            'path': None,
            'error': None
        }
        
        # Save to file if requested
        if output_path:
            sf.write(output_path, audio_data, sample_rate)
            result['path'] = output_path
            print(f"Saved to: {output_path}")
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'audio_data': None,
            'sample_rate': sample_rate,
            'duration': duration,
            'path': None,
            'error': f'Recording failed: {str(e)}'
        }


class VoiceActivityDetector:
    """
    Simple voice activity detection based on energy threshold.
    Records audio when voice is detected, stops on silence.
    """
    
    def __init__(
        self,
        sample_rate: int = None,
        energy_threshold: float = 0.02,
        silence_duration: float = 1.5,
        max_duration: float = 30.0,
        device: int = None
    ):
        self.sample_rate = sample_rate or config.SAMPLE_RATE
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration
        self.device = device
        
        self._recording = False
        self._audio_queue = queue.Queue()
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}")
        self._audio_queue.put(indata.copy())
    
    def record_until_silence(self) -> dict:
        """
        Record audio, automatically stopping after silence is detected.
        
        Returns dict with audio_data and metadata.
        """
        import sounddevice as sd
        
        try:
            # Start stream
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=self._audio_callback,
                device=self.device,
                blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
            )
            
            all_audio = []
            speech_started = False
            silence_samples = 0
            total_samples = 0
            max_samples = int(self.max_duration * self.sample_rate)
            silence_threshold_samples = int(self.silence_duration * self.sample_rate)
            
            print("🎤 Listening... (speak your query)")
            
            with stream:
                while True:
                    # Get audio from queue
                    try:
                        audio_chunk = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    
                    # Calculate energy
                    energy = np.sqrt(np.mean(audio_chunk ** 2))
                    
                    # Detect speech
                    is_speech = energy > self.energy_threshold
                    
                    if is_speech:
                        if not speech_started:
                            print("   Speech detected, recording...")
                            speech_started = True
                        silence_samples = 0
                        all_audio.append(audio_chunk)
                        total_samples += len(audio_chunk)
                    elif speech_started:
                        # Accumulate silence
                        silence_samples += len(audio_chunk)
                        all_audio.append(audio_chunk)
                        total_samples += len(audio_chunk)
                        
                        # Check if we've had enough silence
                        if silence_samples >= silence_threshold_samples:
                            print("   Silence detected, stopping...")
                            break
                    
                    # Check max duration
                    if total_samples >= max_samples:
                        print("   Max duration reached.")
                        break
            
            if not all_audio:
                return {
                    'success': False,
                    'audio_data': None,
                    'sample_rate': self.sample_rate,
                    'duration': 0,
                    'error': 'No speech detected'
                }
            
            # Combine all audio
            audio_data = np.concatenate(all_audio).flatten()
            duration = len(audio_data) / self.sample_rate
            
            return {
                'success': True,
                'audio_data': audio_data,
                'sample_rate': self.sample_rate,
                'duration': duration,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'audio_data': None,
                'sample_rate': self.sample_rate,
                'duration': 0,
                'error': f'Recording error: {str(e)}'
            }


def record_with_vad(
    energy_threshold: float = 0.02,
    silence_duration: float = 1.5,
    max_duration: float = 30.0
) -> dict:
    """
    Convenience function to record with voice activity detection.
    """
    vad = VoiceActivityDetector(
        energy_threshold=energy_threshold,
        silence_duration=silence_duration,
        max_duration=max_duration
    )
    return vad.record_until_silence()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Audio capture test')
    parser.add_argument('--list', action='store_true', help='List audio devices')
    parser.add_argument('--record', type=float, help='Record for N seconds')
    parser.add_argument('--vad', action='store_true', help='Record with voice activity detection')
    parser.add_argument('--output', '-o', type=str, default='test_recording.wav', help='Output file')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available input devices:")
        print("-" * 50)
        for device in list_audio_devices():
            print(f"  [{device['index']}] {device['name']}")
            print(f"      Channels: {device['channels']}, Rate: {device['sample_rate']}")
    
    elif args.record:
        result = record_audio(output_path=args.output, duration=args.record)
        if result['success']:
            print(f"Recorded {result['duration']:.1f}s to {result['path']}")
        else:
            print(f"Error: {result['error']}")
    
    elif args.vad:
        result = record_with_vad()
        if result['success']:
            print(f"Recorded {result['duration']:.1f}s of speech")
            # Save it
            import soundfile as sf
            sf.write(args.output, result['audio_data'], result['sample_rate'])
            print(f"Saved to: {args.output}")
        else:
            print(f"Error: {result['error']}")
    
    else:
        parser.print_help()

"""
Real-time Speech-to-Text using Groq API with VAD and EOD

Setup:
1. Install dependencies: pip install -r requirements.txt
2. Get your Groq API key from https://console.groq.com/keys
3. Set your API key as environment variable: export GROQ_API_KEY=your_api_key_here
4. Run the script: python record.py

The script will continuously record audio and transcribe it in real-time using Groq's fast speech-to-text API.
Includes Voice Activity Detection (VAD) and End of Discussion (EOD) detection.
Press Ctrl+C to stop recording and save the transcription to log.txt.
"""

import pyaudio
import wave
import os
import time
import numpy as np
from groq import Groq
from dotenv import load_dotenv

# Color constants
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# VAD and EOD parameters
VAD_THRESHOLD = 0.01  # Adjust based on your microphone sensitivity
SILENCE_DURATION_EOD = 2.0  # Seconds of silence to trigger EOD
CHUNK_SIZE = 1024
SAMPLE_RATE = 16000

def calculate_rms(audio_data):
    """Calculate RMS (Root Mean Square) of audio data for VAD."""
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
    return rms / 32768.0  # Normalize to 0-1 range

def is_speech(audio_data, threshold=VAD_THRESHOLD):
    """Simple VAD based on RMS energy."""
    rms = calculate_rms(audio_data)
    return rms > threshold

def transcribe_chunk(client, file_path):
    """
    Transcribe an audio chunk using Groq's speech-to-text API.
    
    Args:
        client: Groq client instance
        file_path: Path to the audio file to transcribe
        
    Returns:
        str: Transcribed text
    """
    try:
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",  # Fast and multilingual
                language="en",  # Optional: specify language for better accuracy
                temperature=0.0
            )
        return transcription.text.strip()
    except Exception as e:
        print(f"Error transcribing chunk: {e}")
        return ""
    

def record_with_vad(p, stream, file_path, max_duration=10):
    """
    Record audio with VAD, stopping when speech ends.
    
    Args:
        p: PyAudio instance
        stream: Audio stream
        file_path: Output file path
        max_duration: Maximum recording duration in seconds
    
    Returns:
        bool: True if speech was detected and recorded, False otherwise
    """
    frames = []
    speech_detected = False
    silence_start = None
    start_time = time.time()
    
    print(f"{BLUE}🎤 Listening for speech...{RESET_COLOR}")
    
    while time.time() - start_time < max_duration:
        try:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            
            if is_speech(data):
                if not speech_detected:
                    print(f"{YELLOW}🗣️  Speech detected, recording...{RESET_COLOR}")
                    speech_detected = True
                
                frames.append(data)
                silence_start = None  # Reset silence timer
            else:
                if speech_detected:
                    frames.append(data)  # Continue recording to capture end of words
                    
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > SILENCE_DURATION_EOD:
                        print(f"{RED}🔇 End of discussion detected{RESET_COLOR}")
                        break
                        
        except OSError as e:
            print(f"Audio input error: {e}")
            break
    
    if not speech_detected:
        print(f"{BLUE}⏸️  No speech detected{RESET_COLOR}")
        return False
    
    # Save the recorded audio
    wf = wave.open(file_path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"{BLUE}💾 Recorded {len(frames)} frames{RESET_COLOR}")
    return True

def main2():
    # Initialize Groq client
    client = Groq()

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)

    accumulated_transcription = ""  # Initialize an empty string to accumulate transcriptions
    
    print(f"{NEON_GREEN}🎯 Real-time Speech-to-Text with VAD/EOD started{RESET_COLOR}")
    print(f"{BLUE}📋 Press Ctrl+C to stop and save transcription{RESET_COLOR}")
    print(f"{YELLOW}⚙️  VAD Threshold: {VAD_THRESHOLD}, EOD Silence: {SILENCE_DURATION_EOD}s{RESET_COLOR}")

    try:
        while True:
            chunk_file = "temp_chunk.wav"
            
            # Record with VAD - this will wait for speech and detect when it ends
            if record_with_vad(p, stream, chunk_file):
                print(f"{BLUE}🤖 Transcribing...{RESET_COLOR}")
                transcription = transcribe_chunk(client, chunk_file)
                
                if transcription.strip():  # Only display non-empty transcriptions
                    print(f"{NEON_GREEN}📝 {transcription}{RESET_COLOR}")
                    accumulated_transcription += transcription + " "
                else:
                    print(f"{YELLOW}⚠️  No transcription result{RESET_COLOR}")
                
                # Clean up the temporary file
                try:
                    os.remove(chunk_file)
                except OSError:
                    pass
            else:
                # No speech detected, continue listening
                print(f"{BLUE}🔄 Continuing to listen...{RESET_COLOR}")
                time.sleep(0.1)  # Small delay to prevent busy waiting

    except KeyboardInterrupt:
        print(f"\n{RED}🛑 Stopping...{RESET_COLOR}")
        # Write the accumulated transcription to the log file
        with open("log.txt", "w") as log_file:
            log_file.write(accumulated_transcription)
        print(f"{NEON_GREEN}📄 Transcription saved to log.txt{RESET_COLOR}")
    finally:
        print(f"{BLUE}📊 Final transcription: {accumulated_transcription}{RESET_COLOR}")
        try:
            stream.stop_stream()
        except:
            pass
        try:
            stream.close()
        except:
            pass
        p.terminate()

if __name__ == "__main__":
    main2()
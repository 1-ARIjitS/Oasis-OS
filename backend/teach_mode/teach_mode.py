import time
import json
import os
import wave
import numpy as np
import pyaudio
from pynput import mouse, keyboard
from pathlib import Path
import threading
from collections import deque
import pyautogui
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TeachModeRecorder:
    def __init__(self, session_name):
        self.session_name = session_name
        # Always store sessions relative to this module's directory
        base_sessions_dir = Path(__file__).resolve().parent / "teach_sessions"
        base_sessions_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir = base_sessions_dir / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.mouse_events = deque(maxlen=10000)
        self.key_events = deque(maxlen=10000)
        self.voice_commands = deque(maxlen=100)
        self.frames = deque(maxlen=1000)  # Store frame metadata
        
        self.mouse_listener = None
        self.keyboard_listener = None
        self.running = False
        self.start_time = 0
        self.last_event_time = 0
        self.modifiers = set()
        
        # Frame capture settings
        self.frame_interval = 0.5  # Capture frame every 0.5 seconds
        self.last_frame_time = 0
        
        # Speech-to-text settings with better error checking
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
                self.audio_enabled = True
                print(f"🎤 Speech recording enabled with Groq API")
            except Exception as e:
                print(f"⚠️ Failed to initialize Groq client: {e}")
                self.groq_client = None
                self.audio_enabled = False
        else:
            print("⚠️ GROQ_API_KEY not found in environment variables")
            self.groq_client = None
            self.audio_enabled = False
            
        self.audio_stream = None
        self.audio_pyaudio = None
        self.speech_thread = None
        
        # VAD and speech parameters
        self.VAD_THRESHOLD = 0.01
        self.SILENCE_DURATION_EOD = 2.0
        self.CHUNK_SIZE = 1024
        self.SAMPLE_RATE = 16000
        
        if not self.audio_enabled:
            print("🚫 Speech recording disabled - check GROQ_API_KEY environment variable")
        else:
            print("✅ Speech recording ready")

    def calculate_rms(self, audio_data):
        """Calculate RMS (Root Mean Square) of audio data for VAD."""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
        return rms / 32768.0  # Normalize to 0-1 range

    def is_speech(self, audio_data, threshold=None):
        """Simple VAD based on RMS energy."""
        if threshold is None:
            threshold = self.VAD_THRESHOLD
        rms = self.calculate_rms(audio_data)
        return rms > threshold

    def record_speech_chunk(self, file_path, max_duration=10):
        """
        Record audio with VAD, stopping when speech ends.
        
        Args:
            file_path: Output file path
            max_duration: Maximum recording duration in seconds
        
        Returns:
            bool: True if speech was detected and recorded, False otherwise
        """
        if not self.audio_enabled or not self.audio_stream:
            return False
            
        frames = []
        speech_detected = False
        silence_start = None
        start_time = time.time()
        
        while time.time() - start_time < max_duration and self.running:
            try:
                data = self.audio_stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                
                if self.is_speech(data):
                    if not speech_detected:
                        speech_detected = True
                        print("🗣️ Speech detected in teach mode")
                    
                    frames.append(data)
                    silence_start = None  # Reset silence timer
                else:
                    if speech_detected:
                        frames.append(data)  # Continue recording to capture end of words
                        
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.SILENCE_DURATION_EOD:
                            break
                            
            except OSError as e:
                print(f"Audio input error: {e}")
                break
        
        if not speech_detected:
            return False
        
        # Save the recorded audio
        try:
            wf = wave.open(file_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio_pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            return True
        except Exception as e:
            print(f"Error saving audio: {e}")
            return False

    def transcribe_chunk(self, file_path):
        """
        Transcribe an audio chunk using Groq's speech-to-text API.
        
        Args:
            file_path: Path to the audio file to transcribe
            
        Returns:
            str: Transcribed text
        """
        if not self.audio_enabled:
            return ""
            
        try:
            with open(file_path, "rb") as file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=file,
                    model="whisper-large-v3-turbo",
                    language="en",
                    temperature=0.0
                )
            return transcription.text.strip()
        except Exception as e:
            print(f"Error transcribing chunk: {e}")
            return ""

    def _speech_recording_thread(self):
        """Background thread for speech recording with VAD"""
        if not self.audio_enabled or not self.audio_stream:
            print("🚫 Speech recording disabled - no audio stream")
            return
            
        print("🎙️ Speech recording thread started")
        print(f"🔧 VAD Threshold: {self.VAD_THRESHOLD}, Silence Duration: {self.SILENCE_DURATION_EOD}s")
        
        frames_buffer = []
        speech_detected = False
        silence_start = None
        
        try:
            while self.running:
                try:
                    # Check if stream is still active
                    if not self.audio_stream or not hasattr(self.audio_stream, 'read'):
                        print("⚠️ Audio stream no longer available")
                        break
                        
                    # Read audio data with timeout
                    try:
                        data = self.audio_stream.read(
                            self.CHUNK_SIZE, 
                            exception_on_overflow=False
                        )
                    except Exception as e:
                        print(f"⚠️ Audio read error: {e}")
                        break
                    
                    # Check for speech using VAD
                    is_speaking = self.is_speech(data)
                    
                    if is_speaking:
                        if not speech_detected:
                            print("🗣️ Speech detected in teach mode - starting recording")
                            speech_detected = True
                            frames_buffer = []  # Clear buffer
                        
                        frames_buffer.append(data)
                        silence_start = None
                        
                    else:
                        if speech_detected:
                            frames_buffer.append(data)
                            
                            if silence_start is None:
                                silence_start = time.time()
                                print(f"🔇 Silence started - waiting {self.SILENCE_DURATION_EOD}s for EOD")
                            elif time.time() - silence_start > self.SILENCE_DURATION_EOD:
                                # End of speech detected
                                print(f"🎯 EOD detected - processing {len(frames_buffer)} audio frames")
                                self._process_speech_chunk(frames_buffer)
                                frames_buffer = []
                                speech_detected = False
                                silence_start = None
                
                except Exception as e:
                    print(f"⚠️ Speech processing error: {e}")
                    import traceback
                    traceback.print_exc()
                    break
                    
        except Exception as e:
            print(f"⚠️ Speech thread error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Process any remaining speech
            if frames_buffer and speech_detected:
                try:
                    print(f"🎯 Processing final speech chunk with {len(frames_buffer)} frames")
                    self._process_speech_chunk(frames_buffer)
                except Exception as e:
                    print(f"⚠️ Final speech processing error: {e}")
            
            print("🎙️ Speech recording thread stopped")
    
    def _process_speech_chunk(self, frames_buffer):
        """Process recorded speech chunk with error handling"""
        if not frames_buffer:
            return
            
        try:
            # Create timestamp for unique filenames
            timestamp = int(time.time() * 1000)
            chunk_file = self.session_dir / f"temp_speech_{timestamp}.wav"
            
            # Create WAV file
            with wave.open(str(chunk_file), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(b''.join(frames_buffer))
            
            print(f"🎵 Audio chunk saved: {chunk_file.name}")
            
            # Transcribe with timeout
            transcription = self._transcribe_with_timeout(str(chunk_file))
            
            if transcription and transcription.strip():
                print(f"🎙️ Voice command: {transcription}")
                
                # Save to transcript file only
                self._save_to_transcript(transcription)
                
                # Add to voice commands for session.json
                voice_command = {
                    'time': time.time() - self.start_time,
                    'text': transcription,
                    'event_type': 'voice_command'
                }
                self.voice_commands.append(voice_command)
                print(f"✅ Voice command saved to transcript")
                
                # Immediate save to prevent loss
                self.save_session()
                
            else:
                print(f"⚠️ No transcription received or empty text")
                
            # Clean up temp file
            try:
                chunk_file.unlink()
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Speech processing error: {e}")
            import traceback
            traceback.print_exc()
            # Clean up temp file on error
            try:
                if chunk_file.exists():
                    chunk_file.unlink()
            except:
                pass

    def _save_to_transcript(self, transcription):
        """Save transcription to simple transcript file"""
        try:
            transcript_file = self.session_dir / "speech_transcript.txt"
            relative_time = time.time() - self.start_time
            
            with open(transcript_file, 'a', encoding='utf-8') as f:
                f.write(f"[{relative_time:.2f}s] {transcription}\n")
            
            print(f"📝 Added to transcript: {transcription}")
            
        except Exception as e:
            print(f"⚠️ Error saving to transcript: {e}")

    def _initialize_speech_files(self):
        """Initialize speech transcript file for a new session"""
        try:
            transcript_file = self.session_dir / "speech_transcript.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"Speech Transcript - {self.session_name}\n")
                f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 40 + "\n\n")
            
            print(f"📝 Initialized speech transcript: {transcript_file.name}")
            
        except Exception as e:
            print(f"⚠️ Error initializing speech transcript: {e}")

    def _transcribe_with_timeout(self, file_path, timeout=10):
        """Transcribe audio with timeout to prevent hanging"""
        try:
            # Create a fresh Groq client for each transcription to avoid conflicts
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            with open(file_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=file,
                    model="whisper-large-v3-turbo",
                    language="en",
                    temperature=0.0
                )
            
            return transcription.text.strip()
            
        except Exception as e:
            print(f"⚠️ Transcription error: {e}")
            return ""
        finally:
            # Explicitly cleanup client
            try:
                client = None
            except:
                pass

    def start_recording(self):
        print("🎯 Starting teach mode recording...")
        self.running = True
        self.start_time = time.time()
        self.last_event_time = self.start_time
        self.last_frame_time = self.start_time
        
        # Initialize speech transcript files
        if self.audio_enabled:
            self._initialize_speech_files()
        
        # Initialize audio stream if speech is enabled
        if self.audio_enabled:
            try:
                print("🎤 Initializing audio stream for speech recording...")
                self.audio_pyaudio = pyaudio.PyAudio()
                self.audio_stream = self.audio_pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK_SIZE
                )
                print("✅ Audio stream initialized successfully")
                
                # Quick audio level test
                print("🔊 Testing microphone levels...")
                try:
                    test_data = self.audio_stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    test_rms = self.calculate_rms(test_data)
                    print(f"📊 Current audio level: {test_rms:.4f} (VAD threshold: {self.VAD_THRESHOLD})")
                    if test_rms > 0:
                        print("✅ Microphone is receiving audio")
                    else:
                        print("⚠️ No audio detected - check microphone permissions")
                except Exception as e:
                    print(f"⚠️ Audio test failed: {e}")
                
                # Start speech recording thread
                print("🎯 Starting speech recording thread...")
                self.speech_thread = threading.Thread(target=self._speech_recording_thread, daemon=True)
                self.speech_thread.start()
                print(f"✅ Speech recording thread started (thread alive: {self.speech_thread.is_alive()})")
                
            except Exception as e:
                print(f"⚠️ Failed to initialize audio: {e}")
                import traceback
                traceback.print_exc()
                self.audio_enabled = False
                self.audio_stream = None
                self.audio_pyaudio = None
        
        # Start mouse listener
        try:
            self.mouse_listener = mouse.Listener(
                on_click=self.on_click,
                on_move=self.on_mouse_move
            )
            self.mouse_listener.start()
        except Exception as e:
            print(f"⚠️ Failed to start mouse listener: {e}")
        
        # Start keyboard listener
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
        except Exception as e:
            print(f"⚠️ Failed to start keyboard listener: {e}")
        
        # Start frame capture thread
        try:
            self.frame_thread = threading.Thread(target=self.capture_frames, daemon=True)
            self.frame_thread.start()
        except Exception as e:
            print(f"⚠️ Failed to start frame capture: {e}")
        
        print("✅ All recording components started")

    def capture_frames(self):
        """Capture screenshots at regular intervals"""
        frame_count = 0
        while self.running:
            current_time = time.time()
            if current_time - self.last_frame_time >= self.frame_interval:
                try:
                    # Capture and save frame
                    frame_path = self.session_dir / f"frame_{frame_count:05d}.png"
                    pyautogui.screenshot(str(frame_path))
                    
                    # Record frame metadata
                    self.frames.append({
                        "time": current_time - self.start_time,
                        "path": str(frame_path)
                    })
                    
                    frame_count += 1
                    self.last_frame_time = current_time
                except Exception as e:
                    print(f"⚠️ Frame capture error: {e}")
            time.sleep(0.1)

    def stop_recording(self):
        print("🛑 Stopping teach mode recording...")
        self.running = False
        
        # Stop listeners first
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener.join(timeout=2)
                self.mouse_listener = None
        except Exception as e:
            print(f"⚠️ Mouse listener cleanup error: {e}")
            
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener.join(timeout=2)
                self.keyboard_listener = None
        except Exception as e:
            print(f"⚠️ Keyboard listener cleanup error: {e}")
        
        # Stop audio stream and cleanup with proper error handling
        if self.audio_enabled and self.audio_stream:
            try:
                if hasattr(self.audio_stream, 'is_active') and self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                    time.sleep(0.1)  # Give it time to stop
                    
                if hasattr(self.audio_stream, 'close'):
                    self.audio_stream.close()
                    
                self.audio_stream = None
                print("🎤 Audio stream stopped")
            except Exception as e:
                print(f"⚠️ Audio stream cleanup error: {e}")
        
        # Cleanup PyAudio
        if self.audio_pyaudio:
            try:
                self.audio_pyaudio.terminate()
                self.audio_pyaudio = None
                print("🎤 Audio system terminated")
            except Exception as e:
                print(f"⚠️ Audio system cleanup error: {e}")
        
        # Wait for speech thread to complete
        if hasattr(self, 'speech_thread') and self.speech_thread and self.speech_thread.is_alive():
            try:
                self.speech_thread.join(timeout=3)
                if self.speech_thread.is_alive():
                    print("⚠️ Speech thread did not terminate gracefully")
            except Exception as e:
                print(f"⚠️ Speech thread cleanup error: {e}")
        
        # Force cleanup of any remaining temporary files
        try:
            temp_files = list(self.session_dir.glob("temp_speech_*.wav"))
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Temp file cleanup error: {e}")
        
        # Save session data
        try:
            self.save_session()
            print("📦 Session data saved")
            
            # Complete the speech transcript
            if self.audio_enabled:
                self._complete_speech_transcript()
                
        except Exception as e:
            print(f"⚠️ Session save error: {e}")
        
        # Final cleanup
        try:
            import gc
            gc.collect()
        except:
            pass
        
        print("✅ Teach mode recording stopped")

    def periodic_save(self):
        while self.running:
            time.sleep(3)
            self.save_session()

    def save_session(self):
        """Save current events to session.json"""
        session_data = {
            "mouse_events": list(self.mouse_events),
            "key_events": list(self.key_events),
            "voice_commands": list(self.voice_commands),
            "frames": list(self.frames),
            "start_time": self.start_time,
            "end_time": time.time(),
            "speech_enabled": self.audio_enabled,
            "speech_settings": {
                "vad_threshold": self.VAD_THRESHOLD,
                "silence_duration": self.SILENCE_DURATION_EOD,
                "sample_rate": self.SAMPLE_RATE
            } if self.audio_enabled else None
        }
        
        with open(self.session_dir / "session.json", "w") as f:
            json.dump(session_data, f, indent=2)

    def on_click(self, x, y, button, pressed):
        if pressed:  # Only record click presses, not releases
            self.mouse_events.append({
                "time": time.time() - self.start_time,
                "type": "click",
                "x": x,
                "y": y,
                "button": button.name  # Store simplified button name
            })
            self.last_event_time = time.time()

    def on_mouse_move(self, x, y):
        """Handle mouse movement events (optional recording)"""
        # Only record significant moves to avoid too much data
        current_time = time.time()
        if current_time - self.last_event_time > 0.5:  # Only record every 0.5 seconds
            self.mouse_events.append({
                "time": current_time - self.start_time,
                "type": "move",
                "x": x,
                "y": y
            })

    def on_key_press(self, key):
        try:
            current_time = time.time() - self.start_time
            
            # Handle special keys
            if hasattr(key, 'name'):
                key_name = key.name
                
                # Track modifier keys
                if key_name in ['ctrl', 'alt', 'shift', 'cmd']:
                    if key_name not in self.modifiers:
                        self.modifiers.add(key_name)
                        self.key_events.append({
                            "time": current_time,
                            "type": "modifier_press",
                            "key": key_name
                        })
                    return
            # Handle regular characters
            elif hasattr(key, 'char') and key.char:
                self.key_events.append({
                    "time": current_time,
                    "type": "type",
                    "text": key.char
                })
                return
            
            # Handle named keys
            try:
                key_name = key.name
                self.key_events.append({
                    "time": current_time,
                    "type": "keypress",
                    "key": key_name
                })
            except AttributeError:
                pass
                
        except Exception as e:
            print(f"⚠️ Key press error: {e}")

    def on_key_release(self, key):
        try:
            # Handle modifier releases
            if hasattr(key, 'name'):
                key_name = key.name
                if key_name in ['ctrl', 'alt', 'shift', 'cmd']:
                    if key_name in self.modifiers:
                        self.modifiers.remove(key_name)
                        self.key_events.append({
                            "time": time.time() - self.start_time,
                            "type": "modifier_release",
                            "key": key_name
                        })
        except Exception as e:
            print(f"⚠️ Key release error: {e}")

    def add_voice_command(self, text):
        """Add a voice command with timestamp"""
        current_time = time.time() - self.start_time
        self.voice_commands.append({
            "time": current_time,
            "text": text,
            "event_type": "voice_command"
        })
        self.last_event_time = time.time()

    def _complete_speech_transcript(self):
        """Complete the speech transcript with session summary"""
        try:
            transcript_file = self.session_dir / "speech_transcript.txt"
            if transcript_file.exists():
                with open(transcript_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n" + "-" * 40 + "\n")
                    f.write(f"Session ended: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total voice commands: {len(self.voice_commands)}\n")
                
                print(f"📝 Completed speech transcript")
                
        except Exception as e:
            print(f"⚠️ Error completing speech transcript: {e}")
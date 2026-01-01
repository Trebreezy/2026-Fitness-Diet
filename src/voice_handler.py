"""
Voice note handling for the Fitness & Diet Logger.
Processes audio files and transcribes them to text.
"""
import hashlib
import wave
import struct
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import shutil
import json

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import settings


class VoiceHandler:
    """
    Handles voice note processing for the fitness and diet logger.
    - Records audio (if hardware available)
    - Transcribes audio to text
    - Extracts metadata from audio files
    """

    SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}

    def __init__(self, voice_dir: Optional[Path] = None):
        """
        Initialize the voice handler.

        Args:
            voice_dir: Directory to store voice notes
        """
        self.voice_dir = voice_dir or settings.VOICE_DIR
        self.voice_dir.mkdir(parents=True, exist_ok=True)

        if HAS_SR:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None

    def validate_audio(self, audio_path: Path) -> Tuple[bool, str]:
        """
        Validate that the file is a supported audio format.

        Args:
            audio_path: Path to the audio file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not audio_path.exists():
            return False, f"File not found: {audio_path}"

        if audio_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {audio_path.suffix}. Supported: {self.SUPPORTED_FORMATS}"

        return True, ""

    def get_audio_metadata(self, audio_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from an audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "filename": audio_path.name,
            "size_bytes": audio_path.stat().st_size,
            "format": audio_path.suffix.lower(),
            "duration_seconds": None,
            "sample_rate": None,
            "channels": None,
        }

        # Try to get WAV metadata
        if audio_path.suffix.lower() == ".wav":
            try:
                with wave.open(str(audio_path), "rb") as wav:
                    frames = wav.getnframes()
                    rate = wav.getframerate()
                    metadata["duration_seconds"] = frames / float(rate)
                    metadata["sample_rate"] = rate
                    metadata["channels"] = wav.getnchannels()
            except Exception:
                pass

        # Try pydub for other formats
        elif HAS_PYDUB:
            try:
                audio = AudioSegment.from_file(audio_path)
                metadata["duration_seconds"] = len(audio) / 1000.0
                metadata["sample_rate"] = audio.frame_rate
                metadata["channels"] = audio.channels
            except Exception:
                pass

        return metadata

    def convert_to_wav(self, audio_path: Path) -> Path:
        """
        Convert audio file to WAV format for transcription.

        Args:
            audio_path: Path to the audio file

        Returns:
            Path to the converted WAV file
        """
        if audio_path.suffix.lower() == ".wav":
            return audio_path

        if not HAS_PYDUB:
            raise RuntimeError(
                "pydub is required to convert audio formats. Install with: pip install pydub"
            )

        # Generate output filename
        file_hash = hashlib.md5(
            f"{audio_path.name}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        output_path = self.voice_dir / f"{audio_path.stem}_{file_hash}.wav"

        try:
            audio = AudioSegment.from_file(audio_path)
            audio.export(output_path, format="wav")
            return output_path
        except Exception as e:
            raise RuntimeError(f"Failed to convert audio: {e}")

    def transcribe(
        self,
        audio_path: Path,
        language: str = "en-US",
        engine: str = "google",
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to the audio file
            language: Language code for transcription
            engine: Transcription engine ("google", "sphinx", "whisper")

        Returns:
            Dictionary with transcription results
        """
        if not HAS_SR:
            return {
                "success": False,
                "text": "",
                "error": "speech_recognition library not installed. Install with: pip install SpeechRecognition",
                "confidence": None,
            }

        # Convert to WAV if needed
        try:
            wav_path = self.convert_to_wav(audio_path)
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "confidence": None,
            }

        try:
            with sr.AudioFile(str(wav_path)) as source:
                audio_data = self.recognizer.record(source)

            if engine == "google":
                # Free Google Speech Recognition
                text = self.recognizer.recognize_google(
                    audio_data, language=language
                )
                return {
                    "success": True,
                    "text": text,
                    "error": None,
                    "confidence": None,
                    "engine": "google",
                }

            elif engine == "sphinx":
                # Offline CMU Sphinx
                text = self.recognizer.recognize_sphinx(audio_data)
                return {
                    "success": True,
                    "text": text,
                    "error": None,
                    "confidence": None,
                    "engine": "sphinx",
                }

            elif engine == "whisper":
                # OpenAI Whisper (requires whisper package)
                try:
                    text = self.recognizer.recognize_whisper(
                        audio_data, language=language.split("-")[0]
                    )
                    return {
                        "success": True,
                        "text": text,
                        "error": None,
                        "confidence": None,
                        "engine": "whisper",
                    }
                except sr.RequestError:
                    return {
                        "success": False,
                        "text": "",
                        "error": "Whisper not available. Install with: pip install openai-whisper",
                        "confidence": None,
                    }

            else:
                return {
                    "success": False,
                    "text": "",
                    "error": f"Unknown engine: {engine}",
                    "confidence": None,
                }

        except sr.UnknownValueError:
            return {
                "success": False,
                "text": "",
                "error": "Speech could not be understood",
                "confidence": None,
            }
        except sr.RequestError as e:
            return {
                "success": False,
                "text": "",
                "error": f"Transcription service error: {e}",
                "confidence": None,
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"Transcription failed: {e}",
                "confidence": None,
            }

    def process_voice_note(
        self,
        audio_path: Path,
        transcribe: bool = True,
        language: str = "en-US",
    ) -> Dict[str, Any]:
        """
        Process a voice note: validate, extract metadata, optionally transcribe.

        Args:
            audio_path: Path to the audio file
            transcribe: Whether to transcribe the audio
            language: Language for transcription

        Returns:
            Processing results including metadata and transcription
        """
        # Validate
        is_valid, error = self.validate_audio(audio_path)
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "metadata": None,
                "transcription": None,
            }

        # Extract metadata
        metadata = self.get_audio_metadata(audio_path)

        # Copy to voice directory
        file_hash = hashlib.md5(
            f"{audio_path.name}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp}_{file_hash}{audio_path.suffix}"
        saved_path = self.voice_dir / saved_filename
        shutil.copy2(audio_path, saved_path)

        result = {
            "success": True,
            "error": None,
            "metadata": metadata,
            "saved_path": str(saved_path),
            "transcription": None,
        }

        # Transcribe if requested
        if transcribe:
            result["transcription"] = self.transcribe(audio_path, language=language)

        return result

    def save_transcription(
        self,
        audio_path: Path,
        transcription: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save transcription alongside the audio file.

        Args:
            audio_path: Path to the audio file
            transcription: Transcribed text
            metadata: Optional metadata to include

        Returns:
            Path to the saved transcription file
        """
        transcript_path = audio_path.with_suffix(".json")

        data = {
            "audio_file": audio_path.name,
            "transcription": transcription,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        with open(transcript_path, "w") as f:
            json.dump(data, f, indent=2)

        return transcript_path

    def cleanup_old_files(self, max_age_days: int = 30) -> int:
        """
        Remove voice files older than the specified age.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of files removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0

        for file_path in self.voice_dir.glob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    file_path.unlink()
                    removed += 1

        return removed


class VoiceNoteRecorder:
    """
    Records voice notes from the microphone.
    Requires pyaudio to be installed.
    """

    def __init__(self, voice_dir: Optional[Path] = None):
        self.voice_dir = voice_dir or settings.VOICE_DIR
        self.voice_dir.mkdir(parents=True, exist_ok=True)

    def check_microphone(self) -> Tuple[bool, str]:
        """Check if a microphone is available."""
        if not HAS_SR:
            return False, "speech_recognition not installed"

        try:
            with sr.Microphone() as source:
                return True, "Microphone available"
        except Exception as e:
            return False, f"No microphone available: {e}"

    def record(
        self,
        duration: Optional[int] = None,
        timeout: int = 10,
        phrase_time_limit: Optional[int] = None,
    ) -> Path:
        """
        Record audio from the microphone.

        Args:
            duration: Recording duration in seconds (None for automatic)
            timeout: Maximum wait time for speech to start
            phrase_time_limit: Maximum time for a single phrase

        Returns:
            Path to the recorded audio file
        """
        if not HAS_SR:
            raise RuntimeError("speech_recognition not installed")

        recognizer = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

                if duration:
                    # Record for specific duration
                    audio_data = recognizer.record(source, duration=duration)
                else:
                    # Listen until silence
                    audio_data = recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit,
                    )

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.voice_dir / f"recording_{timestamp}.wav"

            with open(output_path, "wb") as f:
                f.write(audio_data.get_wav_data())

            return output_path

        except sr.WaitTimeoutError:
            raise RuntimeError("No speech detected within timeout")
        except Exception as e:
            raise RuntimeError(f"Recording failed: {e}")

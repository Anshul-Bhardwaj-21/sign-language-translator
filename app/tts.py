"""Text-to-Speech engine with multiple backend support."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Text-to-Speech engine with fallback support.
    
    Supports:
    - Browser Web Speech API (default, no dependencies)
    - pyttsx3 (offline, cross-platform)
    """
    
    def __init__(self, engine: str = "browser", rate: float = 1.0, volume: float = 1.0):
        self.engine_type = engine
        self.rate = rate
        self.volume = volume
        self._pyttsx3_engine: Optional[object] = None
        
        if engine == "pyttsx3":
            self._init_pyttsx3()
    
    def _init_pyttsx3(self) -> None:
        """Initialize pyttsx3 engine if available."""
        try:
            import pyttsx3
            self._pyttsx3_engine = pyttsx3.init()
            self._pyttsx3_engine.setProperty('rate', int(self.rate * 150))
            self._pyttsx3_engine.setProperty('volume', self.volume)
            logger.info("pyttsx3 TTS engine initialized")
        except Exception as exc:
            logger.warning(f"Failed to initialize pyttsx3: {exc}")
            self._pyttsx3_engine = None
    
    def speak(self, text: str) -> bool:
        """
        Speak text using configured engine.
        
        Returns:
            True if speech initiated successfully, False otherwise.
        """
        if not text or not text.strip():
            return False
        
        if self.engine_type == "pyttsx3" and self._pyttsx3_engine is not None:
            return self._speak_pyttsx3(text)
        
        # Browser engine handled by UI component
        return True
    
    def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3 engine."""
        try:
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
            return True
        except Exception as exc:
            logger.error(f"pyttsx3 speech failed: {exc}")
            return False
    
    def stop(self) -> None:
        """Stop current speech."""
        if self._pyttsx3_engine is not None:
            try:
                self._pyttsx3_engine.stop()
            except Exception:
                pass
    
    def close(self) -> None:
        """Clean up TTS resources."""
        self.stop()
        self._pyttsx3_engine = None


def create_tts_engine(engine: str = "browser", rate: float = 1.0, volume: float = 1.0) -> TTSEngine:
    """Factory function for creating TTS engine."""
    return TTSEngine(engine=engine, rate=rate, volume=volume)

"""
Text Generation Engine for ASL Recognition

Converts ASL letter predictions into words and sentences.
Implements gesture-based controls (space, del, fist confirmation).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import List, Optional

logger = logging.getLogger(__name__)

# Timing thresholds
IDLE_TIMEOUT_SECONDS = 1.5


@dataclass
class TextState:
    """Current text generation state."""
    
    current_word: str = ""
    confirmed_words: List[str] = []
    confirmed_sentences: List[str] = ""
    last_letter_time: float = 0.0
    is_idle: bool = False


class TextGenerator:
    """
    Converts ASL predictions into structured text.
    
    Rules:
    - A-Z: Append to current word
    - space: Confirm word → add to sentence
    - del: Remove last letter from current word
    - nothing: Ignore
    - Fist gesture: Confirm sentence → trigger TTS
    - 1.5s idle: Auto-confirm sentence
    """
    
    def __init__(self, idle_timeout: float = IDLE_TIMEOUT_SECONDS):
        self.idle_timeout = idle_timeout
        self._state = TextState()
        self._lock = Lock()
        
        # Track last confirmed sentence to avoid duplicates
        self._last_confirmed_sentence = ""
    
    def add_letter(self, letter: str) -> TextState:
        """
        Process ASL letter prediction.
        
        Args:
            letter: Predicted letter (A-Z, space, del, nothing)
        
        Returns:
            Updated TextState
        """
        with self._lock:
            current_time = time.time()
            
            # Handle special gestures
            if letter == "space":
                self._confirm_word()
            
            elif letter == "del":
                self._delete_last_letter()
            
            elif letter == "nothing":
                # Check for idle timeout
                if self._state.current_word or self._state.confirmed_words:
                    time_since_last = current_time - self._state.last_letter_time
                    if time_since_last >= self.idle_timeout:
                        self._state.is_idle = True
            
            elif letter.isalpha() and len(letter) == 1:
                # Add letter to current word
                self._state.current_word += letter
                self._state.last_letter_time = current_time
                self._state.is_idle = False
            
            return self._get_state_copy()
    
    def confirm_sentence_by_fist(self) -> Optional[str]:
        """
        Confirm sentence via fist gesture.
        
        Returns:
            Confirmed sentence text, or None if nothing to confirm
        """
        with self._lock:
            return self._confirm_sentence()
    
    def confirm_sentence_by_idle(self) -> Optional[str]:
        """
        Confirm sentence via idle timeout.
        
        Returns:
            Confirmed sentence text, or None if not idle or nothing to confirm
        """
        with self._lock:
            if not self._state.is_idle:
                return None
            
            return self._confirm_sentence()
    
    def _confirm_word(self) -> None:
        """Move current word to confirmed words."""
        if self._state.current_word:
            self._state.confirmed_words.append(self._state.current_word)
            self._state.current_word = ""
            self._state.last_letter_time = time.time()
            logger.debug(f"Word confirmed: {self._state.confirmed_words[-1]}")
    
    def _delete_last_letter(self) -> None:
        """Remove last letter from current word."""
        if self._state.current_word:
            self._state.current_word = self._state.current_word[:-1]
            self._state.last_letter_time = time.time()
            logger.debug(f"Letter deleted. Current word: {self._state.current_word}")
    
    def _confirm_sentence(self) -> Optional[str]:
        """
        Confirm current sentence and reset state.
        
        Returns:
            Confirmed sentence text, or None if nothing to confirm
        """
        # Confirm any pending word first
        if self._state.current_word:
            self._confirm_word()
        
        # Build sentence from confirmed words
        if not self._state.confirmed_words:
            return None
        
        sentence = " ".join(self._state.confirmed_words)
        
        # Avoid duplicate confirmations
        if sentence == self._last_confirmed_sentence:
            return None
        
        self._last_confirmed_sentence = sentence
        
        # Add to confirmed sentences
        self._state.confirmed_sentences = sentence
        
        # Reset state
        self._state.confirmed_words = []
        self._state.current_word = ""
        self._state.is_idle = False
        
        logger.info(f"Sentence confirmed: {sentence}")
        return sentence
    
    def get_live_caption(self) -> str:
        """
        Get current live caption (current word being formed).
        
        Returns:
            Current word in progress
        """
        with self._lock:
            return self._state.current_word
    
    def get_confirmed_words(self) -> List[str]:
        """
        Get list of confirmed words in current sentence.
        
        Returns:
            List of confirmed words
        """
        with self._lock:
            return self._state.confirmed_words.copy()
    
    def get_confirmed_sentences(self) -> str:
        """
        Get last confirmed sentence.
        
        Returns:
            Last confirmed sentence text
        """
        with self._lock:
            return self._state.confirmed_sentences
    
    def reset(self) -> None:
        """Reset all text generation state."""
        with self._lock:
            self._state = TextState()
            self._last_confirmed_sentence = ""
            logger.info("Text generator reset")
    
    def _get_state_copy(self) -> TextState:
        """Get thread-safe copy of current state."""
        return TextState(
            current_word=self._state.current_word,
            confirmed_words=self._state.confirmed_words.copy(),
            confirmed_sentences=self._state.confirmed_sentences,
            last_letter_time=self._state.last_letter_time,
            is_idle=self._state.is_idle
        )


def create_text_generator(idle_timeout: float = IDLE_TIMEOUT_SECONDS) -> TextGenerator:
    """Factory function for creating text generator."""
    return TextGenerator(idle_timeout=idle_timeout)

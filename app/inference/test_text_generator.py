"""
Unit tests for Text Generator module.
"""

import pytest
import time
from app.inference.text_generator import (
    TextGenerator,
    create_text_generator,
    IDLE_TIMEOUT_SECONDS
)


class TestTextGenerator:
    """Test suite for Text Generator."""
    
    def test_create_text_generator(self):
        """Test text generator creation."""
        generator = create_text_generator()
        assert generator is not None
        assert generator.idle_timeout == IDLE_TIMEOUT_SECONDS
    
    def test_add_letter(self):
        """Test adding letters to current word."""
        generator = create_text_generator()
        
        # Add letters
        generator.add_letter('H')
        generator.add_letter('E')
        generator.add_letter('L')
        generator.add_letter('L')
        generator.add_letter('O')
        
        # Check current word
        assert generator.get_live_caption() == 'HELLO'
    
    def test_space_confirms_word(self):
        """Test that space gesture confirms word."""
        generator = create_text_generator()
        
        # Add letters
        generator.add_letter('H')
        generator.add_letter('I')
        
        # Add space
        generator.add_letter('space')
        
        # Current word should be empty
        assert generator.get_live_caption() == ''
        
        # Word should be confirmed
        assert generator.get_confirmed_words() == ['HI']
    
    def test_del_removes_letter(self):
        """Test that del gesture removes last letter."""
        generator = create_text_generator()
        
        # Add letters
        generator.add_letter('H')
        generator.add_letter('E')
        generator.add_letter('L')
        generator.add_letter('L')
        generator.add_letter('O')
        
        # Delete last letter
        generator.add_letter('del')
        
        # Check current word
        assert generator.get_live_caption() == 'HELL'
    
    def test_del_on_empty_word(self):
        """Test del on empty word does nothing."""
        generator = create_text_generator()
        
        # Delete on empty word
        generator.add_letter('del')
        
        # Should still be empty
        assert generator.get_live_caption() == ''
    
    def test_nothing_ignored(self):
        """Test that 'nothing' predictions are ignored."""
        generator = create_text_generator()
        
        # Add letter
        generator.add_letter('A')
        
        # Add nothing
        generator.add_letter('nothing')
        
        # Word should still be 'A'
        assert generator.get_live_caption() == 'A'
    
    def test_confirm_sentence_by_fist(self):
        """Test sentence confirmation via fist gesture."""
        generator = create_text_generator()
        
        # Build sentence
        generator.add_letter('H')
        generator.add_letter('I')
        generator.add_letter('space')
        generator.add_letter('T')
        generator.add_letter('H')
        generator.add_letter('E')
        generator.add_letter('R')
        generator.add_letter('E')
        
        # Confirm sentence
        sentence = generator.confirm_sentence_by_fist()
        
        # Check sentence
        assert sentence == 'HI THERE'
        
        # State should be reset
        assert generator.get_live_caption() == ''
        assert generator.get_confirmed_words() == []
    
    def test_confirm_sentence_includes_current_word(self):
        """Test that sentence confirmation includes current word."""
        generator = create_text_generator()
        
        # Build sentence without final space
        generator.add_letter('H')
        generator.add_letter('I')
        
        # Confirm sentence
        sentence = generator.confirm_sentence_by_fist()
        
        # Should include current word
        assert sentence == 'HI'
    
    def test_confirm_empty_sentence(self):
        """Test confirming empty sentence returns None."""
        generator = create_text_generator()
        
        # Confirm without any words
        sentence = generator.confirm_sentence_by_fist()
        
        # Should return None
        assert sentence is None
    
    def test_duplicate_sentence_prevention(self):
        """Test that duplicate sentences are not confirmed."""
        generator = create_text_generator()
        
        # Build and confirm sentence
        generator.add_letter('H')
        generator.add_letter('I')
        sentence1 = generator.confirm_sentence_by_fist()
        assert sentence1 == 'HI'
        
        # Try to confirm again immediately
        sentence2 = generator.confirm_sentence_by_fist()
        assert sentence2 is None
    
    def test_idle_timeout(self):
        """Test idle timeout sentence confirmation."""
        generator = create_text_generator(idle_timeout=0.1)  # 100ms timeout
        
        # Add letters
        generator.add_letter('H')
        generator.add_letter('I')
        
        # Wait for idle timeout
        time.sleep(0.15)
        
        # Add nothing to trigger idle check
        state = generator.add_letter('nothing')
        
        # Should be marked as idle
        assert state.is_idle
        
        # Confirm by idle
        sentence = generator.confirm_sentence_by_idle()
        assert sentence == 'HI'
    
    def test_idle_not_triggered_without_timeout(self):
        """Test that idle is not triggered before timeout."""
        generator = create_text_generator(idle_timeout=10.0)  # 10s timeout
        
        # Add letters
        generator.add_letter('H')
        generator.add_letter('I')
        
        # Add nothing immediately
        state = generator.add_letter('nothing')
        
        # Should not be idle yet
        assert not state.is_idle
        
        # Confirm by idle should return None
        sentence = generator.confirm_sentence_by_idle()
        assert sentence is None
    
    def test_reset(self):
        """Test generator reset."""
        generator = create_text_generator()
        
        # Build some state
        generator.add_letter('H')
        generator.add_letter('I')
        generator.add_letter('space')
        generator.add_letter('T')
        generator.add_letter('H')
        generator.add_letter('E')
        generator.add_letter('R')
        generator.add_letter('E')
        
        # Reset
        generator.reset()
        
        # All state should be cleared
        assert generator.get_live_caption() == ''
        assert generator.get_confirmed_words() == []
        assert generator.get_confirmed_sentences() == ''
    
    def test_thread_safety(self):
        """Test thread-safe operations."""
        import threading
        
        generator = create_text_generator()
        errors = []
        
        def add_letters():
            try:
                for _ in range(100):
                    generator.add_letter('A')
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads
        threads = [threading.Thread(target=add_letters) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not have any errors
        assert len(errors) == 0
    
    def test_multiple_words_in_sentence(self):
        """Test building sentence with multiple words."""
        generator = create_text_generator()
        
        # Build multi-word sentence
        generator.add_letter('H')
        generator.add_letter('E')
        generator.add_letter('L')
        generator.add_letter('L')
        generator.add_letter('O')
        generator.add_letter('space')
        
        generator.add_letter('W')
        generator.add_letter('O')
        generator.add_letter('R')
        generator.add_letter('L')
        generator.add_letter('D')
        
        # Confirm
        sentence = generator.confirm_sentence_by_fist()
        
        # Check sentence
        assert sentence == 'HELLO WORLD'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

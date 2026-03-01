"""
Mock Inference Engine for Demo/Development
No external AI API calls - deterministic predictions for offline demo
"""

import random
import time
from typing import Dict, List, Optional, Tuple
from dataclimport dataclass


@dataclass
class MockPrediction:
    """Mock prediction result"""
    letter: str
    confidence: float
    is_stable: bool


class MockASLModel:
    """
    Mock ASL classifier that returns deterministic predictions
    based on hand position heuristics (no external API calls)
    """
    
    # ASL alphabet for demo
    ASL_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    COMMON_WORDS = ["HELLO", "YES", "NO", "PLEASE", "THANK", "YOU", "HELP", "SORRY"]
    
    def __init__(self, mode: str = "deterministic"):
        """
        Initialize mock model
        
        Args:
            mode: "deterministic" (same input -> same output) or "random" (varied)
        """
        self.mode = mode
        self.last_prediction = "NOTHING"
        self.prediction_count = 0
        self.confidence_threshold = 0.60
        
    def predict(self, landmarks: Optional[List[Tuple[float, float, float]]] = None) -> MockPrediction:
        """
        Generate mock prediction based on hand landmarks
        
        Args:
            landmarks: Hand landmarks (21 points, each with x, y, z)
            
        Returns:
            MockPrediction with letter, confidence, and stability
        """
        if landmarks is None or len(landmarks) < 21:
            return MockPrediction(
                letter="NOTHING",
                confidence=0.0,
                is_stable=False
            )
        
        # Simple heuristic: use hand position to determine letter
        # This is deterministic and doesn't require external AI
        
        # Calculate hand "openness" (distance between thumb and index finger)
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        wrist = landmarks[0]
        
        # Euclidean distance
        thumb_index_dist = self._distance(thumb_tip, index_tip)
        hand_height = wrist[1] - index_tip[1]  # Y-axis (inverted in image coords)
        
        # Map to letters based on simple rules
        letter, base_confidence = self._heuristic_classify(
            thumb_index_dist, 
            hand_height,
            landmarks
        )
        
        # Add some variance in deterministic mode
        if self.mode == "deterministic":
            # Same input -> same output (with small noise)
            confidence = min(0.95, base_confidence + 0.05 * random.random())
        else:
            # Random mode for testing
            confidence = random.uniform(0.50, 0.95)
            if random.random() < 0.3:  # 30% chance of different letter
                letter = random.choice(self.ASL_LETTERS)
        
        # Stability check: same letter for 3+ frames
        is_stable = (letter == self.last_prediction and self.prediction_count >= 2)
        
        if letter == self.last_prediction:
            self.prediction_count += 1
        else:
            self.prediction_count = 0
            self.last_prediction = letter
        
        return MockPrediction(
            letter=letter,
            confidence=confidence,
            is_stable=is_stable and confidence > self.confidence_threshold
        )
    
    def _distance(self, p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
        """Calculate Euclidean distance between two 3D points"""
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)**0.5
    
    def _heuristic_classify(
        self, 
        thumb_index_dist: float, 
        hand_height: float,
        landmarks: List[Tuple[float, float, float]]
    ) -> Tuple[str, float]:
        """
        Simple heuristic classification based on hand geometry
        
        Returns:
            (letter, confidence)
        """
        # Count extended fingers
        extended_fingers = self._count_extended_fingers(landmarks)
        
        # Simple rules (not accurate ASL, just for demo)
        if extended_fingers == 0:
            # Fist
            return "S", 0.85
        elif extended_fingers == 1:
            # One finger
            return "A", 0.80
        elif extended_fingers == 2:
            if thumb_index_dist > 0.15:
                return "V", 0.82
            else:
                return "U", 0.78
        elif extended_fingers == 3:
            return "W", 0.80
        elif extended_fingers == 4:
            return "B", 0.75
        elif extended_fingers == 5:
            # Open hand
            if hand_height > 0.3:
                return "HELLO", 0.88
            else:
                return "FIVE", 0.85
        else:
            # Default
            return random.choice(["H", "E", "L", "O"]), 0.70
    
    def _count_extended_fingers(self, landmarks: List[Tuple[float, float, float]]) -> int:
        """Count how many fingers are extended"""
        # Finger tip indices: thumb=4, index=8, middle=12, ring=16, pinky=20
        # Finger base indices: thumb=2, index=6, middle=10, ring=14, pinky=18
        
        finger_tips = [4, 8, 12, 16, 20]
        finger_bases = [2, 6, 10, 14, 18]
        
        extended = 0
        for tip_idx, base_idx in zip(finger_tips, finger_bases):
            tip = landmarks[tip_idx]
            base = landmarks[base_idx]
            
            # Simple check: tip is above base (lower Y value in image coords)
            if tip[1] < base[1] - 0.05:  # threshold
                extended += 1
        
        return extended
    
    def is_ready(self) -> bool:
        """Check if model is ready (always true for mock)"""
        return True
    
    def reset(self):
        """Reset prediction state"""
        self.last_prediction = "NOTHING"
        self.prediction_count = 0


class MockTextGenerator:
    """
    Mock text generator that builds words/sentences from letters
    """
    
    def __init__(self):
        self.current_word = ""
        self.confirmed_words = []
        self.last_letter = ""
        self.letter_count = 0
        self.idle_frames = 0
        self.idle_threshold = 30  # ~3 seconds at 10 FPS
        
    def add_letter(self, letter: str) -> Dict[str, any]:
        """
        Add a letter to current word
        
        Returns:
            {
                "current_word": str,
                "confirmed_words": List[str],
                "sentence": str
            }
        """
        if letter == "NOTHING" or letter == self.last_letter:
            self.idle_frames += 1
        else:
            self.idle_frames = 0
            
            # Add letter to current word
            if letter in ["SPACE", "HELLO"]:  # Special commands
                if self.current_word:
                    self.confirmed_words.append(self.current_word)
                    self.current_word = ""
            else:
                self.current_word += letter
                
            self.last_letter = letter
        
        return {
            "current_word": self.current_word,
            "confirmed_words": self.confirmed_words.copy(),
            "sentence": " ".join(self.confirmed_words + ([self.current_word] if self.current_word else []))
        }
    
    def confirm_word(self) -> Optional[str]:
        """Confirm current word and start new one"""
        if self.current_word:
            self.confirmed_words.append(self.current_word)
            word = self.current_word
            self.current_word = ""
            return word
        return None
    
    def confirm_sentence(self) -> Optional[str]:
        """Confirm entire sentence"""
        if self.confirmed_words or self.current_word:
            sentence = " ".join(self.confirmed_words + ([self.current_word] if self.current_word else []))
            self.confirmed_words = []
            self.current_word = ""
            return sentence
        return None
    
    def reset(self):
        """Reset all state"""
        self.current_word = ""
        self.confirmed_words = []
        self.last_letter = ""
        self.letter_count = 0
        self.idle_frames = 0


def create_mock_model(mode: str = "deterministic") -> MockASLModel:
    """Factory function to create mock model"""
    return MockASLModel(mode=mode)


def create_mock_text_generator() -> MockTextGenerator:
    """Factory function to create mock text generator"""
    return MockTextGenerator()


if __name__ == "__main__":
    # Test the mock model
    model = create_mock_model()
    text_gen = create_mock_text_generator()
    
    print("Mock ASL Model Test")
    print("=" * 50)
    
    # Simulate some hand landmarks (dummy data)
    dummy_landmarks = [(i * 0.05, i * 0.05, 0.0) for i in range(21)]
    
    for i in range(10):
        prediction = model.predict(dummy_landmarks)
        result = text_gen.add_letter(prediction.letter if prediction.is_stable else "NOTHING")
        
        print(f"Frame {i+1}:")
        print(f"  Letter: {prediction.letter}")
        print(f"  Confidence: {prediction.confidence:.2f}")
        print(f"  Stable: {prediction.is_stable}")
        print(f"  Current word: {result['current_word']}")
        print(f"  Sentence: {result['sentence']}")
        print()
        
        time.sleep(0.1)
    
    print("Test complete!")

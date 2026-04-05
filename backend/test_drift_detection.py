#!/usr/bin/env python3
"""
Unit Tests for Drift Detection Service

Tests the drift detection functionality including:
- Confidence score logging
- Manual accuracy sampling
- Weekly metrics calculation
- Ground truth labeling

Requirements:
- 52.3: Sample and label production data for accuracy evaluation (100 samples/week)
- 52.4: Alert when F1 score drops below threshold (default 80%)

Author: AI-Powered Meeting Platform Team
"""

import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, call

# Add parent directory to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from drift_detection import DriftDetectionService


class TestDriftDetectionService(unittest.TestCase):
    """Test cases for DriftDetectionService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = DriftDetectionService()
        self.test_user_id = str(uuid.uuid4())
        self.test_meeting_id = str(uuid.uuid4())
        self.test_model_version_id = str(uuid.uuid4())
    
    @patch('drift_detection.psycopg2.connect')
    def test_log_prediction(self, mock_connect):
        """
        Test logging a prediction to the database.
        
        Validates: Requirement 52.3 (log predictions for accuracy evaluation)
        """
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [self.test_user_id]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        # Log a prediction
        prediction_id = self.service.log_prediction(
            model_version_id=self.test_model_version_id,
            user_id=self.test_user_id,
            meeting_id=self.test_meeting_id,
            predicted_gesture='hello',
            confidence=0.95,
            latency_ms=150.5
        )
        
        # Verify prediction was logged
        self.assertIsNotNone(prediction_id)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('drift_detection.psycopg2.connect')
    def test_log_prediction_with_ground_truth(self, mock_connect):
        """
        Test logging a prediction with ground truth label.
        
        Validates: Requirement 52.3 (log predictions with ground truth)
        """
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [self.test_user_id]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        # Log a prediction with ground truth
        prediction_id = self.service.log_prediction(
            model_version_id=self.test_model_version_id,
            user_id=self.test_user_id,
            meeting_id=self.test_meeting_id,
            predicted_gesture='hello',
            confidence=0.95,
            latency_ms=150.5,
            ground_truth_gesture='hello'
        )
        
        # Verify correctness was calculated
        self.assertIsNotNone(prediction_id)
        # Check that is_correct was set to True (hello == hello)
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('is_correct', call_args[0])
    
    @patch('drift_detection.psycopg2.connect')
    def test_sample_predictions_for_evaluation(self, mock_connect):
        """
        Test sampling predictions for manual evaluation.
        
        Validates: Requirement 52.3 (sample 100 predictions per week)
        """
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock sample data
        sample_data = [
            {
                'id': str(uuid.uuid4()),
                'predicted_gesture': f'gesture_{i}',
                'confidence': 0.8,
                'timestamp': datetime.now(),
                'model_version_id': self.test_model_version_id,
                'user_id': self.test_user_id,
                'meeting_id': self.test_meeting_id,
                'latency_ms': 100
            }
            for i in range(100)
        ]
        
        mock_cursor.fetchall.return_value = sample_data
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        # Sample 100 predictions
        samples = self.service.sample_predictions_for_evaluation(count=100, days_back=7)
        
        # Verify sample count
        self.assertEqual(len(samples), 100)
        
        # Verify database was queried
        self.assertEqual(mock_cursor.execute.call_count, 2)  # SELECT + UPDATE
        mock_conn.commit.assert_called_once()
    
    @patch('drift_detection.psycopg2.connect')
    def test_update_ground_truth(self, mock_connect):
        """Test updating a prediction with ground truth label."""
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        prediction_id = str(uuid.uuid4())
        
        # Update with ground truth
        self.service.update_ground_truth(prediction_id, 'hello')
        
        # Verify database was updated
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('drift_detection.psycopg2.connect')
    def test_calculate_weekly_metrics_no_data(self, mock_connect):
        """Test metrics calculation with no labeled data."""
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'total_samples': 0,
            'correct_predictions': 0,
            'avg_confidence': None,
            'stddev_confidence': None,
            'p50_confidence': None,
            'p90_confidence': None,
            'p95_confidence': None,
            'p99_confidence': None,
            'avg_latency_ms': None,
            'p95_latency_ms': None
        }
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        metrics = self.service.calculate_weekly_metrics(days_back=7)
        
        self.assertEqual(metrics['total_samples'], 0)
        self.assertEqual(metrics['accuracy'], 0.0)
    
    @patch('drift_detection.psycopg2.connect')
    def test_calculate_weekly_metrics_with_data(self, mock_connect):
        """
        Test weekly metrics calculation with labeled data.
        
        Validates: Requirement 52.4 (calculate accuracy metrics)
        """
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock metrics data (85% accuracy)
        mock_cursor.fetchone.return_value = {
            'total_samples': 100,
            'correct_predictions': 85,
            'avg_confidence': 0.85,
            'stddev_confidence': 0.1,
            'p50_confidence': 0.85,
            'p90_confidence': 0.95,
            'p95_confidence': 0.97,
            'p99_confidence': 0.99,
            'avg_latency_ms': 150.0,
            'p95_latency_ms': 180.0
        }
        
        # Mock per-class metrics
        mock_cursor.fetchall.return_value = [
            {'ground_truth_gesture': 'hello', 'total': 50, 'correct': 45, 'avg_confidence': 0.85},
            {'ground_truth_gesture': 'goodbye', 'total': 50, 'correct': 40, 'avg_confidence': 0.80}
        ]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        # Calculate metrics
        metrics = self.service.calculate_weekly_metrics(days_back=7)
        
        # Verify metrics
        self.assertEqual(metrics['total_samples'], 100)
        self.assertEqual(metrics['correct_predictions'], 85)
        self.assertAlmostEqual(metrics['accuracy'], 0.85, places=2)
        self.assertAlmostEqual(metrics['error_rate'], 0.15, places=2)
        
        # Verify confidence statistics
        self.assertGreater(metrics['avg_confidence'], 0.0)
        self.assertGreater(metrics['p50_confidence'], 0.0)
        self.assertGreater(metrics['p95_confidence'], 0.0)
        
        # Verify latency statistics
        self.assertGreater(metrics['avg_latency_ms'], 0.0)
        self.assertGreater(metrics['p95_latency_ms'], 0.0)
        
        # Verify per-class metrics
        self.assertEqual(len(metrics['per_class_metrics']), 2)
    
    @patch('drift_detection.psycopg2.connect')
    def test_calculate_weekly_metrics_below_threshold(self, mock_connect):
        """
        Test alert when accuracy drops below threshold.
        
        Validates: Requirement 52.4 (alert when F1 score drops below 80%)
        """
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock metrics data (75% accuracy - below threshold)
        mock_cursor.fetchone.return_value = {
            'total_samples': 100,
            'correct_predictions': 75,
            'avg_confidence': 0.80,
            'stddev_confidence': 0.1,
            'p50_confidence': 0.80,
            'p90_confidence': 0.90,
            'p95_confidence': 0.95,
            'p99_confidence': 0.99,
            'avg_latency_ms': 150.0,
            'p95_latency_ms': 180.0
        }
        
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        # Calculate metrics
        metrics = self.service.calculate_weekly_metrics(days_back=7)
        
        # Verify alert is present
        self.assertIn('alert', metrics)
        self.assertIn('below threshold', metrics['alert'])
        self.assertAlmostEqual(metrics['accuracy'], 0.75, places=2)
    
    @patch('drift_detection.psycopg2.connect')
    def test_get_confidence_distribution(self, mock_connect):
        """
        Test confidence distribution monitoring.
        
        Validates: Requirement 52.1 (monitor confidence score distribution)
        """
        # Setup mock
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock distribution data
        mock_cursor.fetchone.return_value = {
            'total_predictions': 70,
            'mean': 0.85,
            'stddev': 0.1,
            'min': 0.7,
            'max': 0.99,
            'p50': 0.85,
            'p90': 0.95,
            'p95': 0.97,
            'p99': 0.99
        }
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        self.service.conn = mock_conn
        
        # Get confidence distribution
        dist = self.service.get_confidence_distribution(days_back=7)
        
        # Verify distribution statistics
        self.assertEqual(dist['total_predictions'], 70)
        self.assertGreater(dist['mean'], 0.0)
        self.assertGreater(dist['stddev'], 0.0)
        self.assertEqual(dist['min'], 0.7)
        self.assertEqual(dist['max'], 0.99)
        self.assertGreater(dist['p50'], 0.0)
        self.assertGreater(dist['p95'], 0.0)


class TestDriftDetectionIntegration(unittest.TestCase):
    """Integration tests for drift detection with inference service."""
    
    def test_prediction_logging_integration(self):
        """Test that predictions are logged during inference."""
        # This would be an integration test with the actual inference service
        # For now, we'll just verify the interface
        
        service = DriftDetectionService()
        
        # Verify log_prediction method signature
        import inspect
        sig = inspect.signature(service.log_prediction)
        params = list(sig.parameters.keys())
        
        self.assertIn('model_version_id', params)
        self.assertIn('user_id', params)
        self.assertIn('meeting_id', params)
        self.assertIn('predicted_gesture', params)
        self.assertIn('confidence', params)
        self.assertIn('latency_ms', params)
        self.assertIn('ground_truth_gesture', params)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDriftDetectionService))
    suite.addTests(loader.loadTestsFromTestCase(TestDriftDetectionIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())

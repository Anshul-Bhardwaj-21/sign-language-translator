#!/usr/bin/env python3
"""
Drift Detection Service (Layer 7 - Production ML)

This module implements basic drift detection for the sign language recognition model.
It logs confidence scores, implements manual accuracy sampling, and calculates weekly metrics.

Features:
- Confidence score logging to database
- Manual accuracy sampling script (100 samples/week)
- Weekly sampling schedule
- Ground truth label collection
- Weekly accuracy metrics calculation

Requirements:
- 52.3: Sample and label production data for accuracy evaluation (100 samples/week)
- 52.4: Alert when F1 score drops below threshold (default 80%)

Phase: MVP

Usage:
    # Log a prediction
    python -c "from drift_detection import log_prediction; log_prediction(...)"
    
    # Run weekly sampling
    python drift_detection.py sample --count 100
    
    # Calculate weekly metrics
    python drift_detection.py calculate-metrics

Author: AI-Powered Meeting Platform Team
"""

import argparse
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriftDetectionService:
    """
    Service for monitoring model performance and detecting drift.
    
    This is the MVP version with basic manual sampling and metrics calculation.
    Phase 2 will add automated drift detection with alerts and rollback.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize drift detection service.
        
        Args:
            db_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        """
        self.db_url = db_url or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/meeting_db'
        )
        self.conn = None
    
    def connect(self):
        """Establish database connection."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self.db_url)
            logger.info("Connected to database")
    
    def close(self):
        """Close database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Closed database connection")
    
    def log_prediction(
        self,
        model_version_id: str,
        user_id: str,
        meeting_id: str,
        predicted_gesture: str,
        confidence: float,
        latency_ms: float,
        ground_truth_gesture: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a prediction to the database for drift monitoring.
        
        Requirements:
            - 52.3: Log predictions for accuracy evaluation
        
        Args:
            model_version_id: UUID of the model version
            user_id: UUID of the user
            meeting_id: UUID of the meeting
            predicted_gesture: Predicted gesture label
            confidence: Prediction confidence (0.0-1.0)
            latency_ms: Inference latency in milliseconds
            ground_truth_gesture: Optional ground truth label (for labeled samples)
            metadata: Optional additional metadata
        
        Returns:
            UUID of the created prediction log entry
        """
        self.connect()
        
        try:
            with self.conn.cursor() as cur:
                # Determine if prediction is correct (if ground truth provided)
                is_correct = None
                if ground_truth_gesture is not None:
                    is_correct = predicted_gesture == ground_truth_gesture
                
                # Insert prediction log
                cur.execute("""
                    INSERT INTO prediction_logs (
                        model_version_id,
                        user_id,
                        meeting_id,
                        predicted_gesture,
                        confidence,
                        ground_truth_gesture,
                        is_correct,
                        latency_ms,
                        metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    model_version_id,
                    user_id,
                    meeting_id,
                    predicted_gesture,
                    confidence,
                    ground_truth_gesture,
                    is_correct,
                    latency_ms,
                    metadata or {}
                ))
                
                prediction_id = cur.fetchone()[0]
                self.conn.commit()
                
                logger.debug(
                    f"Logged prediction: id={prediction_id}, gesture={predicted_gesture}, "
                    f"confidence={confidence:.3f}"
                )
                
                return str(prediction_id)
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to log prediction: {e}")
            raise
    
    def sample_predictions_for_evaluation(
        self,
        count: int = 100,
        days_back: int = 7
    ) -> List[Dict]:
        """
        Sample predictions for manual accuracy evaluation.
        
        Selects random predictions from the past week that haven't been sampled yet.
        
        Requirements:
            - 52.3: Sample production data for accuracy evaluation (100 samples/week)
        
        Args:
            count: Number of samples to select (default: 100)
            days_back: Number of days to look back (default: 7)
        
        Returns:
            List of prediction records to be labeled
        """
        self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                # Select random unsampled predictions
                cur.execute("""
                    SELECT
                        id,
                        model_version_id,
                        user_id,
                        meeting_id,
                        predicted_gesture,
                        confidence,
                        timestamp,
                        latency_ms
                    FROM prediction_logs
                    WHERE timestamp >= %s
                      AND timestamp <= %s
                      AND sampled_for_evaluation = FALSE
                      AND ground_truth_gesture IS NULL
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (start_date, end_date, count))
                
                samples = cur.fetchall()
                
                # Mark as sampled
                if samples:
                    sample_ids = [s['id'] for s in samples]
                    cur.execute("""
                        UPDATE prediction_logs
                        SET sampled_for_evaluation = TRUE
                        WHERE id = ANY(%s)
                    """, (sample_ids,))
                    self.conn.commit()
                
                logger.info(f"Sampled {len(samples)} predictions for evaluation")
                
                return [dict(s) for s in samples]
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to sample predictions: {e}")
            raise
    
    def update_ground_truth(
        self,
        prediction_id: str,
        ground_truth_gesture: str
    ):
        """
        Update a prediction with ground truth label.
        
        Args:
            prediction_id: UUID of the prediction log entry
            ground_truth_gesture: Ground truth gesture label
        """
        self.connect()
        
        try:
            with self.conn.cursor() as cur:
                # Update ground truth and calculate correctness
                cur.execute("""
                    UPDATE prediction_logs
                    SET ground_truth_gesture = %s,
                        is_correct = (predicted_gesture = %s)
                    WHERE id = %s
                """, (ground_truth_gesture, ground_truth_gesture, prediction_id))
                
                self.conn.commit()
                
                logger.info(f"Updated ground truth for prediction {prediction_id}")
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update ground truth: {e}")
            raise
    
    def calculate_weekly_metrics(
        self,
        days_back: int = 7,
        model_version_id: Optional[str] = None
    ) -> Dict:
        """
        Calculate weekly accuracy metrics from labeled samples.
        
        Requirements:
            - 52.4: Alert when F1 score drops below threshold (default 80%)
        
        Args:
            days_back: Number of days to look back (default: 7)
            model_version_id: Optional specific model version to analyze
        
        Returns:
            Dictionary with accuracy metrics
        """
        self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                # Build query
                query = """
                    SELECT
                        COUNT(*) as total_samples,
                        SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) as correct_predictions,
                        AVG(confidence) as avg_confidence,
                        STDDEV(confidence) as stddev_confidence,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) as p50_confidence,
                        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY confidence) as p90_confidence,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY confidence) as p95_confidence,
                        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY confidence) as p99_confidence,
                        AVG(latency_ms) as avg_latency_ms,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms
                    FROM prediction_logs
                    WHERE timestamp >= %s
                      AND timestamp <= %s
                      AND ground_truth_gesture IS NOT NULL
                """
                
                params = [start_date, end_date]
                
                if model_version_id:
                    query += " AND model_version_id = %s"
                    params.append(model_version_id)
                
                cur.execute(query, params)
                result = cur.fetchone()
                
                if result['total_samples'] == 0:
                    logger.warning("No labeled samples found for metrics calculation")
                    return {
                        'total_samples': 0,
                        'accuracy': 0.0,
                        'error_rate': 0.0,
                        'message': 'No labeled samples available'
                    }
                
                # Calculate accuracy
                accuracy = float(result['correct_predictions']) / float(result['total_samples'])
                error_rate = 1.0 - accuracy
                
                # Get per-class metrics
                cur.execute("""
                    SELECT
                        ground_truth_gesture,
                        COUNT(*) as total,
                        SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) as correct,
                        AVG(confidence) as avg_confidence
                    FROM prediction_logs
                    WHERE timestamp >= %s
                      AND timestamp <= %s
                      AND ground_truth_gesture IS NOT NULL
                    """ + (" AND model_version_id = %s" if model_version_id else "") + """
                    GROUP BY ground_truth_gesture
                    ORDER BY total DESC
                """, params)
                
                per_class_metrics = []
                for row in cur.fetchall():
                    class_accuracy = float(row['correct']) / float(row['total'])
                    per_class_metrics.append({
                        'gesture': row['ground_truth_gesture'],
                        'total_samples': row['total'],
                        'accuracy': class_accuracy,
                        'avg_confidence': float(row['avg_confidence'])
                    })
                
                metrics = {
                    'period_start': start_date.isoformat(),
                    'period_end': end_date.isoformat(),
                    'total_samples': result['total_samples'],
                    'correct_predictions': result['correct_predictions'],
                    'accuracy': accuracy,
                    'error_rate': error_rate,
                    'avg_confidence': float(result['avg_confidence']) if result['avg_confidence'] else 0.0,
                    'stddev_confidence': float(result['stddev_confidence']) if result['stddev_confidence'] else 0.0,
                    'p50_confidence': float(result['p50_confidence']) if result['p50_confidence'] else 0.0,
                    'p90_confidence': float(result['p90_confidence']) if result['p90_confidence'] else 0.0,
                    'p95_confidence': float(result['p95_confidence']) if result['p95_confidence'] else 0.0,
                    'p99_confidence': float(result['p99_confidence']) if result['p99_confidence'] else 0.0,
                    'avg_latency_ms': float(result['avg_latency_ms']) if result['avg_latency_ms'] else 0.0,
                    'p95_latency_ms': float(result['p95_latency_ms']) if result['p95_latency_ms'] else 0.0,
                    'per_class_metrics': per_class_metrics
                }
                
                # Check if accuracy is below threshold (Requirement 52.4)
                accuracy_threshold = 0.80  # 80% default threshold
                if accuracy < accuracy_threshold:
                    logger.warning(
                        f"⚠️  ALERT: Accuracy {accuracy:.2%} is below threshold {accuracy_threshold:.2%}"
                    )
                    metrics['alert'] = f"Accuracy below threshold: {accuracy:.2%} < {accuracy_threshold:.2%}"
                else:
                    logger.info(f"✓ Accuracy {accuracy:.2%} is above threshold {accuracy_threshold:.2%}")
                
                return metrics
        
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            raise
    
    def get_confidence_distribution(
        self,
        days_back: int = 7,
        model_version_id: Optional[str] = None
    ) -> Dict:
        """
        Get confidence score distribution for monitoring.
        
        Requirements:
            - 52.1: Monitor confidence score distribution
        
        Args:
            days_back: Number of days to look back (default: 7)
            model_version_id: Optional specific model version to analyze
        
        Returns:
            Dictionary with confidence distribution statistics
        """
        self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                # Build query
                query = """
                    SELECT
                        COUNT(*) as total_predictions,
                        AVG(confidence) as mean,
                        STDDEV(confidence) as stddev,
                        MIN(confidence) as min,
                        MAX(confidence) as max,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) as p50,
                        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY confidence) as p90,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY confidence) as p95,
                        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY confidence) as p99
                    FROM prediction_logs
                    WHERE timestamp >= %s
                      AND timestamp <= %s
                """
                
                params = [start_date, end_date]
                
                if model_version_id:
                    query += " AND model_version_id = %s"
                    params.append(model_version_id)
                
                cur.execute(query, params)
                result = cur.fetchone()
                
                return {
                    'period_start': start_date.isoformat(),
                    'period_end': end_date.isoformat(),
                    'total_predictions': result['total_predictions'],
                    'mean': float(result['mean']) if result['mean'] else 0.0,
                    'stddev': float(result['stddev']) if result['stddev'] else 0.0,
                    'min': float(result['min']) if result['min'] else 0.0,
                    'max': float(result['max']) if result['max'] else 0.0,
                    'p50': float(result['p50']) if result['p50'] else 0.0,
                    'p90': float(result['p90']) if result['p90'] else 0.0,
                    'p95': float(result['p95']) if result['p95'] else 0.0,
                    'p99': float(result['p99']) if result['p99'] else 0.0
                }
        
        except Exception as e:
            logger.error(f"Failed to get confidence distribution: {e}")
            raise


def main():
    """CLI for drift detection operations."""
    parser = argparse.ArgumentParser(
        description="Drift Detection Service - Manual sampling and metrics calculation"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Sample command
    sample_parser = subparsers.add_parser(
        'sample',
        help='Sample predictions for manual evaluation'
    )
    sample_parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of samples to select (default: 100)'
    )
    sample_parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    sample_parser.add_argument(
        '--output',
        type=str,
        help='Output file for samples (JSON format)'
    )
    
    # Calculate metrics command
    metrics_parser = subparsers.add_parser(
        'calculate-metrics',
        help='Calculate weekly accuracy metrics'
    )
    metrics_parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    metrics_parser.add_argument(
        '--model-version',
        type=str,
        help='Specific model version ID to analyze'
    )
    
    # Confidence distribution command
    dist_parser = subparsers.add_parser(
        'confidence-distribution',
        help='Get confidence score distribution'
    )
    dist_parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    dist_parser.add_argument(
        '--model-version',
        type=str,
        help='Specific model version ID to analyze'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize service
    service = DriftDetectionService()
    
    try:
        if args.command == 'sample':
            # Sample predictions
            samples = service.sample_predictions_for_evaluation(
                count=args.count,
                days_back=args.days
            )
            
            print(f"\n✓ Sampled {len(samples)} predictions for evaluation")
            print(f"  Period: Last {args.days} days")
            print(f"  Target: {args.count} samples")
            
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(samples, f, indent=2, default=str)
                print(f"  Output: {args.output}")
            else:
                print("\nSample predictions:")
                for i, sample in enumerate(samples[:5], 1):
                    print(f"  {i}. ID: {sample['id']}")
                    print(f"     Gesture: {sample['predicted_gesture']}")
                    print(f"     Confidence: {sample['confidence']:.3f}")
                    print(f"     Timestamp: {sample['timestamp']}")
                if len(samples) > 5:
                    print(f"  ... and {len(samples) - 5} more")
        
        elif args.command == 'calculate-metrics':
            # Calculate metrics
            metrics = service.calculate_weekly_metrics(
                days_back=args.days,
                model_version_id=args.model_version
            )
            
            print(f"\n📊 Weekly Accuracy Metrics")
            print(f"  Period: {metrics['period_start']} to {metrics['period_end']}")
            print(f"  Total Samples: {metrics['total_samples']}")
            print(f"  Accuracy: {metrics['accuracy']:.2%}")
            print(f"  Error Rate: {metrics['error_rate']:.2%}")
            print(f"\n  Confidence Statistics:")
            print(f"    Mean: {metrics['avg_confidence']:.3f}")
            print(f"    Std Dev: {metrics['stddev_confidence']:.3f}")
            print(f"    P50: {metrics['p50_confidence']:.3f}")
            print(f"    P95: {metrics['p95_confidence']:.3f}")
            print(f"\n  Latency Statistics:")
            print(f"    Mean: {metrics['avg_latency_ms']:.1f} ms")
            print(f"    P95: {metrics['p95_latency_ms']:.1f} ms")
            
            if 'alert' in metrics:
                print(f"\n  ⚠️  ALERT: {metrics['alert']}")
            
            if metrics['per_class_metrics']:
                print(f"\n  Per-Class Accuracy:")
                for class_metric in metrics['per_class_metrics'][:10]:
                    print(f"    {class_metric['gesture']}: {class_metric['accuracy']:.2%} "
                          f"({class_metric['total_samples']} samples)")
        
        elif args.command == 'confidence-distribution':
            # Get confidence distribution
            dist = service.get_confidence_distribution(
                days_back=args.days,
                model_version_id=args.model_version
            )
            
            print(f"\n📈 Confidence Distribution")
            print(f"  Period: {dist['period_start']} to {dist['period_end']}")
            print(f"  Total Predictions: {dist['total_predictions']}")
            print(f"  Mean: {dist['mean']:.3f}")
            print(f"  Std Dev: {dist['stddev']:.3f}")
            print(f"  Min: {dist['min']:.3f}")
            print(f"  Max: {dist['max']:.3f}")
            print(f"  Percentiles:")
            print(f"    P50: {dist['p50']:.3f}")
            print(f"    P90: {dist['p90']:.3f}")
            print(f"    P95: {dist['p95']:.3f}")
            print(f"    P99: {dist['p99']:.3f}")
    
    finally:
        service.close()


if __name__ == "__main__":
    main()

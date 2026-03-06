#!/usr/bin/env python3
"""
Weekly Metrics Calculation Script

This script calculates weekly accuracy metrics from labeled samples.
It should be run after ground truth labels have been added to sampled predictions.

Requirements:
- 52.4: Alert when F1 score drops below threshold (default 80%)

Usage:
    # Calculate metrics for the past week
    python backend/scripts/calculate_weekly_metrics.py
    
    # Calculate metrics with custom parameters
    python backend/scripts/calculate_weekly_metrics.py --days 7 --threshold 0.80

Author: AI-Powered Meeting Platform Team
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from drift_detection import DriftDetectionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Calculate weekly accuracy metrics."""
    parser = argparse.ArgumentParser(
        description="Calculate weekly accuracy metrics"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.80,
        help='Accuracy threshold for alerts (default: 0.80)'
    )
    parser.add_argument(
        '--model-version',
        type=str,
        help='Specific model version ID to analyze'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for metrics (JSON format)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Weekly Accuracy Metrics Calculation")
    logger.info("=" * 60)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Days back: {args.days}")
    logger.info(f"Accuracy threshold: {args.threshold:.2%}")
    
    # Initialize service
    service = DriftDetectionService()
    
    try:
        # Calculate metrics
        logger.info("\nCalculating metrics...")
        metrics = service.calculate_weekly_metrics(
            days_back=args.days,
            model_version_id=args.model_version
        )
        
        # Print results
        logger.info("\n" + "=" * 60)
        logger.info("Metrics Results")
        logger.info("=" * 60)
        logger.info(f"Period: {metrics['period_start']} to {metrics['period_end']}")
        logger.info(f"Total samples: {metrics['total_samples']}")
        
        if metrics['total_samples'] == 0:
            logger.warning("⚠️  No labeled samples found")
            logger.warning("   Please label sampled predictions before calculating metrics")
            return
        
        logger.info(f"\n📊 Accuracy Metrics:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.2%}")
        logger.info(f"  Error rate: {metrics['error_rate']:.2%}")
        logger.info(f"  Correct predictions: {metrics['correct_predictions']}/{metrics['total_samples']}")
        
        logger.info(f"\n📈 Confidence Statistics:")
        logger.info(f"  Mean: {metrics['avg_confidence']:.3f}")
        logger.info(f"  Std Dev: {metrics['stddev_confidence']:.3f}")
        logger.info(f"  P50: {metrics['p50_confidence']:.3f}")
        logger.info(f"  P90: {metrics['p90_confidence']:.3f}")
        logger.info(f"  P95: {metrics['p95_confidence']:.3f}")
        logger.info(f"  P99: {metrics['p99_confidence']:.3f}")
        
        logger.info(f"\n⏱️  Latency Statistics:")
        logger.info(f"  Mean: {metrics['avg_latency_ms']:.1f} ms")
        logger.info(f"  P95: {metrics['p95_latency_ms']:.1f} ms")
        
        # Check threshold (Requirement 52.4)
        if metrics['accuracy'] < args.threshold:
            logger.warning("\n" + "=" * 60)
            logger.warning("⚠️  ALERT: ACCURACY BELOW THRESHOLD")
            logger.warning("=" * 60)
            logger.warning(f"Current accuracy: {metrics['accuracy']:.2%}")
            logger.warning(f"Threshold: {args.threshold:.2%}")
            logger.warning(f"Difference: {(args.threshold - metrics['accuracy']):.2%}")
            logger.warning("\nRecommended actions:")
            logger.warning("1. Review per-class accuracy to identify problematic gestures")
            logger.warning("2. Collect more training data for low-performing classes")
            logger.warning("3. Retrain model with updated dataset")
            logger.warning("4. Consider rolling back to previous model version")
            logger.warning("=" * 60)
        else:
            logger.info(f"\n✓ Accuracy {metrics['accuracy']:.2%} is above threshold {args.threshold:.2%}")
        
        # Show per-class metrics
        if metrics['per_class_metrics']:
            logger.info(f"\n📋 Per-Class Accuracy (top 10):")
            for i, class_metric in enumerate(metrics['per_class_metrics'][:10], 1):
                status = "✓" if class_metric['accuracy'] >= args.threshold else "⚠️"
                logger.info(
                    f"  {status} {i}. {class_metric['gesture']}: "
                    f"{class_metric['accuracy']:.2%} "
                    f"({class_metric['total_samples']} samples, "
                    f"conf: {class_metric['avg_confidence']:.3f})"
                )
            
            # Identify low-performing classes
            low_performing = [
                m for m in metrics['per_class_metrics']
                if m['accuracy'] < args.threshold
            ]
            
            if low_performing:
                logger.warning(f"\n⚠️  {len(low_performing)} gestures below threshold:")
                for class_metric in low_performing[:5]:
                    logger.warning(
                        f"  - {class_metric['gesture']}: {class_metric['accuracy']:.2%}"
                    )
                if len(low_performing) > 5:
                    logger.warning(f"  ... and {len(low_performing) - 5} more")
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            logger.info(f"\n✓ Saved metrics to: {args.output}")
        
        logger.info("\n" + "=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Metrics calculation failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        service.close()


if __name__ == "__main__":
    main()

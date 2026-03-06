#!/usr/bin/env python3
"""
Weekly Drift Detection Sampling Script

This script runs weekly to sample 100 predictions for manual accuracy evaluation.
It should be scheduled using cron or a task scheduler.

Requirements:
- 52.3: Sample and label production data for accuracy evaluation (100 samples/week)

Usage:
    # Run weekly sampling
    python backend/scripts/weekly_drift_sampling.py
    
    # Run with custom parameters
    python backend/scripts/weekly_drift_sampling.py --count 100 --days 7

Schedule with cron (every Monday at 9 AM):
    0 9 * * 1 cd /path/to/project && python backend/scripts/weekly_drift_sampling.py

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
    """Run weekly sampling for drift detection."""
    parser = argparse.ArgumentParser(
        description="Weekly drift detection sampling"
    )
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of samples to select (default: 100)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='backend/storage/drift_samples',
        help='Output directory for samples'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Weekly Drift Detection Sampling")
    logger.info("=" * 60)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Sample count: {args.count}")
    logger.info(f"Days back: {args.days}")
    
    # Initialize service
    service = DriftDetectionService()
    
    try:
        # Sample predictions
        logger.info("\nSampling predictions for evaluation...")
        samples = service.sample_predictions_for_evaluation(
            count=args.count,
            days_back=args.days
        )
        
        if len(samples) == 0:
            logger.warning("⚠️  No predictions available for sampling")
            logger.warning("   This may indicate:")
            logger.warning("   - No inference requests in the past week")
            logger.warning("   - All predictions already sampled")
            return
        
        logger.info(f"✓ Sampled {len(samples)} predictions")
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save samples to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"samples_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(samples, f, indent=2, default=str)
        
        logger.info(f"✓ Saved samples to: {output_file}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Sampling Summary")
        logger.info("=" * 60)
        logger.info(f"Total samples: {len(samples)}")
        logger.info(f"Output file: {output_file}")
        
        # Show confidence distribution
        confidences = [s['confidence'] for s in samples]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)
            logger.info(f"\nConfidence distribution:")
            logger.info(f"  Mean: {avg_conf:.3f}")
            logger.info(f"  Min: {min_conf:.3f}")
            logger.info(f"  Max: {max_conf:.3f}")
        
        # Show gesture distribution
        gestures = {}
        for s in samples:
            gesture = s['predicted_gesture']
            gestures[gesture] = gestures.get(gesture, 0) + 1
        
        logger.info(f"\nGesture distribution (top 10):")
        for gesture, count in sorted(gestures.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {gesture}: {count}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Next Steps")
        logger.info("=" * 60)
        logger.info("1. Review the sampled predictions in the output file")
        logger.info("2. Manually label each prediction with ground truth")
        logger.info("3. Update the database with ground truth labels:")
        logger.info("   python -c \"from drift_detection import DriftDetectionService; ")
        logger.info("   s = DriftDetectionService(); ")
        logger.info("   s.update_ground_truth('<prediction_id>', '<ground_truth_gesture>')\"")
        logger.info("4. Calculate weekly metrics:")
        logger.info("   python backend/drift_detection.py calculate-metrics")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Sampling failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        service.close()


if __name__ == "__main__":
    main()

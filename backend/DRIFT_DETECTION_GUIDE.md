# Drift Detection Guide

## Overview

This guide explains how to use the drift detection system for monitoring sign language recognition model performance in production.

The drift detection system implements **Requirements 52.3 and 52.4** from the advanced meeting features specification:
- **52.3**: Sample and label production data for accuracy evaluation (100 samples/week)
- **52.4**: Alert when F1 score drops below threshold (default 80%)

## Architecture

The drift detection system consists of three main components:

1. **Prediction Logging** (`drift_detection.py`): Logs all predictions with confidence scores to the database
2. **Weekly Sampling** (`scripts/weekly_drift_sampling.py`): Samples 100 predictions per week for manual labeling
3. **Metrics Calculation** (`scripts/calculate_weekly_metrics.py`): Calculates accuracy metrics and alerts on degradation

## Database Schema

The system uses the `prediction_logs` table:

```sql
CREATE TABLE prediction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id UUID REFERENCES model_versions(id),
    user_id UUID REFERENCES users(id),
    meeting_id UUID REFERENCES meetings(id),
    predicted_gesture TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    ground_truth_gesture TEXT,
    is_correct BOOLEAN,
    sampled_for_evaluation BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW(),
    latency_ms FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

## Usage

### 1. Automatic Prediction Logging

Predictions are automatically logged by the inference service. No manual action required.

The inference service logs every prediction:

```python
from drift_detection import DriftDetectionService

drift_service = DriftDetectionService()

# Log a prediction
drift_service.log_prediction(
    model_version_id="uuid-of-model-version",
    user_id="uuid-of-user",
    meeting_id="uuid-of-meeting",
    predicted_gesture="hello",
    confidence=0.95,
    latency_ms=150.5
)
```

### 2. Weekly Sampling (Manual Process)

Run the weekly sampling script to select 100 random predictions for manual evaluation:

```bash
# Run weekly sampling
python backend/scripts/weekly_drift_sampling.py

# Custom parameters
python backend/scripts/weekly_drift_sampling.py --count 100 --days 7 --output-dir backend/storage/drift_samples
```

**Output**: A JSON file with sampled predictions in `backend/storage/drift_samples/samples_YYYYMMDD_HHMMSS.json`

**Schedule**: Set up a cron job or task scheduler to run this weekly:

```bash
# Cron example (every Monday at 9 AM)
0 9 * * 1 cd /path/to/project && python backend/scripts/weekly_drift_sampling.py
```

### 3. Manual Labeling

After sampling, manually review and label each prediction:

1. Open the samples JSON file
2. For each prediction, determine the correct ground truth gesture
3. Update the database with ground truth labels:

```python
from drift_detection import DriftDetectionService

service = DriftDetectionService()

# Update ground truth for a prediction
service.update_ground_truth(
    prediction_id="uuid-of-prediction",
    ground_truth_gesture="hello"
)
```

Or use the CLI:

```bash
python -c "from drift_detection import DriftDetectionService; \
s = DriftDetectionService(); \
s.update_ground_truth('prediction-id', 'ground-truth-gesture')"
```

### 4. Calculate Weekly Metrics

After labeling, calculate accuracy metrics:

```bash
# Calculate metrics for the past week
python backend/scripts/calculate_weekly_metrics.py

# Custom parameters
python backend/scripts/calculate_weekly_metrics.py --days 7 --threshold 0.80

# Save metrics to file
python backend/scripts/calculate_weekly_metrics.py --output metrics.json
```

**Output**:
```
📊 Weekly Accuracy Metrics
  Period: 2024-01-01 to 2024-01-08
  Total Samples: 100
  Accuracy: 85.00%
  Error Rate: 15.00%

  Confidence Statistics:
    Mean: 0.850
    Std Dev: 0.100
    P50: 0.850
    P95: 0.970

  Latency Statistics:
    Mean: 150.0 ms
    P95: 180.0 ms

  Per-Class Accuracy:
    ✓ 1. hello: 90.00% (20 samples, conf: 0.900)
    ✓ 2. goodbye: 85.00% (20 samples, conf: 0.850)
    ⚠️ 3. thanks: 75.00% (20 samples, conf: 0.800)
```

### 5. Alerts

If accuracy drops below the threshold (default 80%), an alert is displayed:

```
⚠️  ALERT: ACCURACY BELOW THRESHOLD
Current accuracy: 75.00%
Threshold: 80.00%
Difference: 5.00%

Recommended actions:
1. Review per-class accuracy to identify problematic gestures
2. Collect more training data for low-performing classes
3. Retrain model with updated dataset
4. Consider rolling back to previous model version
```

## CLI Commands

### Drift Detection Service

```bash
# Sample predictions for evaluation
python backend/drift_detection.py sample --count 100 --days 7 --output samples.json

# Calculate weekly metrics
python backend/drift_detection.py calculate-metrics --days 7 --threshold 0.80

# Get confidence distribution
python backend/drift_detection.py confidence-distribution --days 7
```

### Weekly Sampling Script

```bash
# Run weekly sampling
python backend/scripts/weekly_drift_sampling.py

# Options:
#   --count: Number of samples (default: 100)
#   --days: Days to look back (default: 7)
#   --output-dir: Output directory (default: backend/storage/drift_samples)
```

### Metrics Calculation Script

```bash
# Calculate weekly metrics
python backend/scripts/calculate_weekly_metrics.py

# Options:
#   --days: Days to look back (default: 7)
#   --threshold: Accuracy threshold (default: 0.80)
#   --model-version: Specific model version ID
#   --output: Output file for metrics (JSON)
```

## Monitoring Workflow

### Weekly Workflow

1. **Monday 9 AM**: Automated sampling script runs
   - Selects 100 random predictions from past week
   - Saves to `backend/storage/drift_samples/samples_YYYYMMDD_HHMMSS.json`

2. **Monday-Wednesday**: Manual labeling
   - ML engineer reviews sampled predictions
   - Labels each prediction with ground truth
   - Updates database with ground truth labels

3. **Thursday**: Calculate metrics
   - Run metrics calculation script
   - Review accuracy and per-class metrics
   - Check for alerts

4. **Friday**: Take action if needed
   - If accuracy < 80%: Investigate and plan retraining
   - If accuracy >= 80%: Continue monitoring

### Continuous Monitoring

The system also provides real-time monitoring:

```python
from drift_detection import DriftDetectionService

service = DriftDetectionService()

# Get confidence distribution (last 7 days)
dist = service.get_confidence_distribution(days_back=7)

print(f"Mean confidence: {dist['mean']:.3f}")
print(f"P95 confidence: {dist['p95']:.3f}")
print(f"Total predictions: {dist['total_predictions']}")
```

## Integration with Inference Service

The inference service automatically logs predictions:

```python
# In inference_service.py

from drift_detection import DriftDetectionService

drift_service = DriftDetectionService()

# After making a prediction
drift_service.log_prediction(
    model_version_id=current_model_version_id,
    user_id=user_id,
    meeting_id=meeting_id,
    predicted_gesture=gesture,
    confidence=confidence,
    latency_ms=latency_ms
)
```

## Best Practices

### Sampling

- **Sample size**: 100 predictions per week provides good statistical power
- **Random sampling**: Ensures representative sample of production data
- **No duplicates**: Already sampled predictions are excluded

### Labeling

- **Consistency**: Use same labeling criteria across all samples
- **Quality**: Take time to accurately label each prediction
- **Documentation**: Document any ambiguous cases

### Metrics

- **Threshold**: 80% accuracy is the default threshold
- **Per-class**: Monitor per-class accuracy to identify specific issues
- **Trends**: Track metrics over time to detect gradual drift

### Actions

When accuracy drops below threshold:

1. **Investigate**: Review per-class metrics and confusion patterns
2. **Collect data**: Gather more training data for low-performing classes
3. **Retrain**: Train new model with updated dataset
4. **Test**: Validate new model on held-out test set
5. **Deploy**: Use canary deployment to gradually roll out new model
6. **Monitor**: Continue monitoring to ensure improvement

## Phase 2 Enhancements

The MVP implements basic manual drift detection. Phase 2 will add:

- **Automated drift detection**: KL divergence and KS tests
- **Automated alerts**: Slack/email notifications
- **Automated rollback**: Automatic model rollback on severe drift
- **A/B testing**: Compare old vs new models in production
- **Canary deployments**: Gradual rollout with monitoring
- **Predictive drift**: Detect drift before accuracy drops

## Troubleshooting

### No predictions to sample

**Problem**: `sample_predictions_for_evaluation` returns 0 samples

**Solutions**:
- Check that inference service is running and logging predictions
- Verify database connection
- Check that predictions exist in the past week
- Ensure predictions haven't already been sampled

### No labeled samples for metrics

**Problem**: `calculate_weekly_metrics` returns 0 samples

**Solutions**:
- Run sampling script first
- Label sampled predictions with ground truth
- Verify ground truth labels were saved to database

### Database connection errors

**Problem**: `psycopg2.OperationalError: connection refused`

**Solutions**:
- Ensure PostgreSQL is running
- Check DATABASE_URL environment variable
- Verify database credentials
- Check network connectivity

## Testing

Run the drift detection tests:

```bash
# Simple tests (no database required)
python backend/test_drift_detection_simple.py

# Full tests (requires PostgreSQL)
python backend/test_drift_detection.py
```

## References

- **Requirements**: `.kiro/specs/advanced-meeting-features/requirements.md` (Requirement 52)
- **Design**: `.kiro/specs/advanced-meeting-features/design.md` (Layer 7 - Production ML)
- **Tasks**: `.kiro/specs/advanced-meeting-features/tasks.md` (Task 5.17)

## Support

For questions or issues:
1. Check this guide
2. Review the code documentation in `drift_detection.py`
3. Run the test suite to verify functionality
4. Contact the ML engineering team

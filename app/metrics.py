"""Performance metrics and monitoring for production deployment."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque
import statistics


@dataclass
class ComponentMetrics:
    """Metrics for a single component."""
    name: str
    latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    success_count: int = 0
    failure_count: int = 0
    last_update: float = 0.0
    
    def record_success(self, latency_ms: float):
        """Record successful operation."""
        self.latencies.append(latency_ms)
        self.success_count += 1
        self.last_update = time.time()
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_update = time.time()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0.0
    
    @property
    def avg_latency(self) -> float:
        """Calculate average latency."""
        return statistics.mean(self.latencies) if self.latencies else 0.0
    
    @property
    def p95_latency(self) -> float:
        """Calculate 95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx] if idx < len(sorted_latencies) else sorted_latencies[-1]


class MetricsCollector:
    """
    Collects and aggregates performance metrics.
    
    Tracks:
    - Component latencies
    - Success/failure rates
    - FPS and throughput
    - Detection confidence
    - Error rates
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentMetrics] = {}
        self.start_time = time.time()
        
        # Specific metrics
        self.fps_history: deque = deque(maxlen=100)
        self.confidence_history: deque = deque(maxlen=100)
        self.hand_detection_rate: deque = deque(maxlen=100)
        
        # Counters
        self.total_frames = 0
        self.frames_with_hand = 0
        self.gestures_recognized = 0
        self.false_positives = 0
    
    def get_component(self, name: str) -> ComponentMetrics:
        """Get or create component metrics."""
        if name not in self.components:
            self.components[name] = ComponentMetrics(name=name)
        return self.components[name]
    
    def record_latency(self, component: str, latency_ms: float, success: bool = True):
        """Record component latency."""
        metrics = self.get_component(component)
        if success:
            metrics.record_success(latency_ms)
        else:
            metrics.record_failure()
    
    def record_fps(self, fps: float):
        """Record FPS measurement."""
        self.fps_history.append(fps)
    
    def record_confidence(self, confidence: float):
        """Record prediction confidence."""
        self.confidence_history.append(confidence)
    
    def record_hand_detection(self, detected: bool):
        """Record hand detection result."""
        self.total_frames += 1
        if detected:
            self.frames_with_hand += 1
        self.hand_detection_rate.append(1.0 if detected else 0.0)
    
    def record_gesture_recognized(self):
        """Record successful gesture recognition."""
        self.gestures_recognized += 1
    
    def record_false_positive(self):
        """Record false positive detection."""
        self.false_positives += 1
    
    def get_summary(self) -> Dict:
        """Get comprehensive metrics summary."""
        uptime = time.time() - self.start_time
        
        summary = {
            'uptime_seconds': uptime,
            'total_frames': self.total_frames,
            'frames_with_hand': self.frames_with_hand,
            'gestures_recognized': self.gestures_recognized,
            'false_positives': self.false_positives,
        }
        
        # FPS metrics
        if self.fps_history:
            summary['fps'] = {
                'current': self.fps_history[-1],
                'average': statistics.mean(self.fps_history),
                'min': min(self.fps_history),
                'max': max(self.fps_history),
            }
        
        # Confidence metrics
        if self.confidence_history:
            summary['confidence'] = {
                'average': statistics.mean(self.confidence_history),
                'min': min(self.confidence_history),
                'max': max(self.confidence_history),
            }
        
        # Hand detection rate
        if self.hand_detection_rate:
            summary['hand_detection_rate'] = statistics.mean(self.hand_detection_rate) * 100
        
        # Component metrics
        summary['components'] = {}
        for name, metrics in self.components.items():
            summary['components'][name] = {
                'success_rate': metrics.success_rate,
                'avg_latency_ms': metrics.avg_latency,
                'p95_latency_ms': metrics.p95_latency,
                'total_operations': metrics.success_count + metrics.failure_count,
            }
        
        return summary
    
    def get_health_status(self) -> str:
        """
        Get overall system health status.
        
        Returns: 'healthy', 'degraded', or 'unhealthy'
        """
        summary = self.get_summary()
        
        # Check FPS
        if 'fps' in summary:
            if summary['fps']['average'] < 10:
                return 'unhealthy'
            elif summary['fps']['average'] < 15:
                return 'degraded'
        
        # Check component success rates
        for comp_metrics in summary.get('components', {}).values():
            if comp_metrics['success_rate'] < 80:
                return 'unhealthy'
            elif comp_metrics['success_rate'] < 95:
                return 'degraded'
        
        # Check latencies
        for comp_metrics in summary.get('components', {}).values():
            if comp_metrics['p95_latency_ms'] > 100:
                return 'degraded'
        
        return 'healthy'
    
    def reset(self):
        """Reset all metrics."""
        self.components.clear()
        self.fps_history.clear()
        self.confidence_history.clear()
        self.hand_detection_rate.clear()
        self.total_frames = 0
        self.frames_with_hand = 0
        self.gestures_recognized = 0
        self.false_positives = 0
        self.start_time = time.time()


class PerformanceMonitor:
    """Context manager for measuring component performance."""
    
    def __init__(self, metrics: MetricsCollector, component: str):
        self.metrics = metrics
        self.component = component
        self.start_time = 0.0
        self.success = True
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.perf_counter() - self.start_time) * 1000
        self.success = exc_type is None
        self.metrics.record_latency(self.component, latency_ms, self.success)
        return False  # Don't suppress exceptions
    
    def mark_failure(self):
        """Mark operation as failed."""
        self.success = False


# Global metrics collector
_global_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics

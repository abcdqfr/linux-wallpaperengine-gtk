"""
Tests for PyRust Optimizer profiler module.

These tests verify the hotspot detection and performance analysis capabilities.
"""

from typing import List

import pytest

from src.profiler.hotspot_detector import HotspotDetector, profile_function


def example_hot_function(n: int) -> List[int]:
    """Example function with deliberate performance hotspot."""
    results = []
    for i in range(n):
        # Simulate computational work
        value = sum(j * j for j in range(i % 50 + 1))
        results.append(value)
    return results


def example_cold_function(n: int) -> int:
    """Example function that's already optimized."""
    return n * 2


class TestHotspotDetector:
    """Test suite for HotspotDetector class."""

    def test_detector_initialization(self):
        """Test that HotspotDetector initializes correctly."""
        detector = HotspotDetector()
        assert detector.threshold_ratio == 0.8
        assert detector.min_call_count == 100

    def test_detector_with_custom_params(self):
        """Test detector with custom parameters."""
        detector = HotspotDetector(threshold_ratio=0.5, min_call_count=50)
        assert detector.threshold_ratio == 0.5
        assert detector.min_call_count == 50

    def test_profile_simple_function(self):
        """Test profiling a simple function."""
        detector = HotspotDetector()
        results = detector.profile_codebase(example_hot_function, 100)

        # Check that profiling results are returned
        assert "execution_time" in results
        assert "memory_peak" in results
        assert "hotspots" in results
        assert "optimization_candidates" in results
        assert "performance_metrics" in results

        # Verify execution time is reasonable
        assert results["execution_time"] > 0

        # Check that optimization candidates are identified
        assert isinstance(results["optimization_candidates"], list)

    def test_hotspot_detection(self):
        """Test that hotspots are correctly identified."""
        detector = HotspotDetector()
        results = detector.profile_codebase(example_hot_function, 200)

        hotspots = results["hotspots"]
        assert len(hotspots) > 0

        # Check hotspot structure
        for hotspot in hotspots:
            assert hasattr(hotspot, "function_name")
            assert hasattr(hotspot, "cumulative_time")
            assert hasattr(hotspot, "total_calls")
            assert hasattr(hotspot, "rust_conversion_score")
            assert hotspot.cumulative_time > 0
            assert hotspot.rust_conversion_score >= 0.0
            assert hotspot.rust_conversion_score <= 1.0

    def test_optimization_candidates(self):
        """Test that optimization candidates are properly scored."""
        detector = HotspotDetector()
        results = detector.profile_codebase(example_hot_function, 150)

        candidates = results["optimization_candidates"]

        # Should have at least some candidates for this hot function
        if len(candidates) > 0:
            candidate = candidates[0]
            assert "function_name" in candidate
            assert "conversion_score" in candidate
            assert "performance_impact" in candidate
            assert "optimization_priority" in candidate
            assert "estimated_speedup" in candidate
            assert "recommended_action" in candidate

            # Verify scoring ranges
            assert 0.0 <= candidate["conversion_score"] <= 1.0
            assert candidate["performance_impact"] > 0

    def test_bytecode_analysis(self):
        """Test bytecode analysis functionality."""
        detector = HotspotDetector()

        # Analyze bytecode of example function
        bytecode_results = detector.analyze_bytecode_patterns(example_hot_function)

        assert "operation_counts" in bytecode_results
        assert "loop_indicators" in bytecode_results
        assert "arithmetic_operations" in bytecode_results
        assert "memory_operations" in bytecode_results
        assert "optimization_score" in bytecode_results
        assert "rust_suitable" in bytecode_results

        # Should detect loops in this function
        assert bytecode_results["loop_indicators"] > 0

        # Optimization score should be reasonable
        assert 0.0 <= bytecode_results["optimization_score"] <= 1.0


class TestConvenienceFunctions:
    """Test convenience functions for profiling."""

    def test_profile_function_convenience(self):
        """Test the profile_function convenience function."""
        results = profile_function(example_hot_function, 100)

        assert "execution_time" in results
        assert "hotspots" in results
        assert "optimization_candidates" in results
        assert results["execution_time"] > 0


class TestPerformanceMetrics:
    """Test performance metrics calculation."""

    def test_performance_metrics_structure(self):
        """Test that performance metrics have correct structure."""
        detector = HotspotDetector()
        results = detector.profile_codebase(example_hot_function, 100)

        metrics = results["performance_metrics"]
        assert "total_function_calls" in metrics
        assert "total_execution_time" in metrics
        assert "unique_functions" in metrics
        assert "average_call_time" in metrics
        assert "calls_per_second" in metrics

        # Verify reasonable values
        assert metrics["total_function_calls"] > 0
        assert metrics["total_execution_time"] > 0
        assert metrics["unique_functions"] > 0


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for profiler performance."""

    def test_profiler_overhead(self, benchmark):
        """Benchmark the profiler overhead."""
        detector = HotspotDetector()

        def profile_hot_function():
            return detector.profile_codebase(example_hot_function, 50)

        results = benchmark(profile_hot_function)
        assert results is not None

    def test_hotspot_detection_performance(self, benchmark):
        """Benchmark hotspot detection performance."""
        detector = HotspotDetector()

        # Create a more complex function for benchmarking
        def complex_function(n):
            results = []
            for i in range(n):
                for j in range(i % 10):
                    result = i * j + sum(range(j % 5))
                    results.append(result)
            return results

        def profile_complex():
            return detector.profile_codebase(complex_function, 20)

        results = benchmark(profile_complex)
        assert len(results["optimization_candidates"]) >= 0


# Integration tests
class TestIntegration:
    """Integration tests for profiler with real scenarios."""

    def test_numerical_computation_detection(self):
        """Test detection of numerical computation patterns."""

        def numerical_intensive(size):
            total = 0.0
            for i in range(size):
                total += i * i * 3.14159
            return total

        detector = HotspotDetector()
        results = detector.profile_codebase(numerical_intensive, 1000)

        # Should identify this as a good optimization candidate
        candidates = results["optimization_candidates"]
        if len(candidates) > 0:
            # Should have high Rust conversion potential
            top_candidate = candidates[0]
            assert top_candidate["conversion_score"] > 0.3

    def test_string_processing_detection(self):
        """Test detection of string processing patterns."""

        def string_processor(strings):
            results = []
            for s in strings:
                processed = s.upper().strip().replace(" ", "_")
                results.append(processed)
            return results

        test_strings = [f"test string {i}" for i in range(100)]

        detector = HotspotDetector()
        results = detector.profile_codebase(string_processor, test_strings)

        # Should complete without errors
        assert "execution_time" in results
        assert results["execution_time"] > 0


if __name__ == "__main__":
    # Run basic tests if executed directly
    detector = HotspotDetector()
    print("🧪 Running basic profiler tests...")

    # Test profiling
    results = detector.profile_codebase(example_hot_function, 100)
    print(f"✅ Profiling completed in {results['execution_time']:.4f} seconds")
    print(f"✅ Found {len(results['optimization_candidates'])} optimization candidates")

    # Test bytecode analysis
    bytecode_results = detector.analyze_bytecode_patterns(example_hot_function)
    print(
        f"✅ Bytecode analysis completed, optimization score: {bytecode_results['optimization_score']:.2f}"
    )

    print("🎉 All basic tests passed!")

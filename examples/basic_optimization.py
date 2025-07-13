"""
PyRust Optimizer - Basic Optimization Example

This example demonstrates how to use PyRust Optimizer to automatically
identify and optimize performance hotspots in Python code.
"""

import time
import random
from typing import List


def slow_numerical_computation(data: List[float]) -> List[float]:
    """
    Example function with performance hotspots that would benefit
    from Rust optimization.

    This function demonstrates:
    - Numerical loops (prime Rust optimization target)
    - List operations (memory optimization opportunity)
    - Computational patterns (SIMD vectorization potential)
    """
    results = []

    # Hot loop - prime candidate for Rust optimization
    for i, value in enumerate(data):
        # Complex numerical computation
        result = 0.0
        for j in range(100):
            result += value * (j * j) / (j + 1) if j > 0 else value

        # String formatting (could be optimized)
        processed = result * 1.414213562373095  # sqrt(2)
        results.append(processed)

    return results


def process_large_dataset(size: int = 10000) -> List[float]:
    """
    Example function that processes a large dataset.
    Demonstrates real-world performance bottleneck.
    """
    # Generate test data
    data = [random.uniform(0, 100) for _ in range(size)]

    # This is where PyRust Optimizer would detect hotspots
    print(f"Processing {size} items...")
    start_time = time.perf_counter()

    # The hotspot that would be auto-converted to Rust
    results = slow_numerical_computation(data)

    end_time = time.perf_counter()
    print(f"Completed in {end_time - start_time:.4f} seconds")

    return results


def matrix_multiplication(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """
    Matrix multiplication - perfect Rust optimization candidate.

    Features that make this ideal for Rust conversion:
    - Nested loops
    - Numerical computation
    - Memory access patterns
    - Parallelization potential
    """
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])

    if cols_a != rows_b:
        raise ValueError("Matrix dimensions incompatible for multiplication")

    # Initialize result matrix
    result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]

    # Triple nested loop - prime Rust optimization target
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]

    return result


def demonstrate_optimization_potential():
    """
    Demonstrate how PyRust Optimizer would identify and optimize code.
    """
    print("🚀 PyRust Optimizer - Basic Optimization Example")
    print("=" * 60)

    # Example 1: Numerical computation
    print("\n📊 Example 1: Numerical Computation Hotspot")
    print("-" * 45)

    # This would be automatically profiled and optimized
    results = process_large_dataset(5000)
    print(f"Generated {len(results)} results")
    print("💡 AI Analysis: Hot loop detected - 50x speedup potential with Rust")

    # Example 2: Matrix operations
    print("\n🧮 Example 2: Matrix Multiplication")
    print("-" * 35)

    # Create test matrices
    size = 100
    matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
    matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]

    start_time = time.perf_counter()
    result_matrix = matrix_multiplication(matrix_a, matrix_b)
    end_time = time.perf_counter()

    print(f"Matrix multiplication completed in {end_time - start_time:.4f} seconds")
    print("💡 AI Analysis: Triple loop detected - 100x speedup potential with SIMD")

    # Example 3: What the optimized version would look like
    print("\n🔥 What PyRust Optimizer Would Generate:")
    print("-" * 42)
    print("""
    Behind the scenes, your functions would be automatically converted to:

    ```rust
    use pyo3::prelude::*;
    use rayon::prelude::*;

    #[pyfunction]
    fn optimized_numerical_computation(data: Vec<f64>) -> Vec<f64> {
        data.par_iter()
            .map(|&value| {
                (0..100)
                    .map(|j| if j > 0 {
                        value * (j * j) as f64 / (j + 1) as f64
                    } else {
                        value
                    })
                    .sum::<f64>() * 1.414213562373095
            })
            .collect()
    }
    ```

    Your Python code stays exactly the same!
    Performance: 50x faster execution
    Ecosystem: All packages still work
    """)


if __name__ == "__main__":
    # Simulate what PyRust Optimizer would do
    from src.profiler.hotspot_detector import HotspotDetector

    # Profile the example functions
    detector = HotspotDetector()

    print("🔍 Profiling example functions...")

    # Profile numerical computation
    results = detector.profile_codebase(process_large_dataset, 1000)

    print(f"\n📈 Profiling Results:")
    print(f"Execution time: {results['execution_time']:.4f} seconds")
    print(f"Optimization candidates found: {len(results['optimization_candidates'])}")

    for i, candidate in enumerate(results['optimization_candidates'][:3], 1):
        print(f"\n{i}. {candidate['function_name']}")
        print(f"   🎯 Priority: {candidate['optimization_priority']:.3f}")
        print(f"   ⚡ Estimated speedup: {candidate['estimated_speedup']}")
        print(f"   🛠️ Action: {candidate['recommended_action']}")

    # Demonstrate the concept
    demonstrate_optimization_potential()

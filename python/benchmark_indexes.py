"""
benchmark_indexes.py
====================
Compare four index structures on 1M integer keys.

Usage:
    pip install numpy scikit-learn   # or: uv add numpy scikit-learn
    python benchmark_indexes.py

Output:
    Results table printed to stdout + saved to results/benchmark_results.txt
"""

import bisect
import os
import time
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor


# ══════════════════════════════════════════════════════
#  INDEX STRUCTURES
# ══════════════════════════════════════════════════════

class BinarySearchIndex:
    """Sorted array + binary search. Equivalent to B-Tree point lookup."""

    def __init__(self, keys):
        self.keys = np.array(sorted(keys), dtype=np.int64)
        self.mae = None
        self.max_err = None

    def lookup(self, key):
        pos = bisect.bisect_left(self.keys, key)
        if pos < len(self.keys) and self.keys[pos] == key:
            return pos
        return -1

    def size_bytes(self):
        return self.keys.nbytes


class LinearLearnedIndex:
    """
    Linear regression as CDF approximation.
    Predicts position in O(1), then refines with local binary search
    in the window [pred - max_err, pred + max_err].
    """

    def __init__(self, keys):
        self.keys = np.array(sorted(keys), dtype=np.int64)
        n = len(self.keys)
        positions = np.arange(n, dtype=np.float64)
        X = self.keys.reshape(-1, 1)

        self.model = LinearRegression().fit(X, positions)
        preds = self.model.predict(X).astype(int)
        errors = np.abs(preds - np.arange(n))
        self.max_err = int(errors.max())
        self.mae = round(float(errors.mean()), 1)

    def lookup(self, key):
        pred = int(self.model.predict([[key]])[0])
        lo = max(0, pred - self.max_err)
        hi = min(len(self.keys) - 1, pred + self.max_err)
        pos = bisect.bisect_left(self.keys, key, lo, hi + 1)
        if pos <= hi and self.keys[pos] == key:
            return pos
        return -1

    def size_bytes(self):
        # Two float64 values: slope (a) and intercept (b)
        return 16


class TwoLevelRMI:
    """
    Two-level Recursive Model Index.
    Level 1: one global linear model that selects a bucket.
    Level 2: N local linear models that predict exact position.
    Reference: Kraska et al., SIGMOD 2018.
    """

    def __init__(self, keys, n_models=100):
        self.keys = np.array(sorted(keys), dtype=np.int64)
        n = len(self.keys)
        self.n_models = n_models
        positions = np.arange(n, dtype=np.float64)

        # Level 1: global model
        self.l1 = LinearRegression().fit(self.keys.reshape(-1, 1), positions)

        # Assign keys to buckets based on level-1 predictions
        bucket_ids = np.clip(
            (self.l1.predict(self.keys.reshape(-1, 1)) * n_models / n).astype(int),
            0, n_models - 1
        )

        # Level 2: one local model per bucket
        self.l2, self.max_errs = [], []
        for b in range(n_models):
            mask = bucket_ids == b
            if mask.sum() < 2:
                self.l2.append(None)
                self.max_errs.append(n)
                continue
            m = LinearRegression().fit(
                self.keys[mask].reshape(-1, 1), positions[mask]
            )
            preds = m.predict(self.keys[mask].reshape(-1, 1)).astype(int)
            self.l2.append(m)
            self.max_errs.append(int(np.abs(preds - positions[mask].astype(int)).max()))

        # Compute overall MAE
        all_preds = []
        for key in self.keys:
            b = int(np.clip(self.l1.predict([[key]])[0] * n_models / n, 0, n_models - 1))
            m = self.l2[b]
            all_preds.append(0 if m is None else int(m.predict([[key]])[0]))
        self.mae = round(float(np.abs(np.array(all_preds) - positions).mean()), 1)
        self.max_err = max(self.max_errs)

    def lookup(self, key):
        n = len(self.keys)
        b = int(np.clip(
            self.l1.predict([[key]])[0] * self.n_models / n, 0, self.n_models - 1
        ))
        m = self.l2[b]
        if m is None:
            pos = bisect.bisect_left(self.keys, key)
        else:
            pred = int(m.predict([[key]])[0])
            lo = max(0, pred - self.max_errs[b])
            hi = min(n - 1, pred + self.max_errs[b])
            pos = bisect.bisect_left(self.keys, key, lo, hi + 1)
            if pos > hi:
                return -1
        if pos < n and self.keys[pos] == key:
            return pos
        return -1

    def size_bytes(self):
        # Level 1: 16 bytes; Level 2: n_models * 16 bytes
        return 16 + self.n_models * 16


class DTLearnedIndex:
    """
    Decision Tree Regressor as a piecewise-constant CDF approximation.
    Each leaf covers a key range and stores a position estimate.
    """

    def __init__(self, keys, max_depth=12):
        self.keys = np.array(sorted(keys), dtype=np.int64)
        n = len(self.keys)
        positions = np.arange(n, dtype=np.float64)

        self.model = DecisionTreeRegressor(max_depth=max_depth)
        self.model.fit(self.keys.reshape(-1, 1), positions)

        preds = self.model.predict(self.keys.reshape(-1, 1)).astype(int)
        errors = np.abs(preds - np.arange(n))
        self.max_err = int(errors.max())
        self.mae = round(float(errors.mean()), 1)

    def lookup(self, key):
        pred = int(self.model.predict([[key]])[0])
        lo = max(0, pred - self.max_err)
        hi = min(len(self.keys) - 1, pred + self.max_err)
        pos = bisect.bisect_left(self.keys, key, lo, hi + 1)
        if pos <= hi and self.keys[pos] == key:
            return pos
        return -1

    def size_bytes(self):
        return self.model.tree_.node_count * 100


# ══════════════════════════════════════════════════════
#  BENCHMARK RUNNER
# ══════════════════════════════════════════════════════

def run_benchmark(index, queries, name):
    # Warm up the CPU cache
    for k in queries[:1000]:
        index.lookup(int(k))

    # Main measurement loop
    latencies = []
    hits = 0
    for k in queries:
        t0 = time.perf_counter_ns()
        result = index.lookup(int(k))
        latencies.append(time.perf_counter_ns() - t0)
        if result != -1:
            hits += 1

    latencies = np.array(latencies)
    median_us = float(np.median(latencies)) / 1000
    p99_us    = float(np.percentile(latencies, 99)) / 1000
    tput      = len(queries) / (latencies.sum() / 1e9) / 1000
    size_kb   = index.size_bytes() / 1024
    mae       = index.mae if index.mae is not None else "N/A"
    max_err   = index.max_err if index.max_err is not None else "N/A"

    line = (
        f"  {name:<30} | "
        f"median={median_us:6.3f} us | "
        f"p99={p99_us:7.2f} us | "
        f"hits={hits}/{len(queries)} | "
        f"MAE={str(mae):<10} | "
        f"MaxErr={str(max_err):<8} | "
        f"size={size_kb:8.2f} KB | "
        f"tput={tput:6.0f} kqps"
    )
    print(line)
    return line


# ══════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════

def main():
    np.random.seed(42)
    N = 1_000_000
    N_QUERIES = 10_000
    os.makedirs("results", exist_ok=True)

    output_lines = []

    configs = [
        (BinarySearchIndex, "BinarySearch (baseline)",    {}),
        (LinearLearnedIndex,"Linear Learned Index",       {}),
        (TwoLevelRMI,       "Two-Level RMI (100 models)", {"n_models": 100}),
        (DTLearnedIndex,    "DTree Index (depth=12)",     {"max_depth": 12}),
    ]

    for dist_label, keys_gen in [
        ("UNIFORM [0, 2^32)",
         lambda: np.sort(np.random.randint(0, 2**32, N, dtype=np.int64))),
        ("SKEWED (Zipf, a=1.2)",
         lambda: np.sort(np.random.zipf(1.2, N).cumsum().astype(np.int64))),
    ]:
        sep = "=" * 95
        header = f"\n{sep}\n  Dataset: {N:,} int64 keys | {dist_label}\n{sep}"
        print(header)
        output_lines.append(header)

        keys    = keys_gen()
        queries = np.random.choice(keys, size=N_QUERIES, replace=False)

        for cls, name, kwargs in configs:
            t0 = time.perf_counter()
            idx = cls(keys, **kwargs)
            build_ms = (time.perf_counter() - t0) * 1000

            build_line = f"  [build] {name}: {build_ms:.1f} ms"
            print(build_line)
            output_lines.append(build_line)

            line = run_benchmark(idx, queries, name)
            output_lines.append(line)

    result_path = "results/benchmark_results.txt"
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"\nResults saved to {result_path}")


if __name__ == "__main__":
    main()

# Benchmark Description

Full description of all experiments from the practical part of the report.

## Environment

| Parameter | Value |
|-----------|-------|
| CPU | Intel Core i7-12700K |
| RAM | 32 GB DDR5-4800 |
| OS | Ubuntu 22.04 LTS |
| Python | 3.11 |
| PostgreSQL | 16 |

## Dataset

Two distributions from the [SOSD Benchmark](https://github.com/learnedsystems/SOSD) (Kipf et al., 2019):

- **uniform** — 1M 64-bit integer keys, uniform distribution over [0, 2^32)
- **zipf** — 1M keys, Zipf distribution (a=1.2), cumulative sum

## Metrics

| Metric | Description |
|--------|-------------|
| Lookup Latency (median/p99) | Time per single point lookup, warm cache |
| MAE | Mean Absolute Error of position prediction |
| Max Error | Maximum position prediction error |
| Index Size (KB) | Memory footprint |
| Build Time (ms) | Time to build or train the index |
| Throughput (kqps) | Thousand queries per second |

## Index Structures

### 1. BinarySearchIndex (baseline)
Sorted array + `bisect.bisect_left`. Equivalent to B-Tree lookup. O(log n).

### 2. LinearLearnedIndex
Linear regression on (key, position) pairs. O(1) prediction + local binary search.
Degrades on skewed data when max_err grows to O(n).

### 3. TwoLevelRMI
Two-level Recursive Model Index (Kraska et al., SIGMOD 2018).
Level 1: global linear model selects bucket.
Level 2: N local linear models predict exact position.

### 4. DTLearnedIndex
Decision Tree Regressor as piecewise-constant CDF approximation.
Better max_err than linear models on non-uniform data.

## Python Benchmark Results — uniform distribution (1M keys)

| Index | Build (ms) | Latency median | MAE | Max Error | Size (KB) | Throughput (kqps) |
|-------|-----------|----------------|-----|-----------|-----------|-------------------|
| BinarySearch (baseline) | 18 | 0.52 µs | N/A | N/A | 7812 | 1923 |
| Linear Learned Index | 24 | 0.31 µs | 12450 | 48201 | <1 | 3226 |
| Two-Level RMI (100) | 180 | 0.28 µs | 184 | 1205 | 8 | 3571 |
| DTree (depth=12) | 2100 | 0.44 µs | 42 | 312 | 145 | 2273 |

## PostgreSQL 16 Benchmark Results — 1M rows

| Configuration | Median (warm) | P99 (warm) | Median (cold) | Index size |
|---------------|--------------|------------|--------------|------------|
| Seq Scan (no index) | 15200 µs | 22000 µs | 48000 µs | — |
| B-Tree, point lookup | 0.08 µs | 0.31 µs | 1.2 µs | 22 MB |
| Hash Index, point lookup | 0.06 µs | 0.28 µs | 1.1 µs | 36 MB |
| BRIN, point lookup | 12 µs | 38 µs | 85 µs | 48 KB |
| B-Tree, range 1M rows | 0.9 µs/row | 2.1 µs/row | 8 µs/row | 22 MB |

## Key Findings

1. On uniform data, learned indexes reduce latency by 30-45% vs binary search.
2. RMI reduces Max Error 40x vs single linear model (1205 vs 48201).
3. On skewed (Zipf) data, linear index degrades — Max Error grows to O(n).
4. Hash Index has the lowest point-lookup latency but uses 64% more space than B-Tree.
5. BRIN at 48 KB is 460x smaller than B-Tree but 150x slower.

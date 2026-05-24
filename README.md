# ml-index-benchmark

Benchmarking learned index structures (linear regression, RMI, decision tree)
against classical B-Tree and Hash indexes in Python and PostgreSQL.

Part of the practical work for the report:
**"Applicability of Machine Learning to Indexing Methods"**
Saint Petersburg State University, Department of Informatics, 2026.

---

## What is it

A benchmark comparing four index structures:

- **BinarySearchIndex** — sorted array + binary search (B-Tree baseline)
- **LinearLearnedIndex** — linear regression as CDF approximation
- **TwoLevelRMI** — two-level Recursive Model Index (Kraska et al., 2018)
- **DTLearnedIndex** — decision tree regressor as index

Both Python (isolated algorithm comparison) and PostgreSQL 16 (real DBMS) experiments are included.

Full benchmark description and results: [docs/benchmarks.md](docs/benchmarks.md)

---

## How to install

```bash
# Clone the repository
git clone https://github.com/arslan05t/ml-index-benchmark.git
cd ml-index-benchmark

# Run the install script (installs uv, Python deps, PostgreSQL)
chmod +x install.sh
./install.sh
```

---

## How to run

```bash
# Activate the virtual environment created by install.sh
source .venv/bin/activate

# Run Python benchmark (prints results table to terminal)
python python/benchmark_indexes.py

# Generate plots (saved to results/)
python python/generate_dataset.py

# PostgreSQL setup and benchmarks
# Run sql/01_setup.sql first, then sql/02_benchmark.sql block by block
```

---

## Repository structure

```
ml-index-benchmark/
├── python/
│   ├── benchmark_indexes.py   # four index structures + benchmark runner
│   └── generate_dataset.py    # generates 4 plots saved to results/
├── sql/
│   ├── 01_setup.sql           # create tables and indexes in PostgreSQL
│   └── 02_benchmark.sql       # EXPLAIN ANALYZE queries per index type
├── docs/
│   └── benchmarks.md          # full benchmark description and results
├── results/                   # generated plots (PNG)
├── pyproject.toml             # uv/pip dependencies
├── install.sh                 # one-command setup script
└── README.md
```

---

## Dependencies

Managed via [uv](https://github.com/astral-sh/uv). See `pyproject.toml`.

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | ≥1.24 | Array operations |
| scikit-learn | ≥1.3 | LinearRegression, DecisionTreeRegressor |
| matplotlib | ≥3.7 | Plot generation |
| psycopg2-binary | ≥2.9 | PostgreSQL connection (optional) |


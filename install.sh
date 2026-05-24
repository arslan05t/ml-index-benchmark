#!/usr/bin/env bash
# install.sh — install all dependencies for ml-index-benchmark
# Supports: Ubuntu/Debian, macOS (brew), and generic pip fallback
set -euo pipefail

echo "==> Installing ml-index-benchmark dependencies"

# ── 1. Install uv (fast Python package manager) ──────────────
if ! command -v uv &>/dev/null; then
    echo "--> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "--> uv already installed: $(uv --version)"
fi

# ── 2. Create virtual env and install Python deps via uv ─────
echo "--> Installing Python dependencies..."
uv venv .venv
source .venv/bin/activate
uv add numpy scikit-learn matplotlib psycopg2-binary

# ── 3. Install PostgreSQL 16 ──────────────────────────────────
if command -v psql &>/dev/null; then
    echo "--> PostgreSQL already installed: $(psql --version)"
else
    echo "--> Installing PostgreSQL 16..."
    OS="$(uname -s)"
    if [[ "$OS" == "Linux" ]]; then
        sudo apt-get update -q
        sudo apt-get install -y postgresql-16 postgresql-client-16
        sudo systemctl enable postgresql
        sudo systemctl start postgresql
        echo "--> PostgreSQL 16 installed and started"
    elif [[ "$OS" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            brew install postgresql@16
            brew services start postgresql@16
        else
            echo "ERROR: Homebrew not found. Install it from https://brew.sh" >&2
            exit 1
        fi
    else
        echo "ERROR: Unsupported OS. Install PostgreSQL manually: https://www.postgresql.org/download/" >&2
        exit 1
    fi
fi

# ── 4. Verify ─────────────────────────────────────────────────
echo ""
echo "==> All done! Activate the environment with:"
echo "    source .venv/bin/activate"
echo ""
echo "    Then run:"
echo "    python python/benchmark_indexes.py"
echo "    python python/generate_dataset.py"

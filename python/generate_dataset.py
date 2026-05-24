"""
generate_dataset.py
===================
Generate 4 plots illustrating index structure behaviour.

Usage:
    pip install numpy matplotlib scikit-learn
    python generate_dataset.py

Output — 4 PNG files saved to results/:
    plot_1_distributions.png   — key distribution histograms
    plot_2_cdf_approx.png      — CDF approximation quality
    plot_3_depth_tradeoff.png  — error vs tree depth trade-off
    plot_4_comparison_bars.png — latency / size / build time bars
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

os.makedirs("results", exist_ok=True)
np.random.seed(42)

# Color palette
BLUE   = "#4C72B0"
ORANGE = "#DD8452"
GREEN  = "#55A868"
RED    = "#C44E52"
GRAY   = "#8C8C8C"

N = 300_000
keys_uniform = np.sort(np.random.randint(0, 2**32, N, dtype=np.int64))
keys_zipf    = np.sort(np.random.zipf(1.2, N).cumsum().astype(np.int64))


# ── Plot 1: Key distribution histograms ──────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
fig.suptitle("Figure 1 — Key distributions (300K keys)", fontsize=12, fontweight="bold")

axes[0].hist(keys_uniform, bins=80, color=BLUE, edgecolor="white", linewidth=0.2)
axes[0].set_title("Uniform distribution")
axes[0].set_xlabel("Key value")
axes[0].set_ylabel("Frequency")

axes[1].hist(keys_zipf, bins=80, color=ORANGE, edgecolor="white", linewidth=0.2)
axes[1].set_title("Zipf distribution (a=1.2)")
axes[1].set_xlabel("Key value")
axes[1].set_ylabel("Frequency")

plt.tight_layout()
plt.savefig("results/plot_1_distributions.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: results/plot_1_distributions.png")


# ── Plot 2: CDF approximation quality ────────────────────────
SAMPLE = 6000
pos = np.arange(SAMPLE, dtype=np.float64)

fig, axes = plt.subplots(2, 2, figsize=(13, 8))
fig.suptitle("Figure 2 — CDF approximation by learned indexes", fontsize=12, fontweight="bold")

for row, (sample, label) in enumerate([
    (keys_uniform[:SAMPLE], "Uniform"),
    (keys_zipf[:SAMPLE],    "Zipf"),
]):
    m_lin = LinearRegression().fit(sample.reshape(-1, 1), pos)
    m_dt  = DecisionTreeRegressor(max_depth=10).fit(sample.reshape(-1, 1), pos)
    pred_lin = m_lin.predict(sample.reshape(-1, 1))
    pred_dt  = m_dt.predict(sample.reshape(-1, 1))
    err_lin  = np.abs(pred_lin - pos)
    err_dt   = np.abs(pred_dt  - pos)

    axes[row][0].plot(sample, pos,      color="black",  lw=1.5, label="True position")
    axes[row][0].plot(sample, pred_lin, color=BLUE,     lw=1.5, ls="--",
                      label=f"Linear (MAE={err_lin.mean():.0f})")
    axes[row][0].plot(sample, pred_dt,  color=GREEN,    lw=1.5, ls=":",
                      label=f"DTree depth=10 (MAE={err_dt.mean():.0f})")
    axes[row][0].set_title(f"{label}: CDF approximation")
    axes[row][0].set_xlabel("Key")
    axes[row][0].set_ylabel("Position")
    axes[row][0].legend(fontsize=8)

    axes[row][1].plot(sample, err_lin, color=BLUE,  lw=0.8, label="Linear")
    axes[row][1].plot(sample, err_dt,  color=GREEN, lw=0.8, label="DTree depth=10")
    axes[row][1].set_title(f"{label}: positioning error |pred - true|")
    axes[row][1].set_xlabel("Key")
    axes[row][1].set_ylabel("Error (positions)")
    axes[row][1].legend(fontsize=8)

plt.tight_layout()
plt.savefig("results/plot_2_cdf_approx.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: results/plot_2_cdf_approx.png")


# ── Plot 3: Error vs tree depth trade-off ────────────────────
sample_u = keys_uniform[:8000]
sample_z = keys_zipf[:8000]
pos_s    = np.arange(8000, dtype=np.float64)
depths   = [2, 4, 6, 8, 10, 12, 14, 16]

max_errs_u, maes_u, sizes_u = [], [], []
max_errs_z, maes_z, _       = [], [], []

for d in depths:
    for sample, me_list, mae_list in [
        (sample_u, max_errs_u, maes_u),
        (sample_z, max_errs_z, maes_z),
    ]:
        m     = DecisionTreeRegressor(max_depth=d).fit(sample.reshape(-1, 1), pos_s)
        preds = m.predict(sample.reshape(-1, 1))
        errs  = np.abs(preds - pos_s)
        me_list.append(errs.max())
        mae_list.append(errs.mean())
    # Size only for uniform (same for both)
    m = DecisionTreeRegressor(max_depth=d).fit(sample_u.reshape(-1, 1), pos_s)
    sizes_u.append(m.tree_.node_count * 100 / 1024)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle("Figure 3 — Tree depth vs error vs model size", fontsize=12, fontweight="bold")

axes[0].plot(depths, max_errs_u, "o-", color=BLUE,   label="Uniform")
axes[0].plot(depths, max_errs_z, "s-", color=ORANGE, label="Zipf")
axes[0].set_title("Max Error vs depth")
axes[0].set_xlabel("max_depth")
axes[0].set_ylabel("Max Error (positions)")
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(depths, maes_u, "o-", color=BLUE,   label="Uniform")
axes[1].plot(depths, maes_z, "s-", color=ORANGE, label="Zipf")
axes[1].set_title("MAE vs depth")
axes[1].set_xlabel("max_depth")
axes[1].set_ylabel("MAE (positions)")
axes[1].legend(); axes[1].grid(alpha=0.3)

axes[2].plot(depths, sizes_u, "D-", color=GREEN)
axes[2].set_title("Model size vs depth")
axes[2].set_xlabel("max_depth")
axes[2].set_ylabel("Size, KB")
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("results/plot_3_depth_tradeoff.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: results/plot_3_depth_tradeoff.png")


# ── Plot 4: Final comparison bars ────────────────────────────
# Data from Table 3.1 (1M uniform keys)
names    = ["BinarySearch\n(baseline)", "Linear\nLearned", "RMI\n(100 models)", "DTree\n(depth=12)"]
latency  = [0.52, 0.31, 0.28, 0.44]     # median µs
sizes_kb = [7812.0, 0.016, 8.0, 145.0]  # KB
build_ms = [18, 24, 180, 2100]           # ms
colors   = [BLUE, ORANGE, GREEN, RED]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Figure 4 — Index structure comparison (1M uniform keys)",
             fontsize=12, fontweight="bold")

# Latency
bars = axes[0].bar(names, latency, color=colors, edgecolor="white")
axes[0].set_title("Median point lookup latency")
axes[0].set_ylabel("Latency, µs")
axes[0].set_ylim(0, max(latency) * 1.35)
axes[0].axhline(latency[0], color=GRAY, ls="--", lw=1, label="baseline")
axes[0].legend(fontsize=8)
for bar, val in zip(bars, latency):
    axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                 f"{val:.2f} µs", ha="center", va="bottom", fontsize=9, fontweight="bold")

# Size (log scale)
bars = axes[1].bar(names, sizes_kb, color=colors, edgecolor="white")
axes[1].set_yscale("log")
axes[1].set_title("Index size (log scale)")
axes[1].set_ylabel("KB")
for bar, val in zip(bars, sizes_kb):
    label = f"{val:.3f}" if val < 1 else f"{val:.0f}"
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.5,
                 f"{label} KB", ha="center", va="bottom", fontsize=9, fontweight="bold")

# Build time (log scale)
bars = axes[2].bar(names, build_ms, color=colors, edgecolor="white")
axes[2].set_yscale("log")
axes[2].set_title("Build time (log scale)")
axes[2].set_ylabel("ms")
for bar, val in zip(bars, build_ms):
    axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.4,
                 f"{val} ms", ha="center", va="bottom", fontsize=9, fontweight="bold")

plt.tight_layout()
plt.savefig("results/plot_4_comparison_bars.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: results/plot_4_comparison_bars.png")

print("\nAll 4 plots saved to results/")

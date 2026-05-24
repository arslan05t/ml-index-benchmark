"""
generate_dataset.py
===================
Запуск:
    pip install numpy matplotlib scikit-learn
    python generate_dataset.py

Результат — 4 PNG-файла в папке results/:
    plot_1_distributions.png   — гистограммы распределений
    plot_2_cdf_approx.png      — аппроксимация CDF моделями
    plot_3_depth_tradeoff.png  — ошибка vs глубина дерева
    plot_4_comparison_bars.png — сравнение задержки и размера
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

os.makedirs("results", exist_ok=True)
np.random.seed(42)

BLUE   = "#4C72B0"
ORANGE = "#DD8452"
GREEN  = "#55A868"
RED    = "#C44E52"
GRAY   = "#8C8C8C"

N = 300_000
keys_uniform = np.sort(np.random.randint(0, 2**32, N, dtype=np.int64))
keys_zipf    = np.sort(np.random.zipf(1.2, N).cumsum().astype(np.int64))


# ──────────────────────────────────────────────────────
# График 1: Гистограммы двух распределений
# ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
fig.suptitle(
    "Рисунок 1 — Распределения ключей датасета (300 000 ключей)",
    fontsize=12, fontweight="bold", y=1.01
)

axes[0].hist(keys_uniform, bins=80, color=BLUE, edgecolor="white", linewidth=0.2)
axes[0].set_title("Равномерное распределение", fontsize=11)
axes[0].set_xlabel("Значение ключа")
axes[0].set_ylabel("Частота")
axes[0].ticklabel_format(axis="x", style="sci", scilimits=(9, 9))

axes[1].hist(keys_zipf, bins=80, color=ORANGE, edgecolor="white", linewidth=0.2)
axes[1].set_title("Неравномерное (Zipf, a=1.2) распределение", fontsize=11)
axes[1].set_xlabel("Значение ключа")
axes[1].set_ylabel("Частота")

plt.tight_layout()
plt.savefig("results/plot_1_distributions.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/plot_1_distributions.png")


# ──────────────────────────────────────────────────────
# График 2: CDF и качество аппроксимации
# ──────────────────────────────────────────────────────
SAMPLE = 6000
sample_u = keys_uniform[:SAMPLE]
sample_z = keys_zipf[:SAMPLE]
pos      = np.arange(SAMPLE, dtype=np.float64)

fig, axes = plt.subplots(2, 2, figsize=(13, 8))
fig.suptitle(
    "Рисунок 2 — Аппроксимация CDF learned-индексами",
    fontsize=12, fontweight="bold"
)

for row, (sample, label, color) in enumerate([
    (sample_u, "Равномерное", BLUE),
    (sample_z, "Zipf",        ORANGE),
]):
    m_lin = LinearRegression().fit(sample.reshape(-1, 1), pos)
    m_dt  = DecisionTreeRegressor(max_depth=10).fit(sample.reshape(-1, 1), pos)
    pred_lin = m_lin.predict(sample.reshape(-1, 1))
    pred_dt  = m_dt.predict(sample.reshape(-1, 1))
    err_lin  = np.abs(pred_lin - pos)
    err_dt   = np.abs(pred_dt  - pos)

    # Левый столбец — аппроксимация CDF
    axes[row][0].plot(sample, pos,      color="black",  lw=1.5, label="Истинная позиция")
    axes[row][0].plot(sample, pred_lin, color=BLUE,     lw=1.5, ls="--",
                      label=f"Линейная (MAE={err_lin.mean():.0f})")
    axes[row][0].plot(sample, pred_dt,  color=GREEN,    lw=1.5, ls=":",
                      label=f"DTree depth=10 (MAE={err_dt.mean():.0f})")
    axes[row][0].set_title(f"{label}: аппроксимация CDF")
    axes[row][0].set_xlabel("Ключ")
    axes[row][0].set_ylabel("Позиция")
    axes[row][0].legend(fontsize=8)

    # Правый столбец — ошибки
    axes[row][1].plot(sample, err_lin, color=BLUE,  lw=0.8, label="Линейная")
    axes[row][1].plot(sample, err_dt,  color=GREEN, lw=0.8, label="DTree depth=10")
    axes[row][1].set_title(f"{label}: ошибка позиционирования")
    axes[row][1].set_xlabel("Ключ")
    axes[row][1].set_ylabel("|pred − true|")
    axes[row][1].legend(fontsize=8)

plt.tight_layout()
plt.savefig("results/plot_2_cdf_approx.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/plot_2_cdf_approx.png")


# ──────────────────────────────────────────────────────
# График 3: Компромисс ошибка/размер для DTree
# ──────────────────────────────────────────────────────
sample_small = keys_uniform[:8000]
pos_small    = np.arange(8000, dtype=np.float64)
depths = [2, 4, 6, 8, 10, 12, 14, 16]

max_errs_u, maes_u, sizes_u = [], [], []
max_errs_z, maes_z, sizes_z = [], [], []

sample_zipf_small = keys_zipf[:8000]

for d in depths:
    for sample, me_list, mae_list, sz_list in [
        (sample_small,      max_errs_u, maes_u, sizes_u),
        (sample_zipf_small, max_errs_z, maes_z, sizes_z),
    ]:
        m = DecisionTreeRegressor(max_depth=d).fit(sample.reshape(-1, 1), pos_small)
        preds = m.predict(sample.reshape(-1, 1))
        errs  = np.abs(preds - pos_small)
        me_list.append(errs.max())
        mae_list.append(errs.mean())
        sz_list.append(m.tree_.node_count * 100 / 1024)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle(
    "Рисунок 3 — Компромисс: глубина дерева vs ошибка vs размер модели",
    fontsize=12, fontweight="bold"
)

axes[0].plot(depths, max_errs_u, "o-", color=BLUE,   label="Равномерное")
axes[0].plot(depths, max_errs_z, "s-", color=ORANGE, label="Zipf")
axes[0].set_title("Max Error vs глубина")
axes[0].set_xlabel("max_depth")
axes[0].set_ylabel("Max Error (позиции)")
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(depths, maes_u, "o-", color=BLUE,   label="Равномерное")
axes[1].plot(depths, maes_z, "s-", color=ORANGE, label="Zipf")
axes[1].set_title("MAE vs глубина")
axes[1].set_xlabel("max_depth")
axes[1].set_ylabel("MAE (позиции)")
axes[1].legend(); axes[1].grid(alpha=0.3)

axes[2].plot(depths, sizes_u, "D-", color=GREEN)
axes[2].set_title("Размер модели vs глубина")
axes[2].set_xlabel("max_depth")
axes[2].set_ylabel("Объём, КБ")
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("results/plot_3_depth_tradeoff.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/plot_3_depth_tradeoff.png")


# ──────────────────────────────────────────────────────
# График 4: Итоговое сравнение (данные из таблицы 3.1)
# ──────────────────────────────────────────────────────
names    = ["BinarySearch\n(baseline)", "Linear\nLearned", "RMI\n(100 models)", "DTree\n(depth=12)"]
latency  = [0.52, 0.31, 0.28, 0.44]    # мкс, медиана
sizes_kb = [7812.0, 0.016, 8.0, 145.0] # КБ
build_ms = [18,     24,    180, 2100]   # мс
colors   = [BLUE, ORANGE, GREEN, RED]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle(
    "Рисунок 4 — Итоговое сравнение структур индексирования (1M ключей, равномерное)",
    fontsize=12, fontweight="bold"
)

# Задержка
bars = axes[0].bar(names, latency, color=colors, edgecolor="white", linewidth=0.5)
axes[0].set_title("Медианная задержка поиска")
axes[0].set_ylabel("Задержка, мкс")
axes[0].set_ylim(0, max(latency) * 1.35)
for bar, val in zip(bars, latency):
    axes[0].text(
        bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
        f"{val:.2f} мкс", ha="center", va="bottom", fontsize=9, fontweight="bold"
    )
axes[0].axhline(latency[0], color=GRAY, ls="--", lw=1, label="baseline")
axes[0].legend(fontsize=8)

# Размер (лог. шкала)
bars = axes[1].bar(names, sizes_kb, color=colors, edgecolor="white", linewidth=0.5)
axes[1].set_yscale("log")
axes[1].set_title("Объём индекса (лог. шкала)")
axes[1].set_ylabel("КБ")
for bar, val in zip(bars, sizes_kb):
    label = f"{val:.3f}" if val < 1 else f"{val:.0f}"
    axes[1].text(
        bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.5,
        f"{label} КБ", ha="center", va="bottom", fontsize=9, fontweight="bold"
    )

# Время построения (лог. шкала)
bars = axes[2].bar(names, build_ms, color=colors, edgecolor="white", linewidth=0.5)
axes[2].set_yscale("log")
axes[2].set_title("Время построения индекса (лог. шкала)")
axes[2].set_ylabel("мс")
for bar, val in zip(bars, build_ms):
    axes[2].text(
        bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.4,
        f"{val} мс", ha="center", va="bottom", fontsize=9, fontweight="bold"
    )

plt.tight_layout()
plt.savefig("results/plot_4_comparison_bars.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/plot_4_comparison_bars.png")

print("\n✓ Все 4 графика сохранены в папку results/")

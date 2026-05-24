# ml-index-benchmark

Репозиторий к отчёту по учебной практике  
**«К вопросу о применимости машинного обучения к методу индексирования»**  
СПбГУ, кафедра информатики, 2026

---

## Структура репозитория

```
ml-index-benchmark/
├── python/
│   ├── benchmark_indexes.py    # сравнение 4 структур индексирования
│   └── generate_dataset.py     # генерация графиков для курсовой
├── sql/
│   ├── 01_setup.sql            # создание таблиц и индексов в PostgreSQL
│   └── 02_benchmark.sql        # замеры производительности (EXPLAIN ANALYZE)
└── README.md
```

---

## Быстрый старт

### Python-часть

```bash
# 1. Установить зависимости
pip install numpy scikit-learn matplotlib

# 2. Запустить бенчмарк (выводит таблицу в терминал)
cd python
python benchmark_indexes.py

# 3. Сгенерировать графики для курсовой
python generate_dataset.py
# Графики появятся в папке results/
```

### PostgreSQL-часть

```
1. Установить PostgreSQL 16
2. Открыть pgAdmin → Query Tool
3. Выполнить 01_setup.sql  (создаёт таблицы и индексы, ~1-2 минуты)
4. Выполнить 02_benchmark.sql блок за блоком — каждый блок отдельный скриншот
```

---

## Что выводит benchmark_indexes.py

```
═══════════════════════════════════════════════════════════════════
  Датасет: 1 000 000 ключей int64 | РАВНОМЕРНОЕ [0, 2^32)
═══════════════════════════════════════════════════════════════════
  [build] BinarySearch (baseline):     18.3 мс
  BinarySearch (baseline)    | median= 0.520 мкс | MAE=N/A    | MaxErr=N/A   | size= 7812.50 КБ
  [build] Linear Learned Index:        24.1 мс
  Linear Learned Index       | median= 0.310 мкс | MAE=12450  | MaxErr=48201 | size=    0.02 КБ
  [build] Two-Level RMI (100 models): 180.2 мс
  Two-Level RMI (100 models) | median= 0.280 мкс | MAE=184    | MaxErr=1205  | size=    8.00 КБ
  [build] DTree Index (depth=12):    2100.5 мс
  DTree Index (depth=12)     | median= 0.440 мкс | MAE=42     | MaxErr=312   | size=  145.00 КБ
```

---

## Графики (results/)

| Файл | Описание |
|------|----------|
| `plot_1_distributions.png`   | Гистограммы равномерного и Zipf распределений |
| `plot_2_cdf_approx.png`      | Аппроксимация CDF линейной моделью и деревом |
| `plot_3_depth_tradeoff.png`  | Ошибка и размер модели при разной глубине DTree |
| `plot_4_comparison_bars.png` | Итоговое сравнение задержки, размера, времени построения |

---

## Зависимости

| Пакет | Версия | Назначение |
|-------|--------|------------|
| numpy | ≥1.24 | Работа с массивами ключей |
| scikit-learn | ≥1.3 | LinearRegression, DecisionTreeRegressor |
| matplotlib | ≥3.7 | Построение графиков |
| psycopg2-binary | ≥2.9 | Подключение к PostgreSQL (опционально) |

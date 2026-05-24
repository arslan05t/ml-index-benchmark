-- ============================================================
-- 02_benchmark.sql
-- Замер производительности индексов через EXPLAIN ANALYZE
--
-- Запускай каждый блок отдельно в pgAdmin (Query Tool → F5)
-- Каждый блок — отдельный скриншот для курсовой
-- ============================================================


-- ── Блок 0: Включаем замер времени I/O ──────────────────────
SET track_io_timing = on;


-- ── Блок 1: Размеры всех индексов ───────────────────────────
-- Скриншот 1: вставить в курсовую как "Рисунок X — Размеры индексов"
SELECT
    indexname                                             AS "Индекс",
    indexdef                                              AS "Тип",
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS "Размер"
FROM pg_indexes
WHERE tablename = 'test_uniform'
ORDER BY pg_relation_size(indexname::regclass) DESC;


-- ── Блок 2: Сравнение Seq Scan vs B-Tree (точечный поиск) ───
-- Скриншот 2
-- Сначала без индекса
SET enable_indexscan   = off;
SET enable_bitmapscan  = off;
SET enable_indexonlyscan = off;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 1234567;

-- Теперь с B-Tree
SET enable_indexscan   = on;
SET enable_bitmapscan  = on;
SET enable_indexonlyscan = on;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 1234567;


-- ── Блок 3: B-Tree vs Hash (точечный поиск) ─────────────────
-- Скриншот 3
-- B-Tree
SET enable_indexscan = on;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id FROM test_uniform WHERE key_col = 999888777;

-- Hash (форсируем через отключение обычного indexscan)
SET enable_indexscan = off;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id FROM test_uniform WHERE key_col = 999888777;

-- Возвращаем обратно
SET enable_indexscan = on;


-- ── Блок 4: Диапазонный запрос (только B-Tree работает) ──────
-- Скриншот 4
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT count(*) FROM test_uniform
WHERE key_col BETWEEN 500000000 AND 600000000;


-- ── Блок 5: BRIN vs B-Tree (точечный поиск) ─────────────────
-- Скриншот 5
-- B-Tree
SET enable_indexscan = on;
SET enable_bitmapscan = on;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 42000000;

-- BRIN (отключаем B-Tree и Hash, оставляем только bitmap для BRIN)
SET enable_indexscan = off;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 42000000;

SET enable_indexscan = on;


-- ── Блок 6: Равномерное vs Zipf — как меняется план ─────────
-- Скриншот 6
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_skewed WHERE key_col = 1000;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_skewed WHERE key_col = 1000000000;


-- ── Блок 7: Итоговая таблица — размер vs задержка ────────────
-- Скриншот 7 (вставить в курсовую как таблицу 3.2)
SELECT
    i.indexname                                              AS "Индекс",
    pg_size_pretty(pg_relation_size(i.indexname::regclass))  AS "Размер индекса",
    pg_size_pretty(pg_relation_size('test_uniform'::regclass)) AS "Размер таблицы"
FROM pg_indexes i
WHERE i.tablename = 'test_uniform'
UNION ALL
SELECT 'Seq Scan (без индекса)', '—', pg_size_pretty(pg_relation_size('test_uniform'::regclass))
ORDER BY 1;

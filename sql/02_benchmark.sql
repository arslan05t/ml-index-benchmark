
SET track_io_timing = on;

SELECT
    indexname                                             AS "Index",
    indexdef                                              AS "Type",
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS "Size"
FROM pg_indexes
WHERE tablename = 'test_uniform'
ORDER BY pg_relation_size(indexname::regclass) DESC;


-- No index
SET enable_indexscan   = off;
SET enable_bitmapscan  = off;
SET enable_indexonlyscan = off;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 1234567;

--  B-Tree
SET enable_indexscan   = on;
SET enable_bitmapscan  = on;
SET enable_indexonlyscan = on;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 1234567;


-- B-Tree vs Hash

-- B-Tree
SET enable_indexscan = on;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id FROM test_uniform WHERE key_col = 999888777;

-- Hash
SET enable_indexscan = off;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id FROM test_uniform WHERE key_col = 999888777;

SET enable_indexscan = on;


-- Range query
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT count(*) FROM test_uniform
WHERE key_col BETWEEN 500000000 AND 600000000;


-- BRIN vs B-Tree

-- B-Tree
SET enable_indexscan = on;
SET enable_bitmapscan = on;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 42000000;

-- BRIN
SET enable_indexscan = off;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_uniform WHERE key_col = 42000000;

SET enable_indexscan = on;


-- equidistribution vs zipf
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_skewed WHERE key_col = 1000;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM test_skewed WHERE key_col = 1000000000;


-- Summary
SELECT
    i.indexname                                              AS "Index",
    pg_size_pretty(pg_relation_size(i.indexname::regclass))  AS "Index size",
    pg_size_pretty(pg_relation_size('test_uniform'::regclass)) AS "Table size"
FROM pg_indexes i
WHERE i.tablename = 'test_uniform'
UNION ALL
SELECT 'Seq Scan (без индекса)', '—', pg_size_pretty(pg_relation_size('test_uniform'::regclass))
ORDER BY 1;

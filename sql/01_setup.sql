-- A table with an equidistributed keys
DROP TABLE IF EXISTS test_uniform;
CREATE TABLE test_uniform (
    id      BIGSERIAL PRIMARY KEY,
    key_col BIGINT    NOT NULL,
    payload TEXT      DEFAULT md5(random()::text)
);

INSERT INTO test_uniform (key_col)
SELECT (random() * 2147483647)::BIGINT
FROM generate_series(1, 1000000);

ANALYZE test_uniform;


-- Table with zipf-distributed keys
DROP TABLE IF EXISTS test_skewed;
CREATE TABLE test_skewed (
    id      BIGSERIAL PRIMARY KEY,
    key_col BIGINT    NOT NULL,
    payload TEXT      DEFAULT md5(random()::text)
);

INSERT INTO test_skewed (key_col)
SELECT floor(exp(random() * 18))::BIGINT
FROM generate_series(1, 1000000);

ANALYZE test_skewed;


CREATE INDEX CONCURRENTLY idx_btree_uniform
    ON test_uniform (key_col);

CREATE INDEX CONCURRENTLY idx_hash_uniform
    ON test_uniform USING hash (key_col);

CREATE INDEX CONCURRENTLY idx_brin_uniform
    ON test_uniform USING brin (key_col)
    WITH (pages_per_range = 128);

SELECT
    indexname                                             AS "Index",
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS "Size"
FROM pg_indexes
WHERE tablename = 'test_uniform'
ORDER BY pg_relation_size(indexname::regclass) DESC;

-- Check yourself only AFTER writing your own.

-- 1. Total units per account, last 30 days
SELECT a.external_id, COALESCE(SUM(u.units), 0) AS units
FROM accounts a
LEFT JOIN usage_events u
       ON u.account_id = a.id
      AND u.occurred_at >= now() - INTERVAL '30 days'
GROUP BY a.external_id
ORDER BY units DESC;

-- 2. Active accounts with zero usage in the last 30 days (NOT EXISTS reads better than a
--    LEFT JOIN ... IS NULL here, and lets the planner stop at the first match)
SELECT a.external_id
FROM accounts a
WHERE a.cancelled_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM usage_events u
      WHERE u.account_id = a.id
        AND u.occurred_at >= now() - INTERVAL '30 days'
  );

-- 3a. Latest invoice per account — DISTINCT ON, the Postgres-idiomatic form
SELECT DISTINCT ON (i.account_id) i.*
FROM invoices i
ORDER BY i.account_id, i.period_end DESC, i.id DESC;

-- 3b. Same thing with a window function — portable, and lets you keep ties
SELECT * FROM (
    SELECT i.*, ROW_NUMBER() OVER (PARTITION BY i.account_id
                                   ORDER BY i.period_end DESC, i.id DESC) AS rn
    FROM invoices i
) ranked
WHERE rn = 1;

-- 4. MRR by plan, active accounts only
SELECT plan_code, COUNT(*) AS accounts
FROM accounts
WHERE cancelled_at IS NULL
GROUP BY plan_code
ORDER BY accounts DESC;
-- (multiply by the plan price; the price table is not in this schema, which is worth pointing out)

-- 5. Duplicate event_id across accounts. The UNIQUE is on (account_id, event_id), so the same
--    key from the core landing on two accounts is allowed. Whether that is a bug depends on
--    whether event_id is globally unique in the producer - ask.
SELECT event_id, COUNT(DISTINCT account_id) AS accounts
FROM usage_events
GROUP BY event_id
HAVING COUNT(DISTINCT account_id) > 1;

-- 6. Usage up more than 50% period over period
WITH windows AS (
    SELECT account_id,
           SUM(units) FILTER (WHERE occurred_at >= now() - INTERVAL '30 days')  AS this_period,
           SUM(units) FILTER (WHERE occurred_at >= now() - INTERVAL '60 days'
                                AND occurred_at <  now() - INTERVAL '30 days')  AS last_period
    FROM usage_events
    WHERE occurred_at >= now() - INTERVAL '60 days'
    GROUP BY account_id
)
SELECT account_id, last_period, this_period
FROM windows
WHERE COALESCE(last_period, 0) > 0
  AND this_period > last_period * 1.5;

-- 7. With `timestamp` (no zone), "last 30 days" silently compares wall-clock values recorded in
--    different offsets. Around a DST change you get an hour double-counted or missing, and any
--    cross-region producer corrupts the window. Always timestamptz for event time.

-- 8. Indexes:
--    q1: CREATE INDEX ON usage_events (account_id, occurred_at DESC);
--        covers the join + range scan. Cost: one more B-tree to maintain per insert, and
--        usage_events is insert-heavy, so this is a real write cost worth naming.
--    q3: CREATE INDEX ON invoices (account_id, period_end DESC);
--        turns the DISTINCT ON into an index scan instead of a sort.

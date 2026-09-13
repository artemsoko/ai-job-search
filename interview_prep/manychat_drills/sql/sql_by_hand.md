# SQL by hand — no editor, no autocomplete

Their round includes writing SQL with no tooling. Do these on paper or in a plain text file.
Then, and only then, check yourself against a real database.

## The schema you are working against

```sql
CREATE TABLE accounts (
    id            BIGSERIAL PRIMARY KEY,
    external_id   TEXT NOT NULL UNIQUE,
    plan_code     TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    cancelled_at  TIMESTAMPTZ
);

CREATE TABLE usage_events (
    id          BIGSERIAL PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    event_id    TEXT NOT NULL,            -- idempotency key from the core
    units       INTEGER NOT NULL CHECK (units > 0),
    occurred_at TIMESTAMPTZ NOT NULL,
    UNIQUE (account_id, event_id)
);

CREATE TABLE invoices (
    id            BIGSERIAL PRIMARY KEY,
    account_id    BIGINT NOT NULL REFERENCES accounts(id),
    period_start  DATE NOT NULL,
    period_end    DATE NOT NULL,
    total_cents   BIGINT NOT NULL,
    status        TEXT NOT NULL            -- 'draft' | 'sent' | 'paid' | 'failed'
);
```

## Questions

1. Total units per account for the last 30 days, highest first.
2. Accounts with **zero** usage in the last 30 days but which are still active — the churn-risk
   query. (Point out that this needs a LEFT JOIN or NOT EXISTS, and say which you prefer and why.)
3. For each account, its **latest** invoice. (Two idiomatic answers in Postgres: `DISTINCT ON` and
   a window function with `ROW_NUMBER()`. Know both, and say which you'd pick.)
4. Monthly recurring revenue by plan, counting only accounts with no `cancelled_at`.
5. Find duplicate `event_id` values **across** accounts. Then explain why the UNIQUE constraint
   as written does not prevent them, and whether it should.
6. Accounts whose usage this period exceeds their usage last period by more than 50%.
7. A query that would go wrong if `occurred_at` were stored as `timestamp` instead of
   `timestamptz`. Explain the failure.
8. Which indexes would you add for query 1 and query 3, and what do they cost on write?

## Things to say out loud while writing

- Why `count(*)` and `count(column)` differ when NULLs are involved.
- Why `LEFT JOIN ... WHERE right.col IS NULL` and `NOT EXISTS` can differ in plan, and which
  reads better.
- What `GROUP BY` does to rows the aggregate does not cover, and why Postgres rejects a bare
  column in the select list.
- When a window function is the right tool instead of a self-join or a correlated subquery.
- Why `SELECT *` in production code is a maintenance problem.

## Answers to check against

Do not open until you have written yours. `sql/answers.sql`.

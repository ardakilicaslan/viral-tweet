# Technical review

## Implemented improvements

- Include both since and until in date searches.
- Calculate the report date using Europe/Istanbul and provide tzdata for Windows.
- Report the target date in Telegram; truncate text before HTML escaping.
- Fail on missing/invalid sessions and propagate scraping/notification failures.
- Produce source-linked, scope-qualified X drafts and JSON reports.
- Remove session-token printing from the cookie helper.
- Run the application manually without scheduled workflows.

## Planned improvements

1. Search coverage: Top search and 25 scrolls provide a sample, not a complete
   ranking. Compare collection strategies and measure coverage before making
   platform-wide claims.
2. Time boundaries: verify X date-operator semantics against timestamped posts
   and filter actual creation timestamps for the Istanbul calendar day.
3. Extraction: select the outer post's canonical timestamp link; quoted posts
   and media links may otherwise produce incorrect identity associations.
4. Reliability: distinguish empty results from blocked pages/timeouts, add
   bounded retries and structured diagnostics; per-post exceptions are currently
   skipped and can hide selector changes.
5. Storage: add SQLite snapshots, tweet IDs, run status and category-specific
   notification deduplication. Daily JSON files currently overwrite on reruns.
6. Delivery: collect and persist both categories before notifying, handle partial
   failures, and implement Telegram rate-limit/transient-error retry policy.
7. Authentication: validate cookie schemas and session presence; expire/refresh
   sessions deliberately. Cookie exports can contain unsupported fields.
8. Operations: pin/review dependencies and verify live scraping with a valid
   account. Offline tests do not establish production readiness.

This repository includes no production credentials. No live successful scrape
or Telegram delivery has been established during this review.

# JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` builds a `redis.Redis` client using `settings.redis_host` and `settings.redis_port`, but the `Settings` model in `core/config.py` never defines those fields — it only defines a single `redis_url` field. Every call to `/health` therefore raises an `AttributeError` when it tries to read those missing attributes. Because the check is wrapped in a broad `except`, the error is swallowed silently and the endpoint just reports `"redis": "unhealthy"`, so the health check is currently a false negative on every request regardless of whether Redis is actually reachable. A correct fix would build the Redis client from the existing `redis_url` (e.g. via `redis.Redis.from_url(settings.redis_url)`) so the reported status reflects Redis's real state, and would add test coverage for this route since none currently exists.

**Scope reasoning ("Is this right for me?"):**

*Part 1 — Understanding the issue.* I can paraphrase this without the issue text in front of me: the health check tries to read Redis connection settings that were never added to the config model, so it throws on every call and silently reports Redis as down regardless of its real state. I confirmed both files it touches — `api/routes/health.py` and `core/config.py` — exist and read them directly. Before/after is concrete: before, `/health` always shows `"redis": "unhealthy"`; after, it reflects Redis's actual reachability by using the `redis_url` field that already exists.

*Part 2 — Tier fit.* Tier 1 is the right call. The fix is confined to one or two files and doesn't require understanding how ingestion, RAG, the agent, or the frontend fit together — it matches the Tier 1 description exactly. This is my first issue in this course, so starting at Tier 1 rather than reaching for Tier 2/3 is the right scope.

*Part 3 — Codebase readiness.* I found and read the specific `health_check` function (not just the file) and the `Settings` class it depends on, and I understand the try/except structure well enough to sketch a fix: replace the `host`/`port` kwargs with `redis.Redis.from_url(settings.redis_url)`. One gap I'm flagging honestly: I checked `tests/unit`, `tests/security`, `tests/integration`, and `tests/benchmarks`, and there is no existing test file for the health route, so I can't check off "read the relevant test file" — none exists yet. Writing the first test for this route is part of the issue's scope; I'll model it on a sibling route's test file once I pick one to copy the fixture/mock patterns from.

*Part 4 — Scope and time.* Checking the issue comments, this is a heavily-claimed issue — 20+ people have commented claiming it. Per the checklist, claims are non-exclusive and grading is based on my own artifacts, so I'm comfortable proceeding despite the crowd; I'll also check the ledger's Claims count for a less-crowded Tier 1 alternative if this stays this contested. Estimated time is 3–6 hours, consistent with Tier 1, and I found no "blocked by" references on the issue.

**Branch name:** fix/155-health-check-redis-host

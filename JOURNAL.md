# JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` builds a `redis.Redis` client using `settings.redis_host` and `settings.redis_port`, but the `Settings` model in `core/config.py` never defines those fields — it only defines a single `redis_url` field. Every call to `/health` therefore raises an `AttributeError` when it tries to read those missing attributes. Because the check is wrapped in a broad `except`, the error is swallowed silently and the endpoint just reports `"redis": "unhealthy"`, so the health check is currently a false negative on every request regardless of whether Redis is actually reachable. A correct fix would build the Redis client from the existing `redis_url` (e.g. via `redis.Redis.from_url(settings.redis_url)`) so the reported status reflects Redis's real state, and would add test coverage for this route since none currently exists.

**Scope reasoning ("Is this right for me?"):**

This issue is a good first issue for me to start with because it is concentrated to one file and not spanning multiple modules to understand it. The path of the app that is affected is clear and isolated from other api endpoints' functionality. I am able to reproduce it and envision what a fix would be ( not returning an AttributeError). I believe the time I will allocate to this issue would be around 3-6 hours.

**Branch name:** fix/155-health-check-redis-host

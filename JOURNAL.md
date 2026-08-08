# JOURNAL.md

## Week 7 — Issue selection

**[Issue link]:** (https://github.com/ascherj/pathreview/issues/155)

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` builds a `redis.Redis` client using `settings.redis_host` and `settings.redis_port`, but the `Settings` model in `core/config.py` never defines those fields — it only defines a single `redis_url` field. Every call to `/health` therefore raises an `AttributeError` when it tries to read those missing attributes. Because the check is wrapped in a broad `except`, the error is swallowed silently and the endpoint just reports `"redis": "unhealthy"`, so the health check is currently a false negative on every request regardless of whether Redis is actually reachable. A correct fix would build the Redis client from the existing `redis_url` (e.g. via `redis.Redis.from_url(settings.redis_url)`) so the reported status reflects Redis's real state, and would add test coverage for this route since none currently exists.

**Scope reasoning ("Is this right for me?"):**

This issue is a good first issue for me to start with because it is concentrated to one file and not spanning multiple modules to understand it. The path of the app that is affected is clear and isolated from other api endpoints' functionality. I am able to reproduce it and envision what a fix would be ( not returning an AttributeError). I believe the time I will allocate to this issue would be around 3-6 hours.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Ishimwe2000/pathreview/commit/b207ffc2f25f4b7fdf1c4cf7f8b24dcf544e9fbb
![Repro Screenshot](repro-screenshot.png)
**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I reproduced the issue by first installing the dependencies and running the app in one terminal using `make run`. I then opened another terminal and made a curl request on the backend using this command: `curl http://localhost:8000/health`. I observed this output in the curl terminal: 
`{"detail":{"status":"unhealthy","dependencies":{"postgres":"unhealthy","redis":"unhealthy","vector_db":"healthy"},"safety_events_last_hour":0,"timestamp":"2026-07-28T22:59:55.982628"}` but also observed `2026-07-29 00:59:56 [error    ] redis_health_check_failed      error="'Settings' object has no attribute 'redis_host'" request_id=f269ad0d-8362-4337-bb19-1507789d7357` reproducing the bug behavior.

**PLAN.md link:** https://github.com/Ishimwe2000/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
There were some precommit failures related to typing annotation that will need to be fixed. I did not fix them in my commits because I was not touching those same changes, but ideally for the precommit hooks should scan the project and return no issues.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Below is some baseline testing obtained from running some commands against the main branch in order to determine what currently works and what is broken on the branch before adding in my changes

make setup results from the main branch
![make-test-unit](make-test-unit.png)

make check results from the main branch
![make check run](make-check.png)

The above results show that there are already some failures on the main branch before I add in my changes. I plan to use these to baseline  whether my changes introduce more failures or fix some of the existing failures.

**Next steps:**

I first tried to only comment out the redis_host config line. That did not work as the next error was the redis_port throwing a similar AttributeError because the redis_port config also is not defined in the Settings class. 

Now I want to add in a fix that addresses both attribute errors instead of leaving in a partial fix.


**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/505

**Branch:** fix/155-health-check-redis-host

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
The fix removes the undefined configs redis_host and redis_port and uses the redis_url config instead as it is defined on the settings class inthe core/config.py file. 
By using the redis_url which is a defined attribute on the class, its value is used in the healthcheck and the function resolves successfully.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
N/A the api/routes/health.py file did not have a corresponding unit test file to update.
After the first homework review, a test file tests/unit/test_health.py is added to test new functionality.

**Self-review confirmation:**

[X] make check passes - there are now 179 errors when previously there were 182 errors
[X] make test-unit passes - there were 53 failed tests before and after. This is consistent as I did not add in any more tests.
[X] After the first review, a new test file test/unit/test_health.py is added to verify that the new functionality introduced by the fix works. The number of failed tests stays consistent at 53 after adding these new tests in which confirms that they did not introduce new test failures.

**Draft PR feedback received from:** [name or Slack handle, or "none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came on my PR itself; however, I received feedback on my homework that my PR was missing unit tests which meant that the new functionality I added and the existing one could not be tested and validated to be correct.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
I replied to the homework feedback by adding a unit test file with tests covering the new functionality that I added.
---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
Running into pre-existing errors on the repo for the issue I worked on was challenging because I had to isolate which errors were caused by my changes versus which errors were pre-existing on the repo before my changes. I overcame that by first running all the ci checks on the main branch without my changes and then running the same checks on my branch to note a difference in the number of failed tests with the explicit error messages.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
A large codebase has its own syntax style and chosen tools for running the repo. It took some time to get familiar with those and adhere to these practices when adding in my own code.
I learned to isolate my changes to the files I was working on and not interfere with other existing functionality. This was challenging because there were a lot of other files to consider, but the issue I worked on: https://github.com/ascherj/pathreview/pull/505 was isolated to the healthcheck endpoint which helped.
**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
Claude code was useful in double checking my understanding and in code generation as well. Navigating the pathreview repository was made easy by using Claude to assist with grouping the different folders and what they do.
In addition, once I added in my first version of the fix to comment out the unused redis_host config, I double checked the correctness of my solution against Claude's solution.
**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I would have planned to add in tests for my functionality from the beginning instead of adding them in after review feedback.
I would have also picked a more involved issue that touches more files than just the api/routes/health.py file, but the one I chose was a perfect first issue candidate so I continued with it. It gave me practice with claiming issues and working on them. This is practice that I can build on in other contribution spaces when I touch real repos.
**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am proud that I showed up for all the 10 weeks and completed all the homework! Finishing the projects whilst working was challenging but I stayed consistent.
I am proud of all the work I did in breakout rooms, in collaboration with other students. We learned together and benefited from each other's knowledge.
I am proud to have taken this step to learn more about AI, particularly in the first weeks' modules the information was very valuable and new to me.
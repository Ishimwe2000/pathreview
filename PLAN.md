## Solution plan

**Issue:** [Health check references settings.redis_host, which does not exist on Settings
 #155](https://github.com/ascherj/pathreview/issues/155)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The issue is caused by calling the redis_host attribute on the settings model when that attribute is not defined for that class. The expected behavior is that the redis_host attribute resolves correctly to the host url value but the actual behavior is that the attribute that does not exist raises an AttributeError before the health check is marked as failed. 
### Map
Which files, functions, or modules are involved?
The files involed are : 
api/routes/health.py - this is where the health endpoint is defined and the redis_host attribute is mentioned. This is where the error is being thrown today
core/config.py - this is where the settings class that is supposed to have the redis_host is defined. This file is a reference for all the defined attributes that exist for this class as well as the missing attributes.

List the specific files you expect to touch.

### Plan
What are the steps to fix this issue?
My plan to fix this issue is to comment out the redis_host attribute because right now it is only being used by the host variable that is not being used anywhere else in that file. 
After commenting it out, I will be testing out the same curl command curl http://localhost:8000/health to check if the redis_healthcheck is successful.
Break it into 3–5 concrete sub-tasks.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
the input of the fix is the broken health_check() function. The fix should make the broken function work.

### Risks & unknowns
What could go wrong? What are you still unsure about?
Commenting out just the line that accesses the settings.redis_host attribute might still not lead to the healthcheck function passing. that's because I see there is another settings.redis_port attribute that might not exist as well. In order to work around this, I would need to include the settings.redis_port attribute in the scope of my fix which is beyond the original scope.

### Edge cases
What inputs or states should your fix handle gracefully?
My fix should not break other function calls outside of the health endpoint. It should not falsely report a successful ping if the redis docker compose container is not healthy.

"""
AI Planning package.

The planning module is responsible for converting a user request
into a validated, ordered, dependency-aware execution plan before
a single line of code is written or any tool is invoked.

Import order for consumers:
    plan_step  →  plan  →  (analyzers)  →  roadmap_builder  →  planner
"""

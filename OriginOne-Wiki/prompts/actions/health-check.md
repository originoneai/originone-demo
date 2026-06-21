# Action: Health Check

You are running a knowledge health check.

Goal: inspect whether a stage is still a usable LLM-Wiki slice.

Check:

- `raw/` has original evidence and has not been overwritten by summaries.
- `wiki/index.md` exists and acts as the retrieval entrance.
- `wiki/source-summary-*.md` pages cite raw sources.
- `wiki/concept-*.md` pages cite evidence and avoid unsupported claims.
- `output/` files clearly separate one-time task results from long-term wiki knowledge.
- Data-development outputs name impacted tables, fields, metrics, and uncertainty.
- Project-knowledge outputs name source cards, requirements, rules, and acceptance checks.

Save findings to `output/health-check/llm-wiki-health-check.md` when the stage has a nested output structure; otherwise save to `output/llm-wiki-health-check.md`.

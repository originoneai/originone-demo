# Action: Weave Raw Into Wiki

You are running `weave`.

Goal: read the stage's `raw/` materials and update `wiki/` as long-term knowledge.

Required work:

1. Inspect all files under the stage's `raw/` directory, including nested folders.
2. Do not edit any raw file.
3. For each meaningful raw file, create or update one `wiki/source-summary-*.md` file.
4. Create or update stable `wiki/concept-*.md` pages when multiple raw files support the same reusable idea.
5. Update `wiki/index.md` as the stage's retrieval entrance.
6. Every generated or updated wiki file must include:
   - `source_refs`
   - what the page is useful for
   - what a human should check
   - uncertainty or conflict notes when needed
7. Keep the pages short enough for a beginner to inspect from the terminal.

Output in your final response:

- Files created or updated.
- Evidence read.
- Any uncertainty that should not be promoted to long-term knowledge yet.

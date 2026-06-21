# Action: Ask With Wiki-First Retrieval

You are running `ask`.

Goal: answer the user question by reading the stage's wiki first, then raw evidence when the wiki is not enough.

Required work:

1. Read `wiki/index.md` first.
2. Read the most relevant `wiki/*.md` pages.
3. Read raw files only when needed for evidence, missing details, or conflict checking.
4. Save the answer to `output/ask-<short-question-slug>.md`.
5. The output file must include:
   - the question
   - retrieval path, separated into wiki hits and raw evidence
   - concise answer
   - source references
   - what should be checked by a human
   - whether any part should be promoted back into wiki later
6. Do not edit `raw/`.
7. Do not edit `wiki/` unless the question explicitly asks for wiki maintenance.

Output in your final response:

- Output file path.
- Wiki pages used.
- Raw evidence used.
- Any follow-up maintenance suggestion.

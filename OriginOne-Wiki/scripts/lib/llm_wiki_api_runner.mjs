import fs from "node:fs/promises";
import path from "node:path";

const root = process.argv[2];
const args = process.argv.slice(3);

function usage(exitCode = 0) {
  const text = `Usage:
  bash scripts/llm_wiki_api_runner.sh prompt weave <stage>
  bash scripts/llm_wiki_api_runner.sh prompt ask <stage> "<question>"
  bash scripts/llm_wiki_api_runner.sh dry-run weave <stage>
  bash scripts/llm_wiki_api_runner.sh dry-run ask <stage> "<question>"
  bash scripts/llm_wiki_api_runner.sh weave <stage>
  bash scripts/llm_wiki_api_runner.sh ask <stage> "<question>"

Config:
  LLM_WIKI_API_BASE_URL   default: https://api.deepseek.com
  LLM_WIKI_API_MODEL      default: deepseek-v4-flash
  LLM_WIKI_API_KEY        preferred generic key
  DEEPSEEK_API_KEY        used when LLM_WIKI_API_KEY is empty
  OPENAI_API_KEY          used when both keys above are empty

The API runner calls an OpenAI-compatible Chat Completions API. It asks the
model for file-level JSON, then writes only safe paths:
  weave -> <stage>/wiki/*.md
  ask   -> <stage>/output/*.md
`;
  (exitCode === 0 ? console.log : console.error)(text);
  process.exit(exitCode);
}

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const cmd = argv[0];
  if (!cmd || cmd === "-h" || cmd === "--help" || cmd === "help") {
    usage(0);
  }

  if (cmd === "prompt" || cmd === "dry-run") {
    const action = argv[1];
    const stage = argv[2];
    const question = argv.slice(3).join(" ");
    if (!action || !stage) usage(1);
    return { mode: cmd, action, stage, question };
  }

  if (cmd === "weave" || cmd === "ask") {
    const stage = argv[1];
    const question = argv.slice(2).join(" ");
    if (!stage || (cmd === "ask" && !question)) usage(1);
    return { mode: "run", action: cmd, stage, question };
  }

  fail(`unknown command: ${cmd}`);
}

function fileLang(filePath) {
  if (filePath.endsWith(".md")) return "markdown";
  if (filePath.endsWith(".sql")) return "sql";
  if (filePath.endsWith(".json")) return "json";
  if (filePath.endsWith(".yaml") || filePath.endsWith(".yml")) return "yaml";
  if (filePath.endsWith(".csv")) return "csv";
  return "text";
}

function isTextFile(filePath) {
  return [".md", ".sql", ".txt", ".json", ".yaml", ".yml", ".csv"].some((ext) =>
    filePath.endsWith(ext),
  );
}

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walk(fullPath)));
    } else if (entry.isFile() && isTextFile(fullPath)) {
      files.push(fullPath);
    }
  }
  return files.sort();
}

async function buildStageBundle(stage) {
  const stageDir = path.join(root, stage);
  const files = await walk(stageDir);
  const parts = [];

  for (const filePath of files) {
    const rel = path.relative(root, filePath).split(path.sep).join("/");
    const content = await fs.readFile(filePath, "utf8");
    parts.push(`## File: ${rel}\n\n~~~~${fileLang(filePath)}\n${content}\n~~~~`);
  }

  return { files, text: parts.join("\n\n") };
}

async function readRequired(filePath) {
  if (!(await pathExists(filePath))) {
    fail(`missing file: ${path.relative(root, filePath)}`);
  }
  return fs.readFile(filePath, "utf8");
}

function allowedDescription(action, stage) {
  if (action === "weave") return `Only write Markdown files under ${stage}/wiki/`;
  if (action === "ask") return `Only write Markdown files under ${stage}/output/`;
  fail(`unsupported action for API runner: ${action}`);
}

async function buildPrompt(action, stage, question) {
  const stageDir = path.join(root, stage);
  if (!(await pathExists(stageDir))) fail(`stage not found: ${stage}`);

  const actionPrompt = path.join(root, "prompts", "actions", `${action}.md`);
  const systemPrompt = await readRequired(path.join(root, "prompts", "llm-wiki-system.md"));
  const actionText = await readRequired(actionPrompt);
  const bundle = await buildStageBundle(stage);

  const contract = `# API Runner Mode

You are being called through an OpenAI-compatible Chat Completions API.
You cannot read or edit the user's local file system directly.

Use the bundled files below as evidence. Return only one valid JSON object.
Do not wrap it in Markdown fences.

Repository root:

\`\`\`text
${root}
\`\`\`

Stage:

\`\`\`text
${stage}
\`\`\`

Question:

\`\`\`text
${question || "N/A"}
\`\`\`

Allowed writes:

- ${allowedDescription(action, stage)}
- Never write to raw/.
- Never write outside this stage.
- Every returned file must contain complete file content, not a patch.

Required JSON schema:

\`\`\`json
{
  "summary": "short summary of what will be written",
  "files": [
    {
      "path": "${stage}/${action === "weave" ? "wiki/source-summary-example.md" : "output/ask-example.md"}",
      "content": "complete Markdown file content",
      "reason": "why this file is needed"
    }
  ],
  "source_refs": ["${stage}/raw/example.md"],
  "human_check": ["what a human should verify"]
}
\`\`\`

# Bundled Stage Files

${bundle.text}
`;

  return {
    prompt: [systemPrompt, actionText, contract].join("\n\n"),
    bundledFileCount: bundle.files.length,
  };
}

function requestConfig() {
  const baseUrl = (process.env.LLM_WIKI_API_BASE_URL || "https://api.deepseek.com").replace(/\/+$/, "");
  const model = process.env.LLM_WIKI_API_MODEL || "deepseek-v4-flash";
  const apiKey =
    process.env.LLM_WIKI_API_KEY || process.env.DEEPSEEK_API_KEY || process.env.OPENAI_API_KEY || "";
  const maxTokens = Number.parseInt(process.env.LLM_WIKI_API_MAX_TOKENS || "8192", 10);
  const temperature = Number.parseFloat(process.env.LLM_WIKI_API_TEMPERATURE || "0.2");
  return { baseUrl, model, apiKey, maxTokens, temperature };
}

async function callApi(prompt) {
  const cfg = requestConfig();
  if (!cfg.apiKey) {
    fail("missing API key. Set LLM_WIKI_API_KEY, DEEPSEEK_API_KEY, or OPENAI_API_KEY in .env");
  }

  const body = {
    model: cfg.model,
    messages: [
      {
        role: "system",
        content:
          "You generate safe file-level JSON for an LLM-Wiki runner. Return JSON only.",
      },
      { role: "user", content: prompt },
    ],
    response_format: { type: "json_object" },
    max_tokens: cfg.maxTokens,
    temperature: cfg.temperature,
  };

  const response = await fetch(`${cfg.baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${cfg.apiKey}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const text = await response.text();
  if (!response.ok) {
    fail(`API request failed: HTTP ${response.status}\n${text}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    fail(`API returned non-JSON response:\n${text.slice(0, 1000)}`);
  }

  const content = parsed?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || !content.trim()) {
    fail(`API response did not contain choices[0].message.content:\n${text.slice(0, 1000)}`);
  }
  return content;
}

function parseModelJson(content) {
  let text = content.trim();
  const fenceMatch = text.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  if (fenceMatch) text = fenceMatch[1].trim();

  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return JSON.parse(text.slice(start, end + 1));
    }
    throw new Error("model output is not valid JSON");
  }
}

function validateWritePath(action, stage, relPath) {
  if (typeof relPath !== "string" || !relPath.trim()) {
    fail("file path must be a non-empty string");
  }

  const rawPath = relPath.replaceAll("\\", "/");
  const rawParts = rawPath.split("/");
  if (rawParts.includes("..")) {
    fail(`unsafe path traversal: ${relPath}`);
  }

  const normalized = path.posix.normalize(rawPath);
  if (path.isAbsolute(normalized) || normalized.startsWith("../") || normalized.includes("/../")) {
    fail(`unsafe path: ${relPath}`);
  }

  if (!normalized.endsWith(".md")) {
    fail(`API runner only writes Markdown files: ${normalized}`);
  }

  const allowedPrefix = action === "weave" ? `${stage}/wiki/` : `${stage}/output/`;
  if (!normalized.startsWith(allowedPrefix)) {
    fail(`path not allowed for ${action}: ${normalized}. Expected ${allowedPrefix}*.md`);
  }

  if (normalized.includes("/raw/")) {
    fail(`raw files are immutable: ${normalized}`);
  }

  const absolute = path.resolve(root, normalized);
  if (!absolute.startsWith(`${root}${path.sep}`)) {
    fail(`path escapes repository root: ${normalized}`);
  }

  return { normalized, absolute };
}

async function applyFiles(action, stage, result) {
  if (!result || typeof result !== "object") fail("model JSON must be an object");
  if (!Array.isArray(result.files) || result.files.length === 0) {
    fail("model JSON must include a non-empty files array");
  }

  const written = [];
  for (const file of result.files) {
    const { normalized, absolute } = validateWritePath(action, stage, file.path);
    if (typeof file.content !== "string" || !file.content.trim()) {
      fail(`file content must be non-empty for ${normalized}`);
    }
    await fs.mkdir(path.dirname(absolute), { recursive: true });
    await fs.writeFile(absolute, file.content.endsWith("\n") ? file.content : `${file.content}\n`, "utf8");
    written.push({ path: normalized, reason: file.reason || "" });
  }

  console.log("API runner wrote files:");
  for (const file of written) {
    console.log(`- ${file.path}${file.reason ? ` (${file.reason})` : ""}`);
  }

  if (result.summary) {
    console.log("\nSummary:");
    console.log(result.summary);
  }
  if (Array.isArray(result.source_refs) && result.source_refs.length > 0) {
    console.log("\nSource refs:");
    for (const ref of result.source_refs) console.log(`- ${ref}`);
  }
  if (Array.isArray(result.human_check) && result.human_check.length > 0) {
    console.log("\nHuman check:");
    for (const item of result.human_check) console.log(`- ${item}`);
  }
}

async function main() {
  if (!root) usage(1);
  const parsed = parseArgs(args);
  const { prompt, bundledFileCount } = await buildPrompt(
    parsed.action,
    parsed.stage,
    parsed.question,
  );

  if (parsed.mode === "prompt") {
    console.log(prompt);
    return;
  }

  const cfg = requestConfig();
  if (parsed.mode === "dry-run") {
    console.log("API runner dry run");
    console.log(`base_url: ${cfg.baseUrl}`);
    console.log(`model: ${cfg.model}`);
    console.log(`action: ${parsed.action}`);
    console.log(`stage: ${parsed.stage}`);
    console.log(`bundled_files: ${bundledFileCount}`);
    console.log(`prompt_chars: ${prompt.length}`);
    console.log(`allowed_writes: ${allowedDescription(parsed.action, parsed.stage)}`);
    console.log("api_call: skipped");
    return;
  }

  const content = await callApi(prompt);
  let result;
  try {
    result = parseModelJson(content);
  } catch (error) {
    fail(`${error.message}\nModel output:\n${content.slice(0, 2000)}`);
  }
  await applyFiles(parsed.action, parsed.stage, result);
}

main().catch((error) => {
  fail(error?.stack || error?.message || String(error));
});

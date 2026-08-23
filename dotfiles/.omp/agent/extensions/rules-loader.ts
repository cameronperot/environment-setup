import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

function loadRules(): string {
  const rulesDir = path.join(os.homedir(), ".agent", "rules");
  if (!fs.existsSync(rulesDir)) return "";

  const files = fs
    .readdirSync(rulesDir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".md"))
    .map((entry) => entry.name)
    .sort();

  if (files.length === 0) return "";

  return files
    .map((file) => fs.readFileSync(path.join(rulesDir, file), "utf8"))
    .join("\n\n")
    .trim();
}

interface BeforeAgentStartEvent {
  systemPrompt?: string | string[];
}

type EventHandler = (event: never) => void | Promise<unknown>;

interface AgentAPI {
  on(event: string, handler: EventHandler): void;
}

export default function (agent: AgentAPI) {
  // Rules are read once per session; edits require a session restart.
  let rules = "";

  agent.on("session_start", async () => {
    rules = loadRules();
  });

  agent.on("before_agent_start", async (event: BeforeAgentStartEvent) => {
    if (!rules) return;

    // before_agent_start passes systemPrompt as a string or an array of system
    // prompt blocks; flatten to one string for insertion.
    const raw = event.systemPrompt ?? "";
    const systemPrompt = Array.isArray(raw) ? raw.join("\n") : raw;

    // Insert the rules inside the global AGENTS.md (~/.omp/agent/AGENTS.md)
    // file block, right before its closing tag, so they read as a continuation
    // of it. omp wraps context files in <file path="..."> blocks, unlike pi's
    // <project_instructions>.
    const globalAgentsMd = path.join(os.homedir(), ".omp", "agent", "AGENTS.md");
    const openTag = `<file path="${globalAgentsMd}">`;
    const openIdx = systemPrompt.indexOf(openTag);
    if (openIdx !== -1) {
      const closeIdx = systemPrompt.indexOf("</file>", openIdx + openTag.length);
      if (closeIdx !== -1) {
        return {
          systemPrompt:
            systemPrompt.slice(0, closeIdx) + `\n\n${rules}\n` + systemPrompt.slice(closeIdx),
        };
      }
    }

    // Fallback: append at the end when the global AGENTS.md block is absent.
    return {
      systemPrompt: systemPrompt + "\n\n" + rules,
    };
  });
}

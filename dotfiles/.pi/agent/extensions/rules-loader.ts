import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

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

export default function rulesLoader(pi: ExtensionAPI) {
	// Rules are read once per session; edits require a session restart.
	let rules = "";

	pi.on("session_start", async () => {
		rules = loadRules();
	});

	pi.on("before_agent_start", async (event) => {
		if (!rules) return;

		const systemPrompt = event.systemPrompt;

		// Insert the rules after the first AGENTS.md block so they read as a
		// continuation of it (directly inside the same <project_instructions>).
		const agentsMd = event.systemPromptOptions.contextFiles?.find(
			(entry) => path.basename(entry.path) === "AGENTS.md",
		);
		if (agentsMd) {
			const openTag = `<project_instructions path="${agentsMd.path}">`;
			const openIdx = systemPrompt.indexOf(openTag);
			if (openIdx !== -1) {
				const closeIdx = systemPrompt.indexOf("</project_instructions>", openIdx + openTag.length);
				if (closeIdx !== -1) {
					return {
						systemPrompt:
							systemPrompt.slice(0, closeIdx) + `\n\n${rules}\n` + systemPrompt.slice(closeIdx),
					};
				}
			}
		}

		// Fallback: append at the end when no AGENTS.md block is present.
		return {
			systemPrompt: systemPrompt + "\n\n" + rules,
		};
	});
}

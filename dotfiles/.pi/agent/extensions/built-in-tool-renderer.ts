/**
 * Built-in Tool Renderer + Read Audit
 *
 * Merge of two shipped examples:
 * - built-in-tool-renderer.ts - compact renderCall/renderResult for read, bash,
 *   edit and write, delegating execution to the original implementations.
 * - tool-override.ts - access logging and zero-access blocking on `read`,
 *   plus the /read-log command. The paths it refuses come from the
 *   `zeroAccessPaths` policy in guard-rules.json, shared with the bash guard.
 *
 * They are merged rather than installed side by side because Pi keeps the
 * FIRST registration for a given tool name (runner.js getAllRegisteredTools)
 * and extension discovery is an unsorted readdir, so shipping both files would
 * drop one `read` registration nondeterministically.
 *
 * Difference from the shipped tool-override.ts: `read` delegates to
 * createReadTool() rather than reimplementing the read. The shipped example
 * returns its own details shape and does naive byte-slice truncation, which
 * loses image support, ReadToolDetails and the built-in truncation semantics.
 * Here the block check and the log entry wrap the real implementation, and a
 * block also notifies and appends the same `guard-block` session entry the other
 * three guards do, so the read path leaves the same trace they leave.
 *
 * The base tools are built per-cwd, and `read`/`bash` are given the same
 * settings-derived options core passes in _buildRuntime (images.autoResize,
 * shellCommandPrefix, shellPath). Building them once from process.cwd() with no
 * options — as the shipped example does — silently discards those settings and
 * pins the tools to the startup directory. `edit` and `write` take no options.
 */

import type { BashToolDetails, EditToolDetails, ExtensionAPI, ReadToolDetails } from "@earendil-works/pi-coding-agent";
import {
	createBashTool,
	createEditTool,
	createReadTool,
	createWriteTool,
	SettingsManager,
} from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { LOG_FILE, logAccess } from "./shared/access-log.ts";
import { blockReason, type GuardAudit, takeLoadIssue, zeroAccessMatch } from "./shared/rules.ts";

const BLOCKED_PREFIX = "Access denied:";

/**
 * Base tools for a working directory, built with the settings that apply there.
 * Memoized because a tool is rebuilt on every execute() otherwise, and the
 * settings read is filesystem work.
 */
function makeBaseTools() {
	const cache = new Map<string, ReturnType<typeof buildForCwd>>();

	function buildForCwd(cwd: string) {
		const settings = SettingsManager.create(cwd);
		return {
			read: createReadTool(cwd, { autoResizeImages: settings.getImageAutoResize() }),
			bash: createBashTool(cwd, {
				commandPrefix: settings.getShellCommandPrefix(),
				shellPath: settings.getShellPath(),
			}),
			edit: createEditTool(cwd),
			write: createWriteTool(cwd),
		};
	}

	return (cwd: string) => {
		let tools = cache.get(cwd);
		if (!tools) {
			tools = buildForCwd(cwd);
			cache.set(cwd, tools);
		}
		return tools;
	};
}

export default function (pi: ExtensionAPI) {
	const baseTools = makeBaseTools();

	// Registration needs a description and schema before any ctx exists. Both are
	// cwd- and option-independent, so the startup-cwd set supplies them; every
	// execute() resolves its own set from ctx.cwd.
	const template = baseTools(process.cwd());

	// --- Read tool: audit access, then show path and line count ---
	pi.registerTool({
		name: "read",
		label: "read (audited)",
		description: template.read.description,
		parameters: template.read.parameters,

		async execute(toolCallId, params, signal, onUpdate, ctx) {
			const absolutePath = resolve(ctx.cwd, params.path);

			if (ctx.hasUI) {
				const issue = takeLoadIssue(ctx.cwd);
				if (issue) ctx.ui.notify(`Guard policy: ${issue}`, "warning");
			}

			const secret = zeroAccessMatch(absolutePath, ctx.cwd);
			if (secret) {
				const rule = `zero-access path "${secret}"`;
				await logAccess(absolutePath, false, `matches zero-access rule "${secret}"`);
				if (ctx.hasUI) {
					ctx.ui.notify(`Blocked read of ${rule}: ${params.path}`, "warning");
				}
				pi.appendEntry<GuardAudit>("guard-block", {
					tool: "read",
					rule,
					action: "blocked",
					detail: absolutePath,
				});
				return {
					content: [
						{
							type: "text",
							text: `${BLOCKED_PREFIX} ${blockReason(`"${params.path}" matches the ${rule} in guard-rules.json.`)}`,
						},
					],
					details: undefined,
				};
			}

			await logAccess(absolutePath, true);
			return baseTools(ctx.cwd).read.execute(toolCallId, params, signal, onUpdate);
		},

		renderCall(args, theme, _context) {
			let text = theme.fg("toolTitle", theme.bold("read "));
			text += theme.fg("accent", args.path);
			if (args.offset || args.limit) {
				const parts: string[] = [];
				if (args.offset) parts.push(`offset=${args.offset}`);
				if (args.limit) parts.push(`limit=${args.limit}`);
				text += theme.fg("dim", ` (${parts.join(", ")})`);
			}
			return new Text(text, 0, 0);
		},

		renderResult(result, { expanded, isPartial }, theme, _context) {
			if (isPartial) return new Text(theme.fg("warning", "Reading..."), 0, 0);

			const details = result.details as ReadToolDetails | undefined;
			const content = result.content[0];

			if (content?.type === "image") {
				return new Text(theme.fg("success", "Image loaded"), 0, 0);
			}

			if (content?.type !== "text") {
				return new Text(theme.fg("error", "No content"), 0, 0);
			}

			if (content.text.startsWith(BLOCKED_PREFIX)) {
				return new Text(theme.fg("error", "blocked (zero-access path)"), 0, 0);
			}

			const lineCount = content.text.split("\n").length;
			let text = theme.fg("success", `${lineCount} lines`);

			if (details?.truncation?.truncated) {
				text += theme.fg("warning", ` (truncated from ${details.truncation.totalLines})`);
			}

			if (expanded) {
				const lines = content.text.split("\n").slice(0, 15);
				for (const line of lines) {
					text += `\n${theme.fg("dim", line)}`;
				}
				if (lineCount > 15) {
					text += `\n${theme.fg("muted", `... ${lineCount - 15} more lines`)}`;
				}
			}

			return new Text(text, 0, 0);
		},
	});

	// --- Bash tool: show command and exit code ---
	pi.registerTool({
		name: "bash",
		label: "bash",
		description: template.bash.description,
		parameters: template.bash.parameters,

		async execute(toolCallId, params, signal, onUpdate, ctx) {
			return baseTools(ctx.cwd).bash.execute(toolCallId, params, signal, onUpdate);
		},

		renderCall(args, theme, _context) {
			let text = theme.fg("toolTitle", theme.bold("$ "));
			const cmd = args.command.length > 80 ? `${args.command.slice(0, 77)}...` : args.command;
			text += theme.fg("accent", cmd);
			if (args.timeout) {
				text += theme.fg("dim", ` (timeout: ${args.timeout}s)`);
			}
			return new Text(text, 0, 0);
		},

		renderResult(result, { expanded, isPartial }, theme, _context) {
			if (isPartial) return new Text(theme.fg("warning", "Running..."), 0, 0);

			const details = result.details as BashToolDetails | undefined;
			const content = result.content[0];
			const output = content?.type === "text" ? content.text : "";

			const exitMatch = output.match(/exit code: (\d+)/);
			const exitCode = exitMatch ? parseInt(exitMatch[1], 10) : null;
			const lineCount = output.split("\n").filter((l) => l.trim()).length;

			let text = "";
			if (exitCode === 0 || exitCode === null) {
				text += theme.fg("success", "done");
			} else {
				text += theme.fg("error", `exit ${exitCode}`);
			}
			text += theme.fg("dim", ` (${lineCount} lines)`);

			if (details?.truncation?.truncated) {
				text += theme.fg("warning", " [truncated]");
			}

			if (expanded) {
				const lines = output.split("\n").slice(0, 20);
				for (const line of lines) {
					text += `\n${theme.fg("dim", line)}`;
				}
				if (output.split("\n").length > 20) {
					text += `\n${theme.fg("muted", "... more output")}`;
				}
			}

			return new Text(text, 0, 0);
		},
	});

	// --- Edit tool: show path and diff stats ---
	pi.registerTool({
		name: "edit",
		label: "edit",
		description: template.edit.description,
		parameters: template.edit.parameters,
		renderShell: "self",

		async execute(toolCallId, params, signal, onUpdate, ctx) {
			return baseTools(ctx.cwd).edit.execute(toolCallId, params, signal, onUpdate);
		},

		renderCall(args, theme, _context) {
			let text = theme.fg("toolTitle", theme.bold("edit "));
			text += theme.fg("accent", args.path);
			return new Text(text, 0, 0);
		},

		renderResult(result, { expanded, isPartial }, theme, _context) {
			if (isPartial) return new Text(theme.fg("warning", "Editing..."), 0, 0);

			const details = result.details as EditToolDetails | undefined;
			const content = result.content[0];

			if (content?.type === "text" && content.text.startsWith("Error")) {
				return new Text(theme.fg("error", content.text.split("\n")[0]), 0, 0);
			}

			if (!details?.diff) {
				return new Text(theme.fg("success", "Applied"), 0, 0);
			}

			// Count additions and removals from the diff
			const diffLines = details.diff.split("\n");
			let additions = 0;
			let removals = 0;
			for (const line of diffLines) {
				if (line.startsWith("+") && !line.startsWith("+++")) additions++;
				if (line.startsWith("-") && !line.startsWith("---")) removals++;
			}

			let text = theme.fg("success", `+${additions}`);
			text += theme.fg("dim", " / ");
			text += theme.fg("error", `-${removals}`);

			if (expanded) {
				for (const line of diffLines.slice(0, 30)) {
					if (line.startsWith("+") && !line.startsWith("+++")) {
						text += `\n${theme.fg("success", line)}`;
					} else if (line.startsWith("-") && !line.startsWith("---")) {
						text += `\n${theme.fg("error", line)}`;
					} else {
						text += `\n${theme.fg("dim", line)}`;
					}
				}
				if (diffLines.length > 30) {
					text += `\n${theme.fg("muted", `... ${diffLines.length - 30} more diff lines`)}`;
				}
			}

			return new Text(text, 0, 0);
		},
	});

	// --- Write tool: show path and size ---
	pi.registerTool({
		name: "write",
		label: "write",
		description: template.write.description,
		parameters: template.write.parameters,

		async execute(toolCallId, params, signal, onUpdate, ctx) {
			return baseTools(ctx.cwd).write.execute(toolCallId, params, signal, onUpdate);
		},

		renderCall(args, theme, _context) {
			let text = theme.fg("toolTitle", theme.bold("write "));
			text += theme.fg("accent", args.path);
			const lineCount = args.content.split("\n").length;
			text += theme.fg("dim", ` (${lineCount} lines)`);
			return new Text(text, 0, 0);
		},

		renderResult(result, { isPartial }, theme, _context) {
			if (isPartial) return new Text(theme.fg("warning", "Writing..."), 0, 0);

			const content = result.content[0];
			if (content?.type === "text" && content.text.startsWith("Error")) {
				return new Text(theme.fg("error", content.text.split("\n")[0]), 0, 0);
			}

			return new Text(theme.fg("success", "Written"), 0, 0);
		},
	});

	// Command to view the access log
	pi.registerCommand("read-log", {
		description: "View the file access log",
		handler: async (_args, ctx) => {
			try {
				const log = readFileSync(LOG_FILE, "utf-8");
				const lines = log.trim().split("\n").slice(-20); // Last 20 entries
				ctx.ui.notify(`Recent file access:\n${lines.join("\n")}`, "info");
			} catch {
				ctx.ui.notify("No access log found", "info");
			}
		},
	});
}

/**
 * Approve Gate Extension
 *
 * Two opt-in approval modes, neither on by default:
 *
 * - `/approve`     — every `write` and `edit` needs confirmation.
 * - `/approve-all` — every tool needs confirmation except the ones in
 *                    ALWAYS_ALLOWED.
 *
 * This fills the gap between the other protections, which are *prevention*
 * (plan mode and the `review` preset remove `edit`/`write` entirely),
 * *selective confirmation* (the guards prompt only on a `guard-rules.json`
 * match) and *undo* (`pi-rewind`). Nothing else gates an ordinary edit.
 *
 * Reading is never gated, in either mode. `read`, `grep`, `find` and `ls`
 * cannot modify the filesystem, and prompting for every file the model opens
 * makes the mode unusable — the governing principle is gate side effects, not
 * information. `todo` and `questionnaire` pass for the same reason; gating
 * `questionnaire` would mean approving the model's request to ask you a
 * question.
 *
 * The gate is additive to the guards in `protected-paths*.ts` and
 * `permission-gate.ts`: turning a mode on can only ever add confirmations,
 * never remove one. It is TUI/RPC only — with no UI to ask through it blocks,
 * like every `ask` rule.
 * It also does not reach subagent children, which spawn `--no-session` and so
 * always start with the mode off.
 */

import {
	type ExtensionAPI,
	type ExtensionContext,
	isToolCallEventType,
	type ToolCallEvent,
} from "@earendil-works/pi-coding-agent";
import {
	bashPatterns,
	blockReason,
	commandPathMatch,
	DELETE_INDICATORS,
	getRules,
	type GuardAudit,
	readOnlyMatch,
	WRITE_INDICATORS,
	zeroAccessMatch,
} from "./shared/rules.ts";

type ApproveMode = "off" | "writes" | "all";

/** Shape of the `approve-mode` session entry the mode is restored from. */
interface ApproveState {
	mode: ApproveMode;
}

const WRITE_TOOLS = new Set(["write", "edit"]);

/**
 * Tools that pass without a prompt under `/approve-all`.
 *
 * Membership is the whole policy: anything not listed is gated, so a tool
 * added later is covered by default rather than silently escaping the mode.
 */
const ALWAYS_ALLOWED = new Set(["read", "grep", "find", "ls", "todo", "questionnaire"]);

const MODE_STATUS: Record<Exclude<ApproveMode, "off">, string> = {
	writes: "✔ approve",
	all: "✔ approve-all",
};

const MODE_NOTICE: Record<ApproveMode, string> = {
	off: "Approve mode off. Tool calls run without confirmation.",
	writes: "Approve mode on. Every write and edit needs confirmation.",
	all: `Approve-all mode on. Every tool needs confirmation except ${[...ALWAYS_ALLOWED].join(", ")}.`,
};

const MAX_PREVIEW_LINES = 24;
const MAX_PREVIEW_CHARS = 1200;

/** Keep a preview to something a selector dialog can show without swamping it. */
function clamp(text: string): string {
	const lines = text.split("\n");
	const clipped =
		lines.length > MAX_PREVIEW_LINES
			? `${lines.slice(0, MAX_PREVIEW_LINES).join("\n")}\n… ${lines.length - MAX_PREVIEW_LINES} more lines`
			: text;
	return clipped.length > MAX_PREVIEW_CHARS ? `${clipped.slice(0, MAX_PREVIEW_CHARS)}…` : clipped;
}

function prefixLines(text: string, marker: string): string {
	return text
		.split("\n")
		.map((line) => `${marker} ${line}`)
		.join("\n");
}

/**
 * What the call is about to do, in enough detail to answer honestly.
 *
 * `tool_call` can rewrite arguments, but there is no way to hand an edited
 * version back through a selector, so the answer is yes or no on what is
 * shown — which is why the preview shows the change rather than naming it.
 */
function preview(event: ToolCallEvent): string {
	if (isToolCallEventType("bash", event)) {
		return event.input.command;
	}
	if (isToolCallEventType("write", event)) {
		const lines = event.input.content.split("\n").length;
		return `${event.input.path} (${lines} lines)\n\n${event.input.content}`;
	}
	if (isToolCallEventType("edit", event)) {
		const blocks = event.input.edits.map(
			(edit, i) =>
				`── block ${i + 1} ──\n${prefixLines(edit.oldText, "-")}\n${prefixLines(edit.newText, "+")}`,
		);
		const count = event.input.edits.length;
		return [`${event.input.path} (${count} edit${count === 1 ? "" : "s"})`, ...blocks].join("\n");
	}
	return JSON.stringify(event.input, null, 2);
}

/** The one-line identifier recorded in the audit entry. */
function auditDetail(event: ToolCallEvent): string {
	if (isToolCallEventType("bash", event)) return event.input.command;
	const path = (event.input as { path?: unknown }).path;
	return typeof path === "string" ? path : clamp(JSON.stringify(event.input));
}

/**
 * Will one of the guards already deal with this call?
 *
 * Extension load order is unsorted `readdir` and the first handler to block
 * wins, so without this check the gate can prompt for a call another guard is
 * about to refuse — or prompt a second time for one it is about to ask about.
 * Either way the answer the user gives is not the one that decides the call.
 * Deferring keeps it to exactly one prompt whichever handler runs first.
 */
function guardHandles(event: ToolCallEvent, cwd: string): boolean {
	if (isToolCallEventType("write", event) || isToolCallEventType("edit", event)) {
		const path = event.input.path;
		return zeroAccessMatch(path, cwd) !== undefined || readOnlyMatch(path, cwd) !== undefined;
	}
	if (!isToolCallEventType("bash", event)) return false;

	const command = event.input.command;
	if (bashPatterns(cwd).some((rule) => rule.regex.test(command))) return true;

	const { rules } = getRules(cwd);
	if (commandPathMatch(command, rules.zeroAccessPaths, cwd)) return true;
	if (DELETE_INDICATORS.some((r) => r.test(command)) && commandPathMatch(command, rules.noDeletePaths, cwd)) {
		return true;
	}
	return (
		WRITE_INDICATORS.some((r) => r.test(command)) && commandPathMatch(command, rules.readOnlyPaths, cwd) !== undefined
	);
}

export default function (pi: ExtensionAPI) {
	let mode: ApproveMode = "off";
	// Set by "Yes to all remaining" so a ten-file refactor is not ten prompts.
	// Scoped to one agent run, and dropped whenever the mode changes.
	let approveRestOfRun = false;

	function updateStatus(ctx: ExtensionContext): void {
		ctx.ui.setStatus("approve", mode === "off" ? undefined : ctx.ui.theme.fg("warning", MODE_STATUS[mode]));
	}

	function setMode(next: ApproveMode, ctx: ExtensionContext): void {
		mode = next;
		approveRestOfRun = false;
		updateStatus(ctx);
		pi.appendEntry<ApproveState>("approve-mode", { mode });
		ctx.ui.notify(MODE_NOTICE[mode], "info");
	}

	/** Bare command toggles its own mode; an explicit `off` argument always turns it off. */
	function requested(args: string, target: ApproveMode): ApproveMode {
		if (args.trim() === "off") return "off";
		return mode === target ? "off" : target;
	}

	pi.registerCommand("approve", {
		description: "Toggle confirmation on every write and edit",
		handler: async (args, ctx) => setMode(requested(args, "writes"), ctx),
	});

	pi.registerCommand("approve-all", {
		description: `Toggle confirmation on every tool except ${[...ALWAYS_ALLOWED].join(", ")}`,
		handler: async (args, ctx) => setMode(requested(args, "all"), ctx),
	});

	pi.on("tool_call", async (event, ctx) => {
		if (mode === "off" || approveRestOfRun) return undefined;

		const gated = mode === "writes" ? WRITE_TOOLS.has(event.toolName) : !ALWAYS_ALLOWED.has(event.toolName);
		if (!gated || guardHandles(event, ctx.cwd)) return undefined;

		const rule = `approve mode "${mode}"`;
		const detail = auditDetail(event);

		if (!ctx.hasUI) {
			pi.appendEntry<GuardAudit>("guard-block", { tool: event.toolName, rule, action: "blocked", detail });
			return {
				block: true,
				reason: blockReason(`${event.toolName} needs approval in ${rule}, and there is no UI to ask through.`),
			};
		}

		const choice = await ctx.ui.select(`✔ Approve ${event.toolName}?\n\n${clamp(preview(event))}`, [
			"Yes",
			"No",
			"Yes to all remaining",
		]);

		if (choice !== "Yes" && choice !== "Yes to all remaining") {
			pi.appendEntry<GuardAudit>("guard-block", {
				tool: event.toolName,
				rule,
				action: "blocked_by_user",
				detail,
			});
			return { block: true, reason: blockReason(`Declined by user: ${event.toolName} was not approved in ${rule}.`) };
		}

		if (choice === "Yes to all remaining") approveRestOfRun = true;
		pi.appendEntry<GuardAudit>("guard-block", { tool: event.toolName, rule, action: "allowed_by_user", detail });
		return undefined;
	});

	// "Yes to all remaining" lasts one run. agent_settled rather than turn_end,
	// because it fires once the run has settled with no retry, compaction or
	// queued continuation left to come — a turn boundary would end it early.
	pi.on("agent_settled", async () => {
		approveRestOfRun = false;
	});

	function restore(ctx: ExtensionContext): void {
		const entry = ctx.sessionManager
			.getBranch()
			.filter((e) => e.type === "custom" && e.customType === "approve-mode")
			.pop() as { data?: ApproveState } | undefined;

		// getBranch(), not getEntries(): a mode enabled on a branch that /tree
		// navigated away from must not follow you onto the branch you moved to.
		mode = entry?.data?.mode ?? "off";
		approveRestOfRun = false;
		updateStatus(ctx);
	}

	pi.on("session_start", async (_event, ctx) => restore(ctx));
	pi.on("session_tree", async (_event, ctx) => restore(ctx));
}

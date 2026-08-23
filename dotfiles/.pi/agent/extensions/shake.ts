/**
 * /shake - mechanical context reduction
 *
 * Replaces old tool results with short stubs in the payload sent to the model.
 * Modelled on the /shake command in oh-my-pi (github.com/can1357/oh-my-pi),
 * which is a separate agent rather than a Pi extension, so the behaviour is
 * reimplemented here on Pi's `context` event.
 *
 * Non-destructive by construction. The `context` handler is a pure transform:
 * core applies it to a local variable on the way to the provider (pi-agent-core
 * streamAssistantResponse) and never writes the result back to session state.
 * The transcript on disk, the TUI rendering and /export all keep the full text.
 *
 * That is why the only state here is a set of shaken toolCallIds. The original
 * content arrives intact on every call and each stub is recomputed from it, so
 * nothing has to be cached for recovery and /unshake is a one-line restore.
 * The set is per-process: resuming a session starts unshaken.
 *
 * Manual only. Automatic shaking at a context threshold is deliberately not
 * wired up - rewriting an old message invalidates the provider's prompt cache
 * from that point onward, and whether that is a net win depends on the model's
 * cache pricing and the shape of the session. Measure before automating.
 *
 * Handler exceptions are not caught. The extension runner reports them through
 * emitError (shown in the TUI by showExtensionError) and falls back to the
 * untrimmed messages, so a bug here degrades loudly rather than silently.
 */

import type { ContextEvent, ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { estimateTokens, sessionEntryToContextMessages } from "@earendil-works/pi-coding-agent";

// Derived from the event rather than imported, so these can never drift from
// what the `context` handler is actually handed.
type AgentMessage = ContextEvent["messages"][number];
type ToolResultMessage = Extract<AgentMessage, { role: "toolResult" }>;

/** Newest slice of the transcript that /shake never touches, so the working set survives. */
const PROTECT_RECENT_TOKENS = 20_000;

/** A stub costs ~30 tokens, so smaller results are not worth disturbing. */
const MIN_RESULT_TOKENS = 200;

/** Below this, cache invalidation is likely to cost more than the reclaim saves. */
const MIN_SAVINGS_TOKENS = 2_000;

function asToolResult(message: AgentMessage): ToolResultMessage | undefined {
	return "role" in message && message.role === "toolResult" ? message : undefined;
}

function stubFor(message: ToolResultMessage): ToolResultMessage {
	const text = message.content.map((part) => (part.type === "text" ? part.text : "")).join("\n");
	const lines = text.split("\n").length;
	return {
		...message,
		content: [
			{
				type: "text",
				text: `[shaken] ${message.toolName} result omitted to save context (${lines} line${lines === 1 ? "" : "s"}, ~${estimateTokens(message)} tokens). Re-run the tool if you need it.`,
			},
		],
	};
}

function savingsFor(message: ToolResultMessage): number {
	return estimateTokens(message) - estimateTokens(stubFor(message));
}

/**
 * Oldest-first list of tool results worth shaking, skipping the protected
 * recent window and anything already shaken.
 */
function selectShakeable(messages: AgentMessage[], shaken: ReadonlySet<string>): ToolResultMessage[] {
	const picked: ToolResultMessage[] = [];
	let recentTokens = 0;

	for (let i = messages.length - 1; i >= 0; i--) {
		const message = messages[i];

		if (recentTokens < PROTECT_RECENT_TOKENS) {
			recentTokens += estimateTokens(message);
			continue;
		}

		const result = asToolResult(message);
		if (!result || shaken.has(result.toolCallId)) continue;

		// Images are left alone: a text stub is not a valid substitute for an
		// image block, and images.autoResize already bounds their size.
		if (result.content.some((part) => part.type === "image")) continue;
		if (estimateTokens(result) < MIN_RESULT_TOKENS) continue;

		picked.unshift(result);
	}

	return picked;
}

export default function (pi: ExtensionAPI) {
	const shaken = new Set<string>();
	let reclaimed = 0;

	pi.on("context", (event) => {
		if (shaken.size === 0) return undefined;

		let changed = false;
		const messages = event.messages.map((message) => {
			const result = asToolResult(message);
			if (!result || !shaken.has(result.toolCallId)) return message;
			changed = true;
			return stubFor(result);
		});

		return changed ? { messages } : undefined;
	});

	pi.registerCommand("shake", {
		description: "Drop old tool results from the context sent to the model",
		handler: async (_args, ctx) => {
			const messages = ctx.sessionManager.buildContextEntries().flatMap(sessionEntryToContextMessages);
			const picked = selectShakeable(messages, shaken);
			const savings = picked.reduce((total, message) => total + savingsFor(message), 0);

			if (savings < MIN_SAVINGS_TOKENS) {
				ctx.ui.notify(
					`Not worth shaking: ${picked.length} candidate(s), ~${savings} tokens. Shaking invalidates the prompt cache from the oldest rewritten message, so it needs to reclaim at least ${MIN_SAVINGS_TOKENS}.`,
					"info",
				);
				return;
			}

			for (const message of picked) shaken.add(message.toolCallId);
			reclaimed += savings;
			ctx.ui.setStatus("shake", `shake ${shaken.size} (~${Math.round(reclaimed / 1000)}k)`);
			ctx.ui.notify(
				`Shaken ${picked.length} tool result(s), ~${savings} tokens reclaimed. The transcript is unchanged; /unshake restores them.`,
				"info",
			);
		},
	});

	pi.registerCommand("unshake", {
		description: "Restore tool results previously dropped by /shake",
		handler: async (_args, ctx) => {
			if (shaken.size === 0) {
				ctx.ui.notify("Nothing is shaken.", "info");
				return;
			}

			const count = shaken.size;
			shaken.clear();
			reclaimed = 0;
			ctx.ui.setStatus("shake", undefined);
			ctx.ui.notify(`Restored ${count} tool result(s) to the model's context.`, "info");
		},
	});
}

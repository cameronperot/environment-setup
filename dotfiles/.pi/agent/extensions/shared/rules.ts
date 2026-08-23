/**
 * Guard policy — rule loading and path matching.
 *
 * The three guard extensions (`protected-paths.ts`, `protected-paths-bash.ts`,
 * `permission-gate.ts`) and the `read` guard in `built-in-tool-renderer.ts` are
 * the *mechanism*. The *policy* they enforce lives in `guard-rules.json`, looked
 * up in this order, first hit wins:
 *
 *   1. `<cwd>/.pi/guard-rules.json`      — per-repo policy
 *   2. `~/.pi/agent/guard-rules.json`    — global policy
 *
 * Rule classes:
 *
 * | Class                  | Effect                                              |
 * |------------------------|-----------------------------------------------------|
 * | `zeroAccessPaths`      | No read, no write, no bash reference.               |
 * | `zeroAccessAllowPaths` | Exceptions to the above (`.env.example`).           |
 * | `readOnlyPaths`        | Reads fine; write/edit and bash writes blocked.     |
 * | `noDeletePaths`        | Deletion and move-away blocked.                     |
 * | `bashPatterns`         | Regex over the bash command; `ask: true` confirms.  |
 *
 * JSON rather than YAML deliberately: Pi loads extensions through jiti with an
 * alias map covering only `@earendil-works/*` and `typebox`, and `~/.pi/agent`
 * has no `node_modules`. A bare `yaml` import resolves only by accident through
 * Pi's own nested copy, and would disappear the day Pi drops the dependency —
 * taking every guard with it. `JSON.parse` cannot fail to resolve, and it
 * matches `settings.json` / `presets.json` / `models.json` alongside it.
 *
 * This directory has no index.ts and no package.json, so Pi's extension
 * discovery (extensions/*.ts and extensions/*\/index.ts, one level, no
 * recursion) does not try to load it as an extension.
 */

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { isAbsolute, join, resolve } from "node:path";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

const HOME = homedir();

export interface BashPattern {
	pattern: string;
	reason: string;
	ask?: boolean;
}

export interface Rules {
	zeroAccessPaths: string[];
	zeroAccessAllowPaths: string[];
	readOnlyPaths: string[];
	noDeletePaths: string[];
	bashPatterns: BashPattern[];
}

/** Shape of a `guard-block` session entry, appended on every block or confirmation. */
export interface GuardAudit {
	tool: string;
	rule: string;
	action: "blocked" | "blocked_by_user" | "allowed_by_user";
	detail?: string;
}

/**
 * Minimum protection that applies when `guard-rules.json` is missing, malformed,
 * or omits a class. Deliberately much smaller than the shipped policy — it is a
 * floor, not a second copy to keep in sync. Its purpose is that a typo in the
 * policy file degrades protection rather than removing it: a guard that silently
 * allows everything is worse than one that is merely coarse.
 */
const SAFETY_FLOOR: Rules = {
	zeroAccessPaths: [".env", ".env.*", "*.env", "~/.ssh/", "~/.aws/", "~/.gnupg/"],
	zeroAccessAllowPaths: [".env.example", ".env-example"],
	readOnlyPaths: [".git/"],
	noDeletePaths: [".git/"],
	bashPatterns: [
		{ pattern: "\\brm\\s+(-[^\\s]*)*-[rRf]", reason: "rm with recursive or force flags", ask: true },
		{ pattern: "\\bsudo\\b", reason: "sudo (runs as root)", ask: true },
	],
};

export interface LoadedRules {
	rules: Rules;
	/** Absolute path the policy came from, or "built-in safety floor". */
	source: string;
	/** Set when the policy could not be used as written; surfaced once per cwd. */
	error?: string;
}

const cache = new Map<string, LoadedRules>();
const reported = new Set<string>();

function isStringArray(value: unknown): value is string[] {
	return Array.isArray(value) && value.every((entry) => typeof entry === "string");
}

function isBashPatternArray(value: unknown): value is BashPattern[] {
	return (
		Array.isArray(value) &&
		value.every(
			(entry) =>
				!!entry &&
				typeof entry === "object" &&
				typeof (entry as BashPattern).pattern === "string" &&
				typeof (entry as BashPattern).reason === "string",
		)
	);
}

/**
 * Merge a parsed policy over the floor. A class the file omits keeps the floor's
 * value, so leaving one out cannot silently disable it; a class the file states
 * replaces the floor's entirely, so it can be narrowed on purpose.
 */
function coerce(parsed: unknown): { rules: Rules; problems: string[] } {
	const problems: string[] = [];
	if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
		return { rules: SAFETY_FLOOR, problems: ["policy is not a JSON object"] };
	}
	const raw = parsed as Record<string, unknown>;
	const rules: Rules = { ...SAFETY_FLOOR };

	for (const key of ["zeroAccessPaths", "zeroAccessAllowPaths", "readOnlyPaths", "noDeletePaths"] as const) {
		if (raw[key] === undefined) continue;
		if (isStringArray(raw[key])) {
			rules[key] = raw[key];
		} else {
			problems.push(`${key} is not an array of strings`);
		}
	}

	if (raw.bashPatterns !== undefined) {
		if (isBashPatternArray(raw.bashPatterns)) {
			const valid: BashPattern[] = [];
			for (const entry of raw.bashPatterns) {
				try {
					new RegExp(entry.pattern);
					valid.push(entry);
				} catch {
					problems.push(`bashPatterns entry is not a valid regex: ${entry.pattern}`);
				}
			}
			rules.bashPatterns = valid;
		} else {
			problems.push("bashPatterns is not an array of {pattern, reason}");
		}
	}

	return { rules, problems };
}

export function getRules(cwd: string): LoadedRules {
	const cached = cache.get(cwd);
	if (cached) return cached;

	const candidates = [join(cwd, ".pi", "guard-rules.json"), join(getAgentDir(), "guard-rules.json")];
	const found = candidates.find((candidate) => existsSync(candidate));

	let loaded: LoadedRules;
	if (!found) {
		loaded = {
			rules: SAFETY_FLOOR,
			source: "built-in safety floor",
			error: `No guard-rules.json at ${candidates.join(" or ")} — falling back to the built-in safety floor.`,
		};
	} else {
		try {
			const { rules, problems } = coerce(JSON.parse(readFileSync(found, "utf-8")));
			loaded = {
				rules,
				source: found,
				error: problems.length > 0 ? `${found}: ${problems.join("; ")}` : undefined,
			};
		} catch (err) {
			loaded = {
				rules: SAFETY_FLOOR,
				source: "built-in safety floor",
				error: `${found} could not be parsed (${err instanceof Error ? err.message : String(err)}) — falling back to the built-in safety floor.`,
			};
		}
	}

	cache.set(cwd, loaded);
	return loaded;
}

/**
 * The load problem for this cwd, returned once. Guards call this so a broken
 * policy is announced rather than quietly degrading to the floor, without every
 * guard announcing it on every tool call.
 *
 * The report is one-shot, so only call it when you can actually deliver it —
 * every guard guards the call with `ctx.hasUI`. Calling it headless would burn
 * the single report on a run with nowhere to show it.
 */
export function takeLoadIssue(cwd: string): string | undefined {
	const { error } = getRules(cwd);
	if (!error || reported.has(cwd)) return undefined;
	reported.add(cwd);
	return error;
}

// --- Path matching ---------------------------------------------------------

function expandTilde(p: string): string {
	if (p === "~") return HOME;
	return p.startsWith("~/") ? join(HOME, p.slice(2)) : p;
}

/** One path segment, with `*` and `?` confined to that segment. */
function segmentRegex(segment: string): RegExp {
	const source = segment.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, "[^/]*").replace(/\?/g, "[^/]");
	return new RegExp(`^${source}$`);
}

function segmentsOf(p: string): string[] {
	return p.split("/").filter((segment) => segment.length > 0);
}

function runMatches(target: string[], pattern: RegExp[], start: number): boolean {
	if (start + pattern.length > target.length) return false;
	return pattern.every((regex, offset) => regex.test(target[start + offset]));
}

/**
 * Does `target` name the path `pattern` describes, or something beneath it?
 *
 * Matching is per path *segment*, which is the point: the old `String.includes`
 * check blocked `.env-example` and `environments/` on a `.env` rule, and would
 * have missed `.env` reached by a different spelling of the same directory. An
 * absolute pattern anchors at the root; a relative one matches a contiguous run
 * of segments anywhere in the path, so `node_modules/` catches it at any depth.
 */
export function matchesPath(target: string, pattern: string, cwd: string): boolean {
	const absoluteTarget = resolve(cwd, expandTilde(target));
	const expanded = expandTilde(pattern.endsWith("/") ? pattern.slice(0, -1) : pattern);
	const targetSegments = segmentsOf(absoluteTarget);
	const patternSegments = segmentsOf(expanded).map(segmentRegex);
	if (patternSegments.length === 0) return false;

	if (isAbsolute(expanded)) return runMatches(targetSegments, patternSegments, 0);

	for (let i = 0; i + patternSegments.length <= targetSegments.length; i++) {
		if (runMatches(targetSegments, patternSegments, i)) return true;
	}
	return false;
}

function firstMatch(target: string, patterns: string[], cwd: string): string | undefined {
	return patterns.find((pattern) => matchesPath(target, pattern, cwd));
}

/** True when an explicit allow rule exempts this path from the zero-access set. */
export function isAllowlisted(target: string, cwd: string): boolean {
	return firstMatch(target, getRules(cwd).rules.zeroAccessAllowPaths, cwd) !== undefined;
}

export function zeroAccessMatch(target: string, cwd: string): string | undefined {
	if (isAllowlisted(target, cwd)) return undefined;
	return firstMatch(target, getRules(cwd).rules.zeroAccessPaths, cwd);
}

export function readOnlyMatch(target: string, cwd: string): string | undefined {
	return firstMatch(target, getRules(cwd).rules.readOnlyPaths, cwd);
}

export function noDeleteMatch(target: string, cwd: string): string | undefined {
	return firstMatch(target, getRules(cwd).rules.noDeletePaths, cwd);
}

// --- Bash command inspection ----------------------------------------------

/**
 * Split a bash command into path-like tokens.
 *
 * Shell metacharacters and quotes are separators, so `cat .env && ls` yields
 * `.env` and `cat "$HOME/.ssh/id_rsa"` yields `$HOME/.ssh/id_rsa`. Tokens are
 * matched individually because the path patterns are segment-anchored — testing
 * them against the whole command string would not line up on segment bounds.
 */
export function commandTokens(command: string): string[] {
	return command
		.split(/[\s;|&<>()"'`]+/)
		.map((token) => token.replace(/^@/, "").replace(/[,:]+$/, ""))
		.filter((token) => token.length > 0);
}

export interface TokenMatch {
	token: string;
	pattern: string;
}

/** First token in `command` that matches one of `patterns`, honouring the allowlist. */
export function commandPathMatch(command: string, patterns: string[], cwd: string): TokenMatch | undefined {
	for (const token of commandTokens(command)) {
		if (isAllowlisted(token, cwd)) continue;
		const pattern = firstMatch(token, patterns, cwd);
		if (pattern) return { token, pattern };
	}
	return undefined;
}

export interface CompiledBashPattern {
	regex: RegExp;
	reason: string;
	ask: boolean;
}

export function bashPatterns(cwd: string): CompiledBashPattern[] {
	return getRules(cwd).rules.bashPatterns.map((entry) => ({
		regex: new RegExp(entry.pattern),
		reason: entry.reason,
		ask: entry.ask === true,
	}));
}

/** Commands that can remove or move a path away from where it is. */
export const DELETE_INDICATORS = [
	/\brm\b/,
	/\bunlink\b/,
	/\bshred\b/,
	/\bmv\b/,
	/\btruncate\b/,
	/\bgit\s+(rm|mv)\b/,
];

/** Commands that can modify a path in place. */
export const WRITE_INDICATORS = [
	/>>?/,
	/\btee\b/,
	/\b(cp|mv|rm|ln|install|truncate|dd)\b/,
	/\bsed\b[^|;]*\s-i/,
	/\b(chmod|chown)\b/,
];

// --- Block text ------------------------------------------------------------

/**
 * Wrap a block reason with an explicit instruction not to route around it.
 *
 * Without this a model treats a block as a failed attempt and retries the same
 * intent by another road — `cat` becomes `head` becomes `python -c`. The guards
 * are a speed bump; the speed bump only works if the driver stops.
 */
export function blockReason(detail: string): string {
	return `${detail}\n\nDo not work around this restriction. Do not retry with a different command, path, tool or encoding to reach the same result. Report this block to the user as stated and ask how they want to proceed.`;
}

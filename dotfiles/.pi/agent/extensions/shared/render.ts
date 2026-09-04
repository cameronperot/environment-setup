/**
 * The shared rendering kit for this directory's tool renderers.
 *
 * Imported by built-in-tool-renderer.ts (`read` `bash` `edit` `write`) and
 * todo.ts, so all five tools share one grammar: a call row, a bounded body
 * behind a gutter, and a status row.
 *
 * Everything here is Pi's own machinery. `renderDiff`, `highlightCode` and
 * `keyHint` are exported by pi-coding-agent, so the diff colouring, the
 * tree-sitter highlighting and the expand hint cost no dependency; only the
 * glyph table and the layout are local.
 *
 * Glyphs are Nerd Font There is one table and no ascii fallback.
 *
 * This directory has no index.ts and no package.json, so Pi's extension
 * discovery (extensions/*.ts and extensions/*\/index.ts, one level, no
 * recursion) does not try to load it as an extension.
 */

import type { Theme, ThemeColor } from "@earendil-works/pi-coding-agent";
import { highlightCode, keyHint } from "@earendil-works/pi-coding-agent";
import type { Component } from "@earendil-works/pi-tui";
import { hyperlink, visibleWidth, wrapTextWithAnsi } from "@earendil-works/pi-tui";
import { homedir } from "node:os";
import { isAbsolute, relative, resolve } from "node:path";

/** Nerd Font glyphs, by role. */
export const SYM = {
	bash: "\u{EBCA}",
	edit: "\u{EA73}",
	write: "\u{EA7F}",
	read: "\u{F15B}",
	todo: "\u{EAB3}",
	success: "\u{F00C}",
	error: "\u{F00D}",
	warning: "\u{F12A}",
	aborted: "\u{F04D}",
	checked: "\u{F14A}",
	unchecked: "\u{F096}",
	branch: "\u{251C}\u{2500}",
	last: "\u{2514}\u{2500}",
	gutter: "\u{2502}",
	dot: " \u{00B7} ",
	ellipsis: "\u{2026}",
} as const;

/** Seti glyphs by the language ids getLanguageFromPath() returns. */
const LANG_ICON: Record<string, string> = {
	typescript: "\u{E628}",
	javascript: "\u{E60C}",
	python: "\u{E606}",
	rust: "\u{E7A8}",
	go: "\u{E627}",
	java: "\u{E738}",
	c: "\u{E61E}",
	cpp: "\u{E61D}",
	csharp: "\u{E7B2}",
	ruby: "\u{E791}",
	php: "\u{E608}",
	swift: "\u{E755}",
	kotlin: "\u{E634}",
	bash: "\u{E795}",
	fish: "\u{E795}",
	html: "\u{E736}",
	css: "\u{E749}",
	json: "\u{E60B}",
	yaml: "\u{E615}",
	toml: "\u{E615}",
	markdown: "\u{E609}",
	sql: "\u{E706}",
	dockerfile: "\u{E7B0}",
	lua: "\u{E620}",
};

const LANG_ICON_DEFAULT = "\u{E612}";

/** Braille spinner, ~8fps at SPINNER_MS. */
const SPINNER = ["\u{28FE}", "\u{28FD}", "\u{28FB}", "\u{28BF}", "\u{287F}", "\u{28DF}", "\u{28EF}", "\u{28F7}"] as const;
const SPINNER_MS = 120;

/**
 * Line budgets. Counted in source rows — see BodyText for why the cap is
 * applied before wrapping rather than after.
 */
export const PREVIEW = {
	BASH: 10,
	WRITE_HEAD: 6,
	READ: 3,
	DIFF_ROWS: 40,
	TODO_ITEMS: 8,
	EXPANDED: 12,
} as const;

const INDENT = "  ";

export type BodyMode = "gutter" | "indent";

/**
 * The body zone: pre-styled rows, wrapped to the render width and prefixed on
 * every visual row.
 *
 * A plain Text cannot do this — it would prefix only the first row of a line
 * that wraps, and the gutter would break up mid-paragraph.
 *
 * Budgets count source rows, not the visual rows they wrap into. That keeps the
 * hidden count exact and, more importantly, keeps the work bounded: the cap is
 * applied before wrapping, so a 2000-line result wraps `limit` rows per render
 * rather than all of them. `hidden` covers rows the caller dropped before
 * construction — `numbered()` does that, since highlighting is the expensive
 * part and only the visible slice is worth highlighting.
 */
export class BodyText implements Component {
	#prefix: string;
	#prefixWidth: number;
	#rows: string[];
	#limit: number | undefined;
	#from: "head" | "tail";
	#hidden: number;
	#more: ((hidden: number) => string) | undefined;
	#cache: string[] | undefined;
	#cacheWidth = -1;

	constructor(options: {
		theme: Theme;
		mode: BodyMode;
		rows: string[];
		limit?: number;
		from?: "head" | "tail";
		hidden?: number;
		more?: (hidden: number) => string;
	}) {
		this.#prefix =
			options.mode === "gutter" ? `${INDENT}${options.theme.fg("borderMuted", SYM.gutter)} ` : INDENT;
		this.#prefixWidth = visibleWidth(this.#prefix);
		this.#rows = options.rows;
		this.#limit = options.limit;
		this.#from = options.from ?? "head";
		this.#hidden = options.hidden ?? 0;
		this.#more = options.more;
	}

	invalidate(): void {
		this.#cache = undefined;
	}

	render(width: number): string[] {
		if (this.#cache !== undefined && this.#cacheWidth === width) return this.#cache;

		let rows = this.#rows;
		let hidden = this.#hidden;
		if (this.#limit !== undefined && rows.length > this.#limit) {
			const dropped = rows.length - this.#limit;
			hidden += dropped;
			rows = this.#from === "tail" ? rows.slice(dropped) : rows.slice(0, this.#limit);
		}

		const inner = Math.max(1, width - this.#prefixWidth);
		const lines: string[] = [];
		for (const row of rows) {
			for (const visual of wrapTextWithAnsi(row, inner)) lines.push(`${this.#prefix}${visual}`);
		}
		if (hidden > 0 && this.#more) {
			const marker = `${this.#prefix}${this.#more(hidden)}`;
			if (this.#from === "tail") lines.unshift(marker);
			else lines.push(marker);
		}

		this.#cache = lines;
		this.#cacheWidth = width;
		return lines;
	}
}

/** `<glyph> <name>  <arg>  <meta · meta>`. The arg and meta come pre-styled. */
export function callRow(theme: Theme, options: { glyph: string; name: string; arg?: string; meta?: string[] }): string {
	let line = `${theme.fg("toolTitle", options.glyph)} ${theme.fg("toolTitle", theme.bold(options.name))}`;
	if (options.arg) line += `  ${options.arg}`;
	return line + metaSuffix(theme, options.meta, "  ");
}

export type StatusKind = "success" | "error" | "warning" | "aborted" | "running";

const STATUS_STYLE: Record<Exclude<StatusKind, "running">, { glyph: string; color: ThemeColor }> = {
	success: { glyph: SYM.success, color: "success" },
	error: { glyph: SYM.error, color: "error" },
	warning: { glyph: SYM.warning, color: "warning" },
	aborted: { glyph: SYM.aborted, color: "warning" },
};

/** `<glyph> <label> · <meta> · <meta>`, indented to sit under the body. */
export function statusRow(
	theme: Theme,
	kind: StatusKind,
	label: string,
	meta?: string[],
	spinnerFrame?: number,
): string {
	let head: string;
	if (kind === "running") {
		const frame = SPINNER[(spinnerFrame ?? 0) % SPINNER.length] ?? SPINNER[0];
		head = `${theme.fg("accent", frame)} ${theme.fg("accent", label)}`;
	} else {
		const style = STATUS_STYLE[kind];
		head = `${theme.fg(style.color, style.glyph)} ${theme.fg(style.color, label)}`;
	}
	return INDENT + head + metaSuffix(theme, meta, theme.fg("dim", SYM.dot));
}

function metaSuffix(theme: Theme, meta: string[] | undefined, lead: string): string {
	// visibleWidth, not length: a styled empty string still carries its escapes.
	const parts = (meta ?? []).filter((part) => visibleWidth(part) > 0);
	if (parts.length === 0) return "";
	return lead + parts.join(theme.fg("dim", SYM.dot));
}

/** `3 lines`, `1 line`. */
export function plural(count: number, noun: string): string {
	return `${count} ${count === 1 ? noun : `${noun}s`}`;
}

/** `… 12 more lines (ctrl+o to expand)`; `earlier` instead of `more` for a tail window. */
export function moreRow(theme: Theme, hidden: number, noun: string, from: "head" | "tail" = "head"): string {
	const qualifier = from === "tail" ? "earlier" : "more";
	const count = `${hidden} ${qualifier} ${hidden === 1 ? noun : `${noun}s`}`;
	const hint = keyHint("app.tools.expand", "to expand");
	return `${theme.fg("dim", `${SYM.ellipsis} ${count}`)} ${theme.fg("dim", "(")}${hint}${theme.fg("dim", ")")}`;
}

/** Project-relative if the path is under cwd, else ~-shortened. */
export function shortPath(cwd: string, path: string): string {
	const absolute = resolve(cwd, path);
	const rel = relative(cwd, absolute);
	if (rel && !rel.startsWith("..") && !isAbsolute(rel)) return rel;
	const home = homedir();
	return absolute.startsWith(`${home}/`) ? `~${absolute.slice(home.length)}` : absolute;
}

/** Middle ellipsis, so the tail of a path survives. */
export function elide(text: string, max: number): string {
	if (max < 4 || visibleWidth(text) <= max) return text;
	const keep = max - 1;
	const head = Math.ceil(keep / 2);
	return `${text.slice(0, head)}${SYM.ellipsis}${text.slice(text.length - (keep - head))}`;
}

/** OSC 8 link to a file, optionally at a line. */
export function fileLink(absolutePath: string, text: string, line?: number): string {
	const suffix = line === undefined ? "" : `?line=${line}`;
	return hyperlink(text, `file://${absolutePath}${suffix}`);
}

export function langIcon(language: string | undefined): string {
	return (language && LANG_ICON[language]) || LANG_ICON_DEFAULT;
}

/**
 * Syntax-highlighted rows with a right-aligned dim line-number gutter, capped at
 * `maxLines` source lines. The cap is applied before highlighting: highlightCode
 * costs tens of milliseconds on a large file, and a body that re-renders on
 * every spinner tick cannot afford to highlight what it will not show.
 */
export function numbered(
	theme: Theme,
	code: string,
	language: string | undefined,
	startLine: number,
	maxLines: number,
): string[] {
	const visible = code.replace(/\n+$/, "").split("\n").slice(0, maxLines).join("\n");
	const highlighted = highlightCode(visible, language);
	const width = Math.max(3, String(startLine + highlighted.length - 1).length);
	return highlighted.map((line, i) => `${theme.fg("dim", String(startLine + i).padStart(width, " "))} ${line}`);
}

/**
 * Per-row timing state. Pi shares `context.state` between the call and result
 * slots of one tool row, which is what lets the result read a clock the call
 * started. Lifecycle copied from Pi's own bash renderer.
 */
export interface TimedState {
	startedAt?: number;
	endedAt?: number;
	interval?: ReturnType<typeof setInterval>;
	frame?: number;
}

interface TimedContext {
	state: TimedState;
	executionStarted: boolean;
	isError: boolean;
	invalidate(): void;
}

export function markStarted(context: TimedContext): void {
	if (context.executionStarted && context.state.startedAt === undefined) {
		context.state.startedAt = Date.now();
		context.state.endedAt = undefined;
	}
}

/** Starts the spinner/elapsed ticker while partial; settles and clears it after. */
export function markSettled(context: TimedContext, isPartial: boolean): void {
	const state = context.state;
	if (state.startedAt !== undefined && isPartial && !context.isError && state.interval === undefined) {
		state.interval = setInterval(() => {
			state.frame = (state.frame ?? 0) + 1;
			context.invalidate();
		}, SPINNER_MS);
	}
	if (!isPartial || context.isError) {
		state.endedAt ??= Date.now();
		if (state.interval !== undefined) {
			clearInterval(state.interval);
			state.interval = undefined;
		}
	}
}

export function elapsed(state: TimedState): string {
	if (state.startedAt === undefined) return "";
	const ms = (state.endedAt ?? Date.now()) - state.startedAt;
	if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
	const minutes = Math.floor(ms / 60_000);
	return `${minutes}m${Math.floor((ms % 60_000) / 1000)}s`;
}

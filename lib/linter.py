"""Chapter linter for Svenska per se illustrata.

Enforces the vocabulary budget contract from staircase.yaml:

  - every token in a chapter's prose must resolve to a lexicon lemma that is
    unlocked (introduced in an earlier chapter), or introduced THIS chapter as
    focus / stretch / freebie, or a proper noun  -> otherwise ERROR
  - focus lemmas must recur >= 3x across >= 2 prose blocks (waivable with a
    'restraint' justification in the chapter file)
  - stretch count must respect the arc cap
  - new-lemma density above the warn threshold -> WARNING

Usage:
    python -m lib.linter chapters/kap01.yaml [chapters/kap02.yaml ...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT / "lib" / "lexicon.yaml"
STAIRCASE_PATH = ROOT / "staircase.yaml"

WORD_RE = re.compile(r"[a-zA-ZåäöÅÄÖéÉüÜøØæÆ]+(?:-[a-zA-ZåäöÅÄÖéÉüÜøØæÆ]+)*")


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Lexicon:
    def __init__(self, data: dict):
        self.lemmas: dict[str, dict] = data.get("lemmas", {})
        self.proper: dict[str, dict] = data.get("proper", {})
        # surface form (lowercased) -> set of lemma keys
        self.surface: dict[str, set[str]] = {}
        for key, entry in self.lemmas.items():
            forms = entry.get("forms") or [key]
            for form in forms:
                self.surface.setdefault(form.lower(), set()).add(key)
        # proper-noun surfaces kept separate (matched case-insensitively too,
        # since sentence-initial lowercase words must not collide with names)
        self.proper_surface: dict[str, set[str]] = {}
        for key, entry in self.proper.items():
            forms = entry.get("forms") or [key]
            for form in forms:
                self.proper_surface.setdefault(form.lower(), set()).add(key)

    def lookup(self, token: str) -> set[str]:
        return self.surface.get(token.lower(), set())

    def lookup_proper(self, token: str) -> set[str]:
        return self.proper_surface.get(token.lower(), set())


def iter_prose_blocks(chapter: dict):
    """Yield (section_index, block_index, text) for every prose block,
    including the chapter's repetition reading (if any)."""
    for si, section in enumerate(chapter.get("lasstycken", [])):
        for bi, block in enumerate(section.get("block", [])):
            text = block.get("text", "")
            if text:
                yield si, bi, text
    rep = chapter.get("repetition")
    if rep:
        for bi, block in enumerate(rep.get("block", [])):
            text = block.get("text", "")
            if text:
                yield "R", bi, text


def lint_lasebok(path: Path, lex: Lexicon, data: dict) -> tuple[str, list[str]]:
    """Lint a läsebok text: zero new words — every token must be unlocked at
    its `efter_kapitel` level (intro <= N). No focus/stretch of its own."""
    n = data["efter_kapitel"]
    errors: list[str] = []
    token_count = 0
    unknown: dict[str, int] = {}
    off_budget: dict[str, int] = {}
    for block in data.get("block", []):
        for token in WORD_RE.findall(block.get("text", "")):
            token_count += 1
            lemmas = lex.lookup(token)
            if not lemmas:
                if len(token) == 1 or lex.lookup_proper(token):
                    continue
                unknown[token.lower()] = unknown.get(token.lower(), 0) + 1
                continue
            if not any((lex.lemmas[lm].get("intro") or 0) <= n for lm in lemmas):
                key = "/".join(sorted(lemmas))
                off_budget[key] = off_budget.get(key, 0) + 1
    for token, count in sorted(unknown.items()):
        errors.append(f"unknown token '{token}' x{count}")
    for key, count in sorted(off_budget.items()):
        errors.append(f"off-budget lemma '{key}' x{count} (taught AFTER kap {n})")
    status = "FAIL" if errors else "PASS"
    lines = [
        f"== {path.name} — läsebok '{data.get('titel', '?')}' (efter kap {n}) — {status}"
    ]
    lines += [f"  [ERROR] {e}" for e in errors]
    lines.append(f"  [info]  {token_count} tokens, zero new words required")
    return status, lines


def lint_chapter(path: Path, lex: Lexicon, staircase: dict) -> tuple[str, list[str]]:
    chapter = load_yaml(path)
    if "efter_kapitel" in chapter:
        return lint_lasebok(path, lex, chapter)
    n = chapter["kapitel"]
    arc = chapter.get("arc")
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    focus = list(chapter.get("fokus", []))
    stretch = list(chapter.get("stretch", []))
    restraint = chapter.get("restraint", {}) or {}

    # --- declared-list consistency against the lexicon ---
    for tier_name, lemmas in (("fokus", focus), ("stretch", stretch)):
        for lemma in lemmas:
            entry = lex.lemmas.get(lemma)
            if entry is None:
                errors.append(f"{tier_name} lemma '{lemma}' missing from lexicon")
                continue
            if entry.get("intro") != n:
                errors.append(
                    f"{tier_name} lemma '{lemma}' has lexicon intro={entry.get('intro')}, expected {n}"
                )

    # --- stretch cap ---
    caps = staircase.get("rules", {}).get("stretch_cap_by_arc", {})
    cap = caps.get(arc)
    if cap is not None and len(stretch) > cap:
        errors.append(f"stretch count {len(stretch)} exceeds arc {arc} cap {cap}")

    # --- tokenize prose, check budget ---
    unlocked_ok = 0
    token_count = 0
    unknown: dict[str, int] = {}
    off_budget: dict[str, int] = {}
    # lemma -> total hits, and set of block ids where it appears
    hits: dict[str, int] = {}
    contexts: dict[str, set] = {}

    intro_this = set(focus) | set(stretch)

    for si, bi, text in iter_prose_blocks(chapter):
        for token in WORD_RE.findall(text):
            token_count += 1
            lemmas = lex.lookup(token)
            if not lemmas:
                if len(token) == 1:
                    # bare letters used as objects ("Å är en bokstav") — not vocabulary
                    continue
                if lex.lookup_proper(token):
                    continue
                unknown[token.lower()] = unknown.get(token.lower(), 0) + 1
                continue
            allowed = {
                lm for lm in lemmas
                if (lex.lemmas[lm].get("intro") or 0) < n or lm in intro_this
                or (lex.lemmas[lm].get("intro") == n and lex.lemmas[lm].get("tier") == "freebie")
            }
            if not allowed:
                key = "/".join(sorted(lemmas))
                off_budget[key] = off_budget.get(key, 0) + 1
                continue
            unlocked_ok += 1
            for lm in allowed:
                hits[lm] = hits.get(lm, 0) + 1
                contexts.setdefault(lm, set()).add((si, bi))

    for token, count in sorted(unknown.items()):
        errors.append(f"unknown token '{token}' x{count} — add to lexicon or cut")
    for key, count in sorted(off_budget.items()):
        errors.append(f"off-budget lemma '{key}' x{count} (intro is in a LATER chapter)")

    # --- focus recurrence ---
    meta = staircase.get("meta", {})
    rec_min = meta.get("focus_recurrence_min", 3)
    ctx_min = meta.get("focus_contexts_min", 2)
    for lemma in focus:
        h = hits.get(lemma, 0)
        c = len(contexts.get(lemma, set()))
        if h < rec_min or c < ctx_min:
            if lemma in restraint:
                infos.append(
                    f"focus '{lemma}' {h}x/{c} contexts — waived: {restraint[lemma]}"
                )
            else:
                warnings.append(
                    f"focus '{lemma}' recurs {h}x in {c} contexts (need >= {rec_min}x in >= {ctx_min})"
                )

    # --- stretch must appear at least once ---
    for lemma in stretch:
        if hits.get(lemma, 0) < 1:
            warnings.append(f"stretch '{lemma}' never appears in prose")

    # --- density ---
    density_warn = staircase.get("rules", {}).get("density_warn", 0.05)
    if token_count:
        density = len(intro_this) / token_count
        if density > density_warn:
            warnings.append(
                f"new-lemma density {density:.3f} > {density_warn} ({len(intro_this)} new / {token_count} tokens)"
            )
        infos.append(
            f"{token_count} tokens; {len(focus)} focus + {len(stretch)} stretch; density {len(intro_this)/token_count:.3f}"
        )

    # --- focus count range ---
    lo, hi = meta.get("new_focus_per_chapter", [8, 12])
    if not (lo <= len(focus) <= hi):
        warnings.append(f"focus count {len(focus)} outside plan range [{lo}, {hi}]")

    status = "FAIL" if errors else ("REVIEW" if warnings else "PASS")
    lines = [f"== {path.name} — kap {n} ({chapter.get('titel', '?')}) — {status}"]
    lines += [f"  [ERROR] {e}" for e in errors]
    lines += [f"  [WARN]  {w}" for w in warnings]
    lines += [f"  [info]  {i}" for i in infos]
    return status, lines


def book_report() -> int:
    """Whole-book exposure report: the cross-chapter recycling metric.

    This is the axis that matters most in the per-se method: a word met once
    and never again is not taught. Run after any prose change:
        python -m lib.linter --book
    """
    lex = Lexicon(load_yaml(LEXICON_PATH))
    hits: dict[str, int] = {}
    chapters_seen: dict[str, set] = {}
    total_tokens = 0
    for path in sorted(ROOT.glob("chapters/kap*.yaml")):
        chapter = load_yaml(path)
        n = chapter["kapitel"]
        seen_here = set()
        for _si, _bi, text in iter_prose_blocks(chapter):
            for token in WORD_RE.findall(text):
                total_tokens += 1
                for lm in lex.lookup(token):
                    hits[lm] = hits.get(lm, 0) + 1
                    seen_here.add(lm)
        for lm in seen_here:
            chapters_seen.setdefault(lm, set()).add(n)

    print(f"== BOOK REPORT: {total_tokens} prose tokens ==")
    for tier in ("focus", "stretch", "freebie"):
        keys = [k for k, e in lex.lemmas.items() if e.get("tier") == tier]
        exp = sorted((hits.get(k, 0), k) for k in keys)
        under = [(c, k) for c, k in exp if c < 3]
        orphans = [k for k in keys if len(chapters_seen.get(k, set())) <= 1]
        med = exp[len(exp) // 2][0] if exp else 0
        print(
            f"{tier}: {len(keys)} lemmas | median exposures {med} | "
            f"<3 exposures: {len(under)} | single-chapter: {len(orphans)}"
        )
        if under:
            print("  under-exposed: " + ", ".join(f"{k}({c})" for c, k in under[:40]))
        if tier == "focus" and orphans:
            by_ch = sorted(orphans, key=lambda k: (lex.lemmas[k].get("intro", 0), k))
            print("  single-chapter focus: " + ", ".join(
                f"{k}[{lex.lemmas[k].get('intro')}]" for k in by_ch))
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--book":
        return book_report()
    lex = Lexicon(load_yaml(LEXICON_PATH))
    staircase = load_yaml(STAIRCASE_PATH)
    worst = "PASS"
    order = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    for arg in argv:
        for path in sorted(Path().glob(arg)) or [Path(arg)]:
            status, lines = lint_chapter(Path(path), lex, staircase)
            print("\n".join(lines))
            if order[status] > order[worst]:
                worst = status
    return 0 if worst != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

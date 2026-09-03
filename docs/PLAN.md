# Build plan & status — Svenska per se illustrata, Del I

*(Design rationale lives in [DESIGN.md](DESIGN.md); this file tracks the phased
build and what a future session needs to know to continue.)*

## Phases

| Phase | Scope | Status |
|---|---|---|
| **0. Design** | Curriculum design (DESIGN.md), 30-chapter staircase (staircase.yaml), cast (characters.yaml), repo reorganized (Moomin project deleted — lives in git history), LLPSI PDFs moved to `reference/` | ✅ done |
| **1. Infrastructure** | Lexicon format (lib/lexicon.yaml), linter (lib/linter.py), build pipeline (tools/build_reader.py), web reader SPA (web/) with margin notes, word-tap glosses (SV-first, EN behind toggle), Web-Speech-API audio (▶/🐢/whole chapter), interactive Övning A/B (auto-check) + C (model answers), uttal boxes | ✅ done |
| **2. Arc A** (kap 1–6) | Hemma i Sjövik — all six chapters written, linted PASS, rendering verified in browser | ✅ done |
| **3. Arc B** (kap 7–12) | Dagar och djur (reflexives, shopping, farm, modals, body, the year) | ✅ done |
| **4. Arc C** (kap 13–18) | Skola och tid (klockan, V2, **preteritum**, komparation, perfekt) | ✅ done |
| **5. Arc D** (kap 19–24) | Ut i världen (futurum, definite adjective, BIFF, som, pluskvamperfekt) | ✅ done |
| **6. Arc E** (kap 25–30) | Berättelser och fester (folktales, passive, particle verbs, wedding finale) | ✅ done — **all 30 chapters PASS; 654 lemmas, 76 proper nouns** |
| **6b. Audit revision pass** | Post-audit fixes: (1) **recycling pass** — 29 zero-new-words repetition readings (kap 2–30) targeting the orphan list; prose volume 14.4k → 17.1k tokens; single-chapter focus lemmas 106 → 12 (all kap 29–30, structurally final); `--book` exposure report added to linter; (2) **honest scope** — docs now say A2 / ~420 content lemmas; (3) **Arc A sealed** — all kap 1–6 glosses rewritten self-contained; bilingual guide page ("Så använder du boken") teaches chrome words once; (4) **Arc A illustrations** — six hand-authored labeled SVGs (map of Norden, family tree, house cutaway, birch drama, colored possessions, Sjövik route map), wired into build + reader; (5) **dead machinery removed** — grammar_step fields, stale freebies block, per-chapter freebies lists cut from staircase.yaml | ✅ done |
| **6c. Läseboken** | 10 supplementary readings (`lasebok/lb01–lb10`), each pegged to an `efter_kapitel` level and linted **zero-new-words** against it: five Sjövik slice-of-life texts (Ludde's day, the farm morning, Elsa in the shop, fru Lind's day, puppy-Bill) and four folklore texts retelling common motifs in book vocabulary (the farm tomte, Näcken in the lake, the troll who fled the church bells) plus the finale "Kattens sak" (Misse's secret night, addressed to the reader). Tomten/Näcken enter as proper nouns; ~3.6k extra prose tokens. Rendered as a "Läseboken" section on the landing page with its own reading view + Förra/Nästa. | ✅ done |
| **7. Uttalet module** | Standalone pronunciation intro before kap 1 (alphabet + vowel length + listening contrasts), Ordlista view (searchable cumulative index) | ⬜ |
| **8. Assets — pipeline** | ✅ Built and dry-run-verified, generation pending an API key: `tools/generate_audio.py` (Gemini 2.5 Pro TTS batch; 558 clips = 343 blocks + 215 uttal chips ≈ 136 min ≈ $2; per-character voices + delivery styles in `tools/voice_map.yaml`; content-hashed filenames embedded by build_reader make regeneration automatic and exact) and `tools/generate_images.py` (24 chapter illustrations kap 7–30, shared style+cast preamble for consistency; kap 1–6 keep hand SVGs). `_batch.py` restored from Moomin history. App plays clips with playbackRate for slow speed and falls back to speech synthesis per missing file (verified). Pages workflow + .nojekyll added; .gitignore now commits generated assets (Pages serves repo contents). Anki export still ⬜. | 🔶 ready to run |
| **9. Final sweep** | Read kap 1→30 in order; motif/continuity check; coverage stats; deploy (GitHub Pages) | ⬜ |

## Working loop (per chapter)

1. Draft prose per the staircase entry (grammar foregrounded ≥6×, story first —
   never bend Swedish to fit the budget; bend the scene instead).
2. Add every new lemma to `lib/lexicon.yaml` with **all surface forms**, Swedish
   gloss, English emergency gloss, `intro:` chapter, tier.
3. `python -m lib.linter chapters/kapNN.yaml` → fix ERRORs, judge WARNs.
4. Write GRAMMATIK (Swedish, tables), UTTAL box (chapter words only), Övning
   A (forms, `{answer}` cloze syntax, `|` for alternatives), B (vocab cloze
   with word bank in instruction), C (questions + model answers).
5. `python tools/build_reader.py`; spot-check in browser (launch config
   `reader`, port 8321).

## Editorial rules discovered while writing Arc A

- **Hooks must stay in budget**: end-of-chapter teasers may not use the next
  chapter's vocabulary (kap 4's hook was rewritten for this). Tease with
  proper nouns, unlocked words, or the bare kapitel number.
- **Freebies are added to the lexicon when first used**, not in advance —
  the staircase freebie lists are intent, the lexicon is truth.
- Names ending in -s (Nils, Anders) are a deliberate genitive teaching device.
- "Familjen Berg" appears from kap 2 with a margin preview note (definite form
  is taught kap 3) — Ørberg-style morphology preview, allowed in margins.
- The linter ignores single-letter tokens (alphabet-as-object sentences) but
  still matches "ö"/"i" against the lexicon first.
- Dialogue blocks drop inquit verbs out of prose; if frågar/svarar are focus
  vocab they must be woven into narration deliberately (kap 4 lesson).
- Grammar metalanguage in **prose** stays at the level already taught
  ("subjektet" was cut from kap 5 prose; fine in GRAMMATIK sections).

## Post-book notes (after writing kap 7–30)

- The staircase's provisional vocab plans drifted during writing (as intended —
  chapter files + lexicon are truth). Notable moves: sitta→13, göra→7, förstå→14,
  arbeta→23, bli→24, börja/sluta→25, hjälpa→27 (stretch), tid→16, gång→18.
  "rädda" (kap 28 plan) was cut — the crew self-rescues, no rescue verb needed.
- Cast timeline settled: proposal happens kap 29 (evening by the lake), wedding
  kap 30 (August). Elsa's mother runs the shop (fru Ek) — set up in kap 8, pays
  off in kap 19 (feeding Misse) and kap 21 (the quarrel).
- Embedded folktales (kap 25–26) are original compositions: the lonely troll
  (Tuva), and Fågel-Pelle — an Icarus who listens and lives (morfars morfar!).
- Traditional proverbs used in kap 29 are all built from taught vocabulary
  (borta bra men hemma bäst; den som väntar på något gott …).
- Kap 30 closes the loop: Anders' speech reviews the book, the last block
  mirrors kap 1 and addresses the reader directly.

## Deferred decisions / notes

- **vatten** was pulled forward to kap 6 (bridge scene needs it); kap 20's
  vocab plan should drop it.
- **snäll** moved kap 4 → kap 5; **glad** deferred to kap 7; **tåg/station/gata**
  came early as kap 6 stretch (train tease pays off in kap 19).
- Numbers: 1–5 freebies kap 1, 6–12 kap 2; teens/tens due kap 8 (priser),
  hundra/tusen kap 17.
- Chapter-play audio uses speechSynthesis; when Gemini TTS assets are added,
  `speak()` in web/app.js is the single seam to extend (check for an audio
  file first, fall back to synthesis).
- Exercise progress is not yet persisted per-item (only last-read chapter);
  consider localStorage per övning when Arc C lands.
- `.gitignore` excludes `reference/` (the LLPSI PDFs) — method reference only.

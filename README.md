# Svenska per se illustrata — Del I: Familjen Berg

A Swedish graded reader and interactive web course built on the method of Hans
Ørberg's *Lingua Latina per se Illustrata*: Swedish taught **entirely in Swedish**,
made comprehensible by context, pictures, cognates, controlled vocabulary, and
Swedish-language marginal notes — never by translation.

30 chapters follow the Berg family in the small lakeside town of Sjövik through a
Swedish year — from the map of Norden (kap 1) to a wedding by the lake (kap 30) —
carrying a zero-Swedish English speaker to a solid A2: ~420 content lemmas plus
~230 function words, every content word recycled across chapters (each chapter
ends with a *repetition* reading built from zero new words). B1 is the job of a
future Del II.

**Full design rationale:** [docs/DESIGN.md](docs/DESIGN.md)
**Build status / roadmap:** [docs/PLAN.md](docs/PLAN.md)

## Layout

```
├── docs/
│   ├── DESIGN.md          curriculum design (method, cast, staircase rationale)
│   └── PLAN.md            phased build plan + current status
├── staircase.yaml         30-chapter grammar+vocab plan, budget rules, canon beats
├── characters.yaml        cast, voices, register discipline
├── chapters/              kap01.yaml … kap30.yaml — the book itself
├── lasebok/               lb01.yaml … lb10.yaml — supplementary readings
│                          (folktales + Sjövik slice-of-life; ZERO new words,
│                          each pegged to a chapter level — the Colloquia
│                          Personarum / Fabulae Syrae analogue)
├── lib/
│   ├── lexicon.yaml       lemma → inflected surface forms (the morphology ledger)
│   └── linter.py          chapter validator (vocab budget, recurrence, density)
├── tools/
│   └── build_reader.py    chapters/*.yaml → web/dist/chapters/*.json
├── web/                   the reader SPA (no build step; static hosting)
└── reference/             the LLPSI PDFs (method reference; not course content)
```

## Workflow

```bash
# validate a chapter
python -m lib.linter chapters/kap01.yaml

# validate everything (läsebok texts are checked against their efter_kapitel level)
python -m lib.linter chapters/kap*.yaml lasebok/lb*.yaml

# whole-book exposure report (the cross-chapter recycling metric)
python -m lib.linter --book

# rebuild reader data
python tools/build_reader.py

# serve locally
cd web && python -m http.server 8000
```

## Chapter anatomy

Each `chapters/kapNN.yaml` holds one chapter:

- `pedagogy` — grammar focus, uttal focus, vocab tiers (from `staircase.yaml`)
- `lasstycken` — 2–3 reading sections of prose blocks (`narration` / `dialogue`),
  each block optionally carrying Ørberg-style `margin` notes
- `repetition` — an extra reading with **zero new words**: only unlocked
  vocabulary, deliberately recycling words from earlier chapters (the
  Colloquia-Personarum move — recycling is the method)
- `grammatik` — the chapter's paradigms, in Swedish, as table data
- `ovningar` — ÖVNING A (form blanks), B (vocab cloze), C (comprehension questions)
- `glossary` — Swedish-first gloss per new lemma (+ optional English emergency exit)

Chapters 1–6 also carry hand-authored labeled SVG illustrations
(`web/dist/images/kapNN.svg` — source files, tracked in git), and the reader's
landing page opens with a bilingual guide ("Så använder du boken") that teaches
the book's chrome words and symbols once.

Audio: the web reader plays every prose block and word via the browser's Swedish
speech synthesis out of the box; pre-generated clips in `web/dist/audio/` take
precedence when present. `build_reader.py` embeds a content-hashed clip path
per block (sha1 of voice + style + text, cast in `tools/voice_map.yaml`), so
editing any text automatically invalidates exactly its own clips.

```bash
# audio (Gemini 2.5 Pro TTS; ~$2 for the whole book in batch mode)
python tools/generate_audio.py --dry-run     # queue + cost, no API calls
python tools/generate_audio.py --sample kap01  # audition one chapter, sync
python tools/generate_audio.py --batch       # render everything missing

# illustrations kap 7-30 (kap 1-6 keep their hand-authored SVGs)
python tools/generate_images.py --dry-run
python tools/generate_images.py --batch
```

Both need `GEMINI_API_KEY` in the environment and are idempotent: missing
files are the queue, so re-running after edits renders only what changed.
Publishing: `.github/workflows/pages.yml` deploys `web/` to GitHub Pages on
push (generated mp3/jpg assets are committed — Pages serves repo contents).

## Lineage

This repo previously held ムーミン谷 per se Illustrata, a Japanese Moomin graded
reader whose pipeline (YAML chapters → linter → JSON → static reader) this project
inherits in spirit. The Moomin project lives on in git history prior to the
Swedish reboot commit.

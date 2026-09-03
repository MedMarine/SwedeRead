# Svenska per se illustrata — Design Document

**Del I: Familjen Berg** — a Swedish graded reader + interactive web course in the
spirit of Hans Ørberg's *Lingua Latina per se Illustrata* (LLPSI): the language is
taught **entirely in Swedish**, made comprehensible by pictures, context, cognates,
controlled repetition, and Swedish-language marginal notes — never by translation.

---

## 1. Why the LLPSI method fits Swedish unusually well

Ørberg's central bet is that a text can *carry its own meaning* if every new element
is either (a) transparent from world knowledge (maps, names, numbers), (b) inferable
from pictures and contrast (`stor ↔ liten`), or (c) built from parts already taught.
Latin had to lean hard on (a) and (b). **Swedish gets (c) almost free**, because for
an English speaker the cognate density is enormous:

- Direct cognates: *hus, land, man, hand, arm, finger, vinter, sommar, kan, vill,
  komma, dricka, äta (eat), bok, fisk, katt, gås, ung, lång, kall, varm* …
- Transparent internationalisms: *familj, park, station, telefon, musik, kafé* …
- Systematic sound-shifts an attentive reader picks up in weeks: *sk-/sh-*
  (skepp/ship), *-g/-y* (dag/day, väg/way), *st-* (sten/stone), *k/ch* (kyrka/church).

So a per-se-illustrata Swedish text can be **more natural and less stilted** than the
Latin original from chapter 1, and the learner's inference engine gets constant wins.

What Swedish has that Latin *didn't* need: **sound**. Latin was read; Swedish must be
heard. Swedish orthography is only semi-transparent (sj-/tj- sounds, k/g softening,
long vs. short vowels, pitch accent). Therefore this course is **audio-first**: every
sentence in the book is playable, every word is tappable-to-hear, and each chapter
spotlights one pronunciation pattern (see §6).

## 2. Target learner and outcome

- **Learner:** adult English speaker, zero Swedish. No companion book, no teacher.
- **Outcome after Del I (30 chapters):** a solid A2. Comfortable reading simple
  native prose, able to follow slow clear speech, in command of the full core
  grammar of the modern language (all tenses, both word orders, definiteness,
  adjective agreement, particle verbs, passive). Vocabulary: ~420 content lemmas
  (focus + stretch) plus ~230 function words — chosen by frequency and story
  utility, and *recycled*: every chapter ends with a zero-new-words repetition
  reading, and the linter's `--book` report tracks whole-book exposure.
- **Explicit non-goals of Del I:** B1+ vocabulary breadth, formal/bureaucratic
  register, news prose, dialectal variation. (Reserved for Del II, see §9.)

## 3. Method rules (the Ørberg contract)

1. **Swedish only.** Prose, margin notes, grammar sections, exercise instructions —
   all in Swedish. Grammar terminology uses the Swedish school terms (*substantiv,
   verb, bestämd form, presens, preteritum*), which are themselves near-cognates.
2. **Nothing unexplained.** Every new word is introduced where context, picture,
   margin note (`= synonym`, `↔ motsats`, small illustration, morphology callout),
   or transparent cognacy makes it understandable. The linter enforces the budget.
3. **Controlled introduction, forced recurrence.** ~8–12 new lemmas per chapter as
   *focus* (must recur ≥3× in ≥2 contexts), a small *stretch* allowance glossed in
   the margin, everything else must already be unlocked. One grammar focus per
   chapter, drilled ≥6× in varied sentences.
4. **Story, not specimen sentences.** A continuous cast, real plot beats, motifs
   that return. Grammar is load-bearing in the story (the storm chapter *needs*
   past tense; the Stockholm chapter *needs* definite adjectives).
5. **The learner self-checks.** Each chapter ends with GRAMMATIK (paradigms in
   Swedish, Ørberg's *Grammatica Latina*) and three exercises:
   - **ÖVNING A** — morphology: fill in the ending/form (auto-checked).
   - **ÖVNING B** — vocabulary: cloze with the chapter's words (auto-checked).
   - **ÖVNING C** — comprehension questions, answered in Swedish (model answers
     revealed on demand).
6. **English is an emergency exit, not a crutch.** Word-tap shows the Swedish
   gloss/margin note first; a second tap reveals an English hint. Off by default
   in settings ("nödutgång").

## 4. The cast and the world

Modern Sweden, real geography (chapter 1 is literally the map of Norden, as
Ørberg's chapter 1 was the map of the Roman Empire), plus one invented small town.

**Sjövik** — a small town by a lake in Småland. (The name itself is a lesson:
*sjö* + *vik*.)

| Person | Roll | Funktion i boken |
|---|---|---|
| **Anders Berg** | pappa, snickare | practical vocabulary, workshop, building |
| **Karin Berg** | mamma, läkare | body/health chapters, calm register |
| **Oskar Berg** | son, 12 år | the *puer improbus* — mischief drives plots |
| **Nils Berg** | son, 10 år | the careful one; reads, counts, asks questions |
| **Astrid Berg** | dotter, 7 år | songs, diminutives, child register |
| **Ludde** | hund | motion verbs, imperatives ("Sitt! Kom hit!") |
| **Misse** | katt | ch7 companion; contrast with Ludde |
| **Farmor Ingrid** | Anders mor, bor i Stockholm | letters, the city arc, formal-ish register |
| **Morfar Sven** | Karins far, bonde utanför Sjövik | farm/animal chapters, seasons, proverbs |
| **Lasse** | Anders lillebror, sjöman | the sea chapters; the romance subplot |
| **Maria** | Lasses flickvän, bor i Stockholm | romance subplot → the wedding finale |
| **Elsa Ek** | grannflicka, Oskars vän | dialogue partner, the quarrel chapter |
| **Fru Lind** | lärare i Sjöviks skola | school chapters, classroom register |
| **Herr Holm** | granne med stor hund | the "Akta hunden!" chapter |

Recurring motifs: **sjön** (the lake — opening and closing image), **kartan**
(ch1's map returns in ch19's journey and ch30's guests), **brev** (letters knit
Sjövik to Stockholm), **årstiderna** (the Swedish year structures the arcs).

## 5. The staircase — 30 chapters, 5 arcs

The grammar sequence is chosen so that (a) each step is *usable immediately* in
story, (b) Swedish-specific cruxes get their own dedicated chapters (definiteness,
V2, BIFF, particle verbs, *sin*, the clock), and (c) tense arrives mid-book exactly
where the narrative starts needing to look backward.

### Arc A — Hemma i Sjövik (kap 1–6): the world, the family, the house

| Kap | Titel | Grammatikfokus | Nyckelmoment |
|---|---|---|---|
| 1 | **Sverige och Norden** | *är/ligger*; en/ett; predicative adjective agreement (stor/stort/stora); *inte*; questions (Var? Vad? Är…? Ligger…?); i/på | The map chapter. Section 3 "Bokstäver och siffror" introduces the alphabet, **å ä ö**, and numbers as self-referential objects, exactly as Ørberg did letters and numerals. |
| 2 | **Familjen Berg** | *heter*; vem?/vems?; genitive -s; han/hon/de; hur många?; numbers 1–10; first plurals (-or, -ar, zero) | Cast introduced by portrait + family tree. |
| 3 | **Huset vid sjön** | **bestämd form singular** (-en/-et); *det finns*; den/det as pronouns; under/över/vid/bakom/framför | Room-by-room tour; definiteness taught by pointing: *ett kök → köket*. |
| 4 | **En stygg pojke** | presens of action verbs (-ar/-er/strong); object pronouns (mig/dig/honom/henne/oss/er/dem); varför? – därför att | Oskar teases Astrid; she cries; mamma intervenes. |
| 5 | **Vems är bollen?** | possessives (min/mitt/mina …); **sin/sitt/sina vs. hans/hennes** | Ownership quarrels make *sin* load-bearing: *Oskar tar sin boll / hans boll*. |
| 6 | **Vägen till skolan** | motion verbs (går, åker, kommer); **här/hit, där/dit, hemma/hem, inne/in, ute/ut**; till/från/genom/över; bestämd form plural (-na) | The location/direction adverb pairs — a uniquely Swedish chapter. |

### Arc B — Dagar och djur (kap 7–12): daily life, commerce, the farm, the body

| Kap | Titel | Grammatikfokus | Nyckelmoment |
|---|---|---|---|
| 7 | **Astrid och Misse** | ger/får/visar/tar (transfer verbs, indirect objects); **reflexives** (tvättar sig, lägger sig) | Astrid and the cat's day. |
| 8 | **I affären** | den här/det här/de här; hur mycket kostar…?; numbers 10–100; *vill ha* | Money, buying, cheap/expensive. |
| 9 | **På morfars gård** | någon/något/några ↔ ingen/inget/inga; more plurals; alla/varje | The farm; *ett lamm är borta!* mini-mystery. Sheep = *får* (delicious homograph with the verb, exploited in the margin). |
| 10 | **Djur och människor** | **modals I: kan, vill** + bare infinitive; verb catalogue (flyga, simma, springa, leva) | Fåglar kan flyga; fiskar kan simma; människor kan tala. The classification chapter. |
| 11 | **Kroppen** | **modals II: måste, får (inte), behöver**; *har ont i* + kroppsdel; känner sig | Body parts; Oskar fakes illness, Karin the doctor is not fooled. |
| 12 | **Året och månaderna** | ordinals; dates; months/weekdays/seasons; time expressions (på våren, i januari, om sommaren) | The Swedish year. Sets the seasonal clock that the rest of the book runs on. |

### Arc C — Skola och tid (kap 13–18): routine, school, weather, **the past tense**

| Kap | Titel | Grammatikfokus | Nyckelmoment |
|---|---|---|---|
| 13 | **En ny dag** | **klockan** (halv åtta, kvart i/över); daily-routine verbs with particles/reflexives (vaknar, stiger upp, klär på sig) | The famous Swedish clock gets a full chapter. |
| 14 | **I skolan** | fronted adverbial → **inversion (V2)** taught explicitly; school vocabulary; *lär sig* | Fru Lind's classroom; "På svenska heter det…" — the book becomes self-aware. |
| 15 | **Ovädret** | **preteritum I**: weak -ade; var/hade; det-expletives (det regnar, det blåser) | A storm hits Sjövik; the narrative looks back for the first time: *I går sken solen. I dag regnar det.* |
| 16 | **Vad hände i går?** | **preteritum II**: -de/-te/-dde + core strong verbs (gick, kom, såg, fick, åt, drack, sa) | Retelling the storm day; sequencing words (först, sedan, till slut). |
| 17 | **Vem har mest?** | **komparation** (större/störst, mer/mest, bättre/bäst); än; large numbers | Sibling comparisons; counting saved kronor. |
| 18 | **Ett brev till farmor** | **perfekt** (har + supinum); någonsin/aldrig/redan/just | The children write to farmor: what has happened this year. Letter register. |

### Arc D — Ut i världen (kap 19–24): Stockholm, subordination, people

| Kap | Titel | Grammatikfokus | Nyckelmoment |
|---|---|---|---|
| 19 | **Resan till Stockholm** | **futurum** (ska, kommer att, tänker); travel vocabulary | The map from ch1 comes off the wall. Train through Sweden = live geography. |
| 20 | **Hos farmor** | **bestämd form av adjektiv** (den stora staden, det gamla huset, de höga husen) | Describing Stockholm demands double definiteness — the milestone chapter. |
| 21 | **Bråket** | att-clauses; **bisatsordföljd / BIFF** (…att han **inte** gjorde det); säger/tror/vet/tycker | Oskar and Elsa quarrel; who said what — reported speech makes BIFF load-bearing. |
| 22 | **Akta hunden!** | **imperativ** (full paradigm); får/får inte (permission); vågar; rädd för | Herr Holm's enormous dog. Warnings, commands, courage. |
| 23 | **Lasse och Maria** | **relative som**-clauses; gift/förlovad; känslo-verbs (älskar, saknar, längtar efter) | The romance subplot steps forward: *flickan som Lasse älskar bor i Stockholm.* |
| 24 | **Den sjuka pojken** | **pluskvamperfekt** (hade + supinum); narrative depth (när/medan/innan/efter att) | Nils gets properly ill (unlike faker Oskar in ch11); a night narrative. |

### Arc E — Berättelser och fester (kap 25–30): folktales, the sea, midsummer, the wedding

| Kap | Titel | Grammatikfokus | Nyckelmoment |
|---|---|---|---|
| 25 | **Sagan om trollet i berget** | folktale preteritum mastery; **det var en gång**; narrative connectives | Mamma tells a folktale — the story-within-story, echoing Ørberg's embedded myths. Original tale, John Bauer atmosphere. |
| 26 | **Pojken som ville flyga** | **passiv -s** (kallas, byggdes, sägs); **skulle** (framtid i dåtid / konditionalis) | Second embedded tale — an original Icarus-flavored northern folktale. |
| 27 | **Midsommar** | **partikelverb** spotlight (ställer upp, tar fram, slår upp, håller på) — stressed particles; medan/innan/efter att | Midsummer at morfar's farm: the most Swedish day of the year meets the most Swedish grammar there is. |
| 28 | **Storm på sjön** | **om-satser** (conditionals, real); passive in action; dramatic narrative synthesis | Lasse takes the children sailing; the storm from ch15 returns at sea. |
| 29 | **Man ska inte ge upp** | generic **man**; ordspråk; både…och / varken…eller / antingen…eller; ju…desto | Aftermath and reflection; morfar's proverbs; Lasse decides to propose. |
| 30 | **Festen** | synthesis; speech register (tal, skål); futurum outlook | Lasse and Maria's wedding in Sjövik. The whole cast, the whole grammar, guests traced on the ch1 map. Ends at the lake where the book began. |

**Deliberate echoes of Familia Romana** (structure, not content): the map opening,
letters-and-numbers coda in ch1, the family-tree second chapter, a naughty-child
third-act, a shop chapter, a shepherd/farm chapter with a lost animal, a body
chapter, embedded folktales late, sea peril, and a feast finale. Every sentence,
character, and plot beat is original.

## 6. Pronunciation strand ("Uttal")

A standalone **Uttalet** module before kap 1 (interactive, audio-heavy, minimal
reading): the alphabet; å/ä/ö; the long/short vowel rule (vowel before a single
consonant is long); listening contrasts (*vit/vitt, tak/tack*).

Then each chapter carries one **UTTAL** spotlight box with tappable minimal pairs:

| Kap | Uttalsfokus |
|---|---|
| 1 | å, ä, ö; alphabet; long vs. short vowels |
| 2 | stress basics; -or plural pronounced /-ur/ |
| 3 | g before front vowels (Göteborg!); silent d in *djur*-type onsets (ch9 reprise) |
| 4 | k before front vowels (kär, köper → /ɕ/); tj-ljudet |
| 5 | sj-ljudet (sju, sjö, själv) |
| 6 | skj/stj/sk before front vowels — all spellings of /ɧ/ |
| 7 | soft g/k reprise; gj/hj/lj silent letters (hjärta, ljus) |
| 8 | numbers fast speech (sju, tjugo, fyrtio) |
| 9 | retroflexes: rt, rd, rn, rs, rl (barn, förstår) |
| 10 | pitch accent I: accent 1 vs 2 exists (anden vs. anden) |
| 11 | long/short vowel minimal pairs in body words |
| 12 | pitch accent II: compounds always accent 2 |
| 13+ | rotating reprise, one pattern per chapter, driven by that chapter's vocab |

**Audio engine:** every prose block and every glossed word is playable. The reader
uses pre-generated TTS assets when present (`web/dist/audio/`), and falls back to
the browser's Swedish speech synthesis (Web Speech API, sv-SE) so the course is
fully audible from day one with zero assets.

## 7. Vocabulary policy

- **Budget tiers** (enforced by `lib/linter.py`): `unlocked` (taught earlier),
  `focus` (8–12/chapter, ≥3 recurrences in ≥2 contexts), `stretch` (margin-glossed,
  cap graduated by arc: A:3, B:4, C:4, D:5, E:6, auto-unlocked next chapter),
  `freebies` (function words unlocked by the grammar step), `proper nouns`
  (tracked, unbudgeted). Anything else = off-budget → linter error.
- **Selection:** frequency-first (Swedish core lists), then story utility, then
  cognate leverage (a transparent cognate is cheap — spend the budget on opaque
  high-value words like *flicka, pojke, tycker om*).
- **Morphology ledger:** since there is no reliable open Swedish lemmatizer we want
  to depend on, every lemma entry in the lexicon lists its inflected surface forms
  (*stad: stad, staden, städer, städerna, stads…*). The linter tokenizes prose and
  maps every token through this table; unknown tokens are flagged. The lexicon is
  itself a course artifact (it becomes the word index / Anki export).
- Actual cumulative vocabulary: **~420 content lemmas + ~230 function words**
  by kap 30 — with recycling enforced in review (`python -m lib.linter --book`):
  no focus lemma is met fewer than 3 times, and nearly all appear in 2+ chapters.
- **Repetition readings:** every chapter ends with an extra reading composed
  under a hard zero-new-words constraint — only unlocked vocabulary, written to
  re-deploy under-exposed words from earlier chapters. This is Ørberg's own
  *Colloquia Personarum* move: volume and recycling are the method.

## 8. The web course

A static SPA (no build step, no framework — same architecture that worked for the
Moomin reader), deployable to GitHub Pages.

- **Landing:** cover, Uttalet module, chapter grid grouped by arc, progress.
- **Reader view:** the Ørberg page, digitized —
  - main prose column; **margin-note column** on desktop (the signature LLPSI
    look: `= synonym`, `↔ motsats`, morphology callouts, tiny pictures), margin
    notes become tap-popovers on mobile;
  - word-tap gloss (Swedish first, English behind a second tap);
  - ▶ per block at natural pace, 🐢 slow; whole-chapter play;
  - per-chapter illustration slot.
- **GRAMMATIK view:** the chapter's paradigms as clean tables, in Swedish.
- **ÖVNINGAR view:** A (form blanks) and B (cloze) auto-checked inline with
  gentle feedback; C (free questions) with reveal-model-answer; per-chapter
  completion stored in localStorage.
- **Uttal view:** the pronunciation module + each chapter's UTTAL box, with
  minimal-pair players.
- **Ordlista:** cumulative searchable index (which chapter taught what).

## 9. Scope of the whole program (what Del I is part of)

1. **Del I: Familjen Berg** (this project) — 30 chapters, zero → A2/B1. ✅ build now
2. **Del II: Ut i Sverige** (future) — B1→B2: news register, formal writing,
   history/society chapters (the *Roma Aeterna* analogue), longer native-like prose.
3. **Companion artifacts** (generated from Del I sources, later phases): Anki decks,
   printable workbook (the wblib.py engine from the Moomin project's worksheets
   could be revived for this), pre-generated TTS audio, per-chapter illustrations.

## 10. Quality bars

- Every sentence must be idiomatic Swedish a native would accept; the staircase
  constrains *what is said*, never licenses broken Swedish (the hard-won lesson
  from the Moomin project's audit: staircase-as-guide, not cage).
- V2 word order is respected from the first sentence of kap 1 — word order is
  taught by relentless correct example long before it is named in kap 14.
- Register: neutral modern standard Swedish (rikssvenska); dialogue may be lightly
  colloquial (*ju, väl, nog* enter as focus items, they are load-bearing in real
  Swedish); no slang, no archaisms except flagged folktale formulas in kap 25–26.
- The linter catches budget cheating; it does not dictate style.

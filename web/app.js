/* Svenska per se illustrata — reader app.
   Static SPA: loads dist/chapters/manifest.json + dist/lexicon.json,
   renders chapters (prose + margins + uttal + grammatik + övningar),
   speaks Swedish via the Web Speech API (pre-generated audio can be
   slotted in later by the same interface). */

"use strict";

const state = {
  manifest: null,
  lexicon: null,
  chapter: null,     // loaded chapter JSON
  chapterIndex: -1,  // index into manifest.chapters
  enGlosses: false,
  voice: null,
  speakingBtn: null,
  chapterQueue: null, // array of {text, audio} still to play in play-all mode
  currentAudio: null, // HTMLAudioElement currently playing a pre-generated clip
};

const WORD_RE = /[a-zA-ZåäöÅÄÖéÉüÜøØæÆ]+(?:-[a-zA-ZåäöÅÄÖéÉüÜøØæÆ]+)*/g;

const $ = (sel) => document.querySelector(sel);

/* ---------- boot ---------- */

async function boot() {
  const [manifest, lexicon] = await Promise.all([
    fetch("dist/chapters/manifest.json").then((r) => r.json()),
    fetch("dist/lexicon.json").then((r) => r.json()),
  ]);
  state.manifest = manifest;
  state.lexicon = lexicon;
  state.enGlosses = localStorage.getItem("spsi.en") === "1";
  updateEnToggle();
  pickVoice();
  if (window.speechSynthesis) {
    speechSynthesis.onvoiceschanged = pickVoice;
  }
  renderLanding();
  wireChrome();
}

function pickVoice() {
  if (!window.speechSynthesis) return;
  const voices = speechSynthesis.getVoices();
  state.voice =
    voices.find((v) => /^sv([-_]|$)/i.test(v.lang) && /natural|online/i.test(v.name)) ||
    voices.find((v) => /^sv([-_]|$)/i.test(v.lang)) ||
    null;
}

/* ---------- landing ---------- */

function renderLanding() {
  const list = $("#chapter-list");
  list.innerHTML = "";
  const arcs = state.manifest.arcs || {};
  const chapters = state.manifest.chapters;

  const arcOf = (n) => {
    for (const [k, a] of Object.entries(arcs)) {
      if (n >= a.from && n <= a.to) return k;
    }
    return "?";
  };

  let currentArc = null;
  let groupEl = null;
  chapters.forEach((ch, idx) => {
    const arc = arcOf(ch.n);
    if (arc !== currentArc) {
      currentArc = arc;
      groupEl = document.createElement("div");
      groupEl.className = "arc-group";
      const h = document.createElement("h3");
      h.className = "arc-heading";
      const a = arcs[arc];
      h.textContent = a ? `${arc} · ${a.name}` : "";
      groupEl.appendChild(h);
      list.appendChild(groupEl);
    }
    const card = document.createElement("button");
    card.className = "chapter-card";
    card.innerHTML =
      `<span class="num">${ch.n}</span>` +
      `<span class="t">${esc(ch.titel)}</span>` +
      `<span class="g">${esc(shortFocus(ch.grammatik_fokus))}</span>`;
    card.addEventListener("click", () => openChapter(idx));
    groupEl.appendChild(card);
  });

  // guide card — "how this book works", the one page where English is welcome
  const guideCard = document.createElement("button");
  guideCard.className = "chapter-card guide-card";
  guideCard.innerHTML =
    `<span class="num">📖</span>` +
    `<span class="t">Så använder du boken</span>` +
    `<span class="g">how this book works</span>`;
  guideCard.addEventListener("click", showGuide);
  list.insertBefore(guideCard, list.firstChild);

  // läseboken — supplementary readings
  if (state.manifest.lasebok && state.manifest.lasebok.length) {
    const group = document.createElement("div");
    group.className = "arc-group";
    const h = document.createElement("h3");
    h.className = "arc-heading";
    h.textContent = "Läseboken · mer att läsa — inga nya ord!";
    group.appendChild(h);
    state.manifest.lasebok.forEach((lb, idx) => {
      const card = document.createElement("button");
      card.className = "chapter-card";
      card.innerHTML =
        `<span class="num">${lb.typ === "saga" ? "✨" : "☕"}</span>` +
        `<span class="t">${esc(lb.titel)}</span>` +
        `<span class="g">efter kapitel ${lb.efter_kapitel}</span>`;
      card.addEventListener("click", () => openLasebok(idx));
      group.appendChild(card);
    });
    list.appendChild(group);
  }

  const last = parseInt(localStorage.getItem("spsi.lastChapter") || "-1", 10);
  const banner = $("#continue-banner");
  if (last >= 0 && last < chapters.length) {
    banner.style.display = "";
    $("#continue-chapter-label").textContent =
      `Kapitel ${chapters[last].n} · ${chapters[last].titel}`;
    $("#continue-btn").onclick = () => openChapter(last);
  } else {
    banner.style.display = "none";
  }
}

function shortFocus(s) {
  if (!s) return "";
  const cut = s.split(";")[0];
  return cut.length > 46 ? cut.slice(0, 45) + "…" : cut;
}

/* ---------- chapter loading ---------- */

async function openChapter(idx) {
  const meta = state.manifest.chapters[idx];
  if (!meta) return;
  stopSpeech();
  const data = await fetch("dist/" + meta.file).then((r) => r.json());
  state.chapter = data;
  state.chapterIndex = idx;
  localStorage.setItem("spsi.lastChapter", String(idx));
  renderChapter();
  showView("reader");
  window.scrollTo(0, 0);
}

function showView(id) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  $("#" + id).classList.add("active");
}

/* ---------- läseboken ---------- */

async function openLasebok(idx) {
  const meta = state.manifest.lasebok[idx];
  if (!meta) return;
  stopSpeech();
  const data = await fetch("dist/" + meta.file).then((r) => r.json());
  state.chapter = null;
  state.chapterIndex = -1;

  $("#reader-chapter-num").textContent = "LÄSEBOKEN";
  $("#reader-chapter-title").textContent = data.titel;
  $("#footer-title").textContent = `Läseboken · ${data.titel}`;
  $("#prev-chapter-btn").disabled = idx <= 0;
  $("#next-chapter-btn").disabled = idx >= state.manifest.lasebok.length - 1;
  $("#prev-chapter-btn").onclick = () => idx > 0 && openLasebok(idx - 1);
  $("#next-chapter-btn").onclick = () =>
    idx < state.manifest.lasebok.length - 1 && openLasebok(idx + 1);

  const root = $("#chapter-scroll");
  root.innerHTML = "";
  const head = document.createElement("div");
  head.className = "kap-heading";
  head.innerHTML =
    `<div class="kn">Läseboken · ${data.typ === "saga" ? "en saga" : "ur livet i Sjövik"}</div>` +
    `<h1>${esc(data.titel)}</h1>`;
  root.appendChild(head);
  const note = document.createElement("p");
  note.className = "kap-focus";
  note.textContent =
    `Läs efter kapitel ${data.efter_kapitel} — inga nya ord, bara mer svenska!`;
  root.appendChild(note);
  (data.block || []).forEach((block) => root.appendChild(renderBlock(block)));
  const fin = document.createElement("div");
  fin.className = "fin";
  fin.textContent = "❦";
  root.appendChild(fin);
  showView("reader");
  window.scrollTo(0, 0);
}

/* ---------- guide ---------- */

function showGuide() {
  stopSpeech();
  state.chapter = null;
  state.chapterIndex = -1;
  $("#reader-chapter-num").textContent = "";
  $("#reader-chapter-title").textContent = "Så använder du boken";
  $("#footer-title").textContent = "Så använder du boken · how this book works";
  $("#prev-chapter-btn").disabled = true;
  $("#next-chapter-btn").disabled = true;

  const root = $("#chapter-scroll");
  root.innerHTML = `
  <div class="kap-heading"><div class="kn">Innan du börjar</div>
    <h1>Så använder du boken</h1></div>
  <p class="kap-focus">This is the only page in English. After this: Swedish only —
    and that is the whole idea.</p>

  <section class="gram-item">
    <h4>En bok på svenska — bara på svenska</h4>
    <p>This book teaches Swedish <em>in</em> Swedish, the way Ørberg's
    <em>Lingua Latina</em> taught Latin in Latin. Every new word is understandable
    from the story, the margin notes, the pictures and the words you already know.
    You never translate — you <em>understand</em>. Read slowly, listen often, and
    trust the book: if a word is new, the chapter will show you what it means.</p>
  </section>

  <section class="gram-item">
    <h4>Tryck på orden — tap the words</h4>
    <p>Tap any word in the text to hear it and see a Swedish explanation.
    Stuck? The <strong>EN</strong> button in the popover (or in the top bar, for
    always-on) shows an English hint — think of it as a fire escape, not a door.</p>
    <p>▶ plays a paragraph aloud. 🐢 plays it slowly. <strong>Lyssna</strong> at the
    top plays the whole chapter. Use your ears constantly — Swedish spelling only
    makes sense once you hear it.</p>
  </section>

  <section class="gram-item">
    <h4>Marginalen — the margin notes</h4>
    <p>Notes beside the text explain new words with old words:</p>
    <div class="gram-table-wrap"><table class="gram-table">
      <tr><td><strong>=</strong></td><td>the same thing (<em>ligger i = är i</em>)</td></tr>
      <tr><td><strong>↔</strong></td><td>the opposite (<em>stor ↔ liten</em>)</td></tr>
      <tr><td><strong>ett land — två länder</strong></td><td>word forms, shown as they appear</td></tr>
      <tr><td><strong>⏪ / ⏩</strong></td><td>past / future</td></tr>
      <tr><td><strong>🔍 …?</strong></td><td>a teaser for the next chapter</td></tr>
    </table></div>
  </section>

  <section class="gram-item">
    <h4>Bokens små ord — the book's own words</h4>
    <p>Exercise instructions use a handful of words before the story teaches them.
    Learn these once, here, and every instruction in the book is yours:</p>
    <div class="gram-table-wrap"><table class="gram-table">
      <tr><td><strong>skriv</strong></td><td>write</td>
          <td><strong>svara</strong></td><td>answer</td></tr>
      <tr><td><strong>läs</strong></td><td>read</td>
          <td><strong>lyssna</strong></td><td>listen</td></tr>
      <tr><td><strong>rätta</strong></td><td>check (your answers)</td>
          <td><strong>visa svar</strong></td><td>show the answers</td></tr>
      <tr><td><strong>rätt form</strong></td><td>the correct form</td>
          <td><strong>ordet</strong></td><td>the word</td></tr>
      <tr><td><strong>hela meningar</strong></td><td>complete sentences</td>
          <td><strong>en övning</strong></td><td>an exercise</td></tr>
    </table></div>
  </section>

  <section class="gram-item">
    <h4>Varje kapitel — every chapter</h4>
    <div class="gram-table-wrap"><table class="gram-table">
      <tr><td><strong>Läsestycken</strong></td>
          <td>the story — read it twice: once for the plot, once for the words</td></tr>
      <tr><td><strong>Repetition</strong></td>
          <td>an extra reading with <em>zero</em> new words — pure comprehension,
          old words coming back</td></tr>
      <tr><td><strong>Uttal</strong></td>
          <td>pronunciation: tap the chips and imitate what you hear</td></tr>
      <tr><td><strong>Grammatik</strong></td>
          <td>the chapter's patterns, explained in Swedish with tables</td></tr>
      <tr><td><strong>Övning A</strong></td>
          <td>forms — fill the blanks, press <em>Rätta</em> to check</td></tr>
      <tr><td><strong>Övning B</strong></td>
          <td>words — fill the blanks from the word list</td></tr>
      <tr><td><strong>Övning C</strong></td>
          <td>questions — answer aloud or on paper, then <em>Visa svar</em></td></tr>
    </table></div>
  </section>

  <section class="gram-item">
    <h4>Ett råd — one piece of advice</h4>
    <p>Don't aim for perfect recall; aim for <em>understanding at reading speed</em>.
    Reread old chapters — they get easy, and that feeling of ease is the learning.
    Nu börjar vi: <strong>Sverige är ett land …</strong></p>
  </section>
  <div class="fin">❦</div>`;
  showView("reader");
  window.scrollTo(0, 0);
}

/* ---------- chapter rendering ---------- */

function renderChapter() {
  const ch = state.chapter;
  $("#reader-chapter-num").textContent = "KAP. " + ch.kapitel;
  $("#reader-chapter-title").textContent = ch.titel;
  $("#footer-title").textContent = `Kapitel ${ch.kapitel} · ${ch.titel}`;

  const prev = $("#prev-chapter-btn");
  const next = $("#next-chapter-btn");
  prev.onclick = null; // clear any läsebok navigation handlers
  next.onclick = null;
  prev.disabled = state.chapterIndex <= 0;
  next.disabled = state.chapterIndex >= state.manifest.chapters.length - 1;

  const root = $("#chapter-scroll");
  root.innerHTML = "";

  // heading
  const head = document.createElement("div");
  head.className = "kap-heading";
  head.innerHTML =
    `<div class="kn">Kapitel ${ch.kapitel}</div><h1>${esc(ch.titel)}</h1>`;
  root.appendChild(head);
  const focus = document.createElement("p");
  focus.className = "kap-focus";
  focus.textContent = ch.grammatik_fokus || "";
  root.appendChild(focus);

  // illustration (per se illustrata!)
  if (ch.image) {
    const fig = document.createElement("figure");
    fig.className = "kap-illustration";
    const img = document.createElement("img");
    img.src = "dist/" + ch.image;
    img.alt = ch.titel;
    fig.appendChild(img);
    root.appendChild(fig);
  }

  // läsestycken
  (ch.lasstycken || []).forEach((sect) => {
    const rub = document.createElement("h3");
    rub.className = "lect-rubrik";
    rub.textContent = sect.rubrik || "";
    root.appendChild(rub);
    (sect.block || []).forEach((block) => {
      root.appendChild(renderBlock(block));
    });
  });

  // repetition — the zero-new-words extra reading
  if (ch.repetition) {
    const rep = document.createElement("section");
    rep.className = "repetition-box";
    rep.innerHTML =
      `<h3>Repetition</h3>` +
      `<p class="rep-rubrik">${esc(ch.repetition.rubrik || "")}</p>` +
      `<p class="rep-note">Inga nya ord — läs och förstå allt!</p>`;
    (ch.repetition.block || []).forEach((block) => {
      rep.appendChild(renderBlock(block));
    });
    root.appendChild(rep);
  }

  // uttal
  if (ch.uttal) root.appendChild(renderUttal(ch.uttal, ch.uttal_fokus));

  // grammatik
  if (ch.grammatik && ch.grammatik.length) {
    const sec = document.createElement("section");
    sec.className = "grammatik-section";
    sec.innerHTML = `<h3 class="section-heading">Grammatik</h3>`;
    ch.grammatik.forEach((g) => {
      const item = document.createElement("div");
      item.className = "gram-item";
      let html = `<h4>${esc(g.rubrik || "")}</h4>`;
      if (g.forklaring) html += `<p>${esc(g.forklaring)}</p>`;
      if (g.tabell) html += renderTable(g.tabell);
      item.innerHTML = html;
      sec.appendChild(item);
    });
    root.appendChild(sec);
  }

  // övningar
  if (ch.ovningar) root.appendChild(renderOvningar(ch.ovningar));

  const fin = document.createElement("div");
  fin.className = "fin";
  fin.textContent = "❦";
  root.appendChild(fin);
}

function renderBlock(block) {
  const wrap = document.createElement("div");
  wrap.className = "pblock";

  const prose = document.createElement("div");
  prose.className = "prose";
  if (block.typ === "dialogue" && block.speaker) {
    const sp = document.createElement("span");
    sp.className = "speaker";
    sp.textContent = block.speaker;
    prose.appendChild(sp);
  }
  const p = document.createElement("span");
  p.innerHTML = wrapWords(block.text || "");
  prose.appendChild(p);

  const audioRow = document.createElement("div");
  audioRow.className = "block-audio";
  const play = audioButton("▶", block.text, 1.0, block.audio);
  const slow = audioButton("🐢", block.text, 0.68, block.audio);
  audioRow.appendChild(play);
  audioRow.appendChild(slow);
  prose.appendChild(audioRow);
  wrap.appendChild(prose);

  const mn = document.createElement("aside");
  mn.className = "margin-notes";
  (block.margin || []).forEach((note) => {
    const s = document.createElement("span");
    s.className = "mn";
    s.textContent = note;
    mn.appendChild(s);
  });
  wrap.appendChild(mn);
  return wrap;
}

function renderTable(t) {
  let html = `<div class="gram-table-wrap"><table class="gram-table">`;
  if (t.head && t.head.some((h) => h)) {
    html += "<tr>" + t.head.map((h) => `<th>${esc(h)}</th>`).join("") + "</tr>";
  }
  (t.rows || []).forEach((row) => {
    html += "<tr>" + row.map((c) => `<td>${esc(c)}</td>`).join("") + "</tr>";
  });
  html += "</table></div>";
  return html;
}

function renderUttal(u, fokus) {
  const box = document.createElement("section");
  box.className = "uttal-box";
  box.innerHTML =
    `<h3>Uttal</h3>` +
    `<p class="uttal-rubrik">${esc(u.rubrik || fokus || "")}</p>` +
    (u.forklaring ? `<p class="uttal-forklaring">${esc(u.forklaring)}</p>` : "");
  (u.grupper || []).forEach((g) => {
    const row = document.createElement("div");
    row.className = "uttal-grupp";
    const name = document.createElement("span");
    name.className = "gname";
    name.textContent = g.namn;
    row.appendChild(name);
    (g.ord || []).forEach((w) => {
      const chip = document.createElement("button");
      chip.className = "chip";
      chip.textContent = w;
      chip.addEventListener("click", () => {
        const src = state.chapter && state.chapter.uttal_audio
          ? state.chapter.uttal_audio[w] : null;
        stopSpeech();
        playAudio(src, w, 1.0);
      });
      row.appendChild(chip);
    });
    box.appendChild(row);
  });
  return box;
}

/* ---------- övningar ---------- */

function renderOvningar(ov) {
  const sec = document.createElement("section");
  sec.className = "ovningar-section";
  sec.innerHTML = `<h3 class="section-heading">Övningar</h3>`;

  ["A", "B"].forEach((key) => {
    const o = ov[key];
    if (!o) return;
    const box = document.createElement("div");
    box.className = "ovning";
    box.innerHTML =
      `<h4>Övning ${key}</h4><p class="instruktion">${esc(o.instruktion || "")}</p>`;
    const inputs = [];
    (o.items || []).forEach((item, i) => {
      const div = document.createElement("div");
      div.className = "ov-item";
      div.appendChild(clozeToDom(item.q, inputs));
      box.appendChild(div);
    });
    const actions = document.createElement("div");
    actions.className = "ov-actions";
    const check = document.createElement("button");
    check.className = "ov-btn";
    check.textContent = "Rätta";
    const reveal = document.createElement("button");
    reveal.className = "ov-btn";
    reveal.textContent = "Visa svar";
    const score = document.createElement("span");
    score.className = "ov-score";
    check.addEventListener("click", () => {
      let ok = 0;
      inputs.forEach((inp) => {
        const good = matches(inp.value, inp.dataset.answers);
        inp.classList.toggle("ok", good);
        inp.classList.toggle("bad", !good);
        if (good) ok++;
      });
      score.textContent = `${ok} / ${inputs.length} rätt`;
    });
    reveal.addEventListener("click", () => {
      inputs.forEach((inp) => {
        inp.value = inp.dataset.answers.split("|")[0];
        inp.classList.remove("bad");
        inp.classList.add("ok");
      });
      score.textContent = "";
    });
    actions.appendChild(check);
    actions.appendChild(reveal);
    actions.appendChild(score);
    box.appendChild(actions);
    sec.appendChild(box);
  });

  const c = ov.C;
  if (c) {
    const box = document.createElement("div");
    box.className = "ovning";
    box.innerHTML =
      `<h4>Övning C</h4><p class="instruktion">${esc(c.instruktion || "")}</p>`;
    (c.items || []).forEach((item) => {
      const div = document.createElement("div");
      div.className = "ovc-item";
      const q = document.createElement("div");
      q.className = "ovc-q";
      q.innerHTML = wrapWords(item.q);
      div.appendChild(q);
      const btn = document.createElement("button");
      btn.className = "ovc-reveal";
      btn.textContent = "Visa svar";
      btn.addEventListener("click", () => div.classList.toggle("revealed"));
      div.appendChild(btn);
      const model = document.createElement("p");
      model.className = "ovc-model";
      model.textContent = item.model || "";
      div.appendChild(model);
      box.appendChild(div);
    });
    sec.appendChild(box);
  }
  return sec;
}

/* "Sverige är ett {stort|stora} land." -> DOM with an input per {…} */
function clozeToDom(q, inputs) {
  const frag = document.createDocumentFragment();
  let last = 0;
  const re = /\{([^}]+)\}/g;
  let m;
  while ((m = re.exec(q)) !== null) {
    if (m.index > last) {
      frag.appendChild(spanWithWords(q.slice(last, m.index)));
    }
    const answers = m[1];
    const inp = document.createElement("input");
    inp.type = "text";
    inp.autocapitalize = "off";
    inp.autocomplete = "off";
    inp.spellcheck = false;
    inp.dataset.answers = answers;
    inp.style.width = Math.max(3.2, answers.split("|")[0].length * 0.72 + 1.6) + "em";
    inputs.push(inp);
    frag.appendChild(inp);
    last = re.lastIndex;
  }
  if (last < q.length) frag.appendChild(spanWithWords(q.slice(last)));
  return frag;
}

function spanWithWords(text) {
  const s = document.createElement("span");
  s.innerHTML = wrapWords(text);
  return s;
}

function matches(value, answers) {
  const v = (value || "").trim().toLowerCase();
  return answers.split("|").some((a) => a.trim().toLowerCase() === v);
}

/* ---------- word wrapping + glossing ---------- */

function wrapWords(text) {
  return esc(text).replace(WORD_RE, (w) => `<span class="w">${w}</span>`);
}

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function onWordTap(el) {
  const word = el.textContent;
  const lex = state.lexicon;
  const key = word.toLowerCase();
  const pop = $("#gloss-popover");

  const lemmaKeys = lex.surfaces[key] || [];
  let html = "";
  if (lemmaKeys.length) {
    lemmaKeys.forEach((lk) => {
      const L = lex.lemmas[lk];
      const lemmaLabel = L.pos === "substantiv" && L.gender
        ? `${L.gender} ${displayLemma(lk)}`
        : displayLemma(lk);
      html +=
        `<div class="gp-entry">` +
        `<span class="gp-word">${esc(lemmaLabel)}</span>` +
        `<span class="gp-meta">${esc(L.pos || "")}</span>` +
        `<div class="gp-forms">${esc((L.forms || []).slice(0, 5).join(", "))}</div>` +
        `<div class="gp-sv">${esc(L.sv || "")}</div>` +
        (L.en ? `<div class="gp-en" data-en>${esc(L.en)}</div>` : "") +
        `</div>`;
    });
  } else {
    // proper noun?
    const pn = Object.entries(lex.proper).find(([, e]) =>
      (e.forms || []).some((f) => f.toLowerCase() === key)
    );
    if (pn) {
      html =
        `<span class="gp-word">${esc(pn[0])}</span>` +
        `<span class="gp-meta">namn</span>` +
        `<div class="gp-sv">${esc(pn[1].what || "")}</div>`;
    } else {
      html = `<span class="gp-word">${esc(word)}</span>`;
    }
  }

  html += `<div class="gp-row">` +
    `<button class="gp-btn" data-speak>🔊 lyssna</button>` +
    (html.includes("data-en") && !state.enGlosses
      ? `<button class="gp-btn" data-showen>EN</button>` : "") +
    `</div>`;

  pop.innerHTML = html;
  if (state.enGlosses) {
    pop.querySelectorAll(".gp-en").forEach((e) => e.classList.add("open"));
  }
  pop.querySelector("[data-speak]").addEventListener("click", () => speak(word, 0.85));
  const se = pop.querySelector("[data-showen]");
  if (se) se.addEventListener("click", () => {
    pop.querySelectorAll(".gp-en").forEach((e) => e.classList.add("open"));
    se.remove();
  });

  // position near the word
  const r = el.getBoundingClientRect();
  pop.classList.add("open");
  const px = Math.min(r.left + window.scrollX, window.scrollX + document.documentElement.clientWidth - 320);
  pop.style.left = Math.max(8, px) + "px";
  pop.style.top = r.bottom + window.scrollY + 8 + "px";
  speak(word, 0.9);
}

function displayLemma(key) {
  // lexicon keys like 'var_q' carry a disambiguating suffix; show the bare form
  return key.replace(/_[a-z]+$/, "");
}

/* ---------- audio ---------- */

function audioButton(label, text, rate, audioSrc) {
  const b = document.createElement("button");
  b.className = "audio-btn";
  b.textContent = label;
  b.title = rate < 1 ? "Lyssna långsamt" : "Lyssna";
  b.addEventListener("click", () => {
    if (state.speakingBtn === b) {
      stopSpeech();
      return;
    }
    stopSpeech();
    state.speakingBtn = b;
    b.classList.add("speaking");
    playAudio(audioSrc, text, rate, () => {
      b.classList.remove("speaking");
      if (state.speakingBtn === b) state.speakingBtn = null;
    });
  });
  return b;
}

/* Play a pre-generated clip if it exists; otherwise fall back to the
   browser's Swedish speech synthesis. Slow playback uses playbackRate
   (pitch-preserving by default), so one clip serves both speeds. */
function playAudio(src, text, rate, onend) {
  if (!src) {
    speak(text, rate, onend);
    return;
  }
  const a = new Audio("dist/" + src);
  a.playbackRate = rate || 1.0;
  a.onended = () => {
    if (state.currentAudio === a) state.currentAudio = null;
    if (onend) onend();
  };
  a.onerror = () => {
    // clip not generated (yet) — synthesis covers the gap
    if (state.currentAudio === a) state.currentAudio = null;
    speak(text, rate, onend);
  };
  state.currentAudio = a;
  a.play().catch(() => a.onerror());
}

function speak(text, rate, onend) {
  if (!window.speechSynthesis) return;
  const clean = String(text).replace(/[”“"«»]/g, "");
  const u = new SpeechSynthesisUtterance(clean);
  u.lang = "sv-SE";
  if (state.voice) u.voice = state.voice;
  u.rate = rate || 1.0;
  if (onend) u.onend = onend;
  speechSynthesis.speak(u);
}

function stopSpeech() {
  if (window.speechSynthesis) speechSynthesis.cancel();
  if (state.currentAudio) {
    state.currentAudio.onended = null;
    state.currentAudio.onerror = null;
    state.currentAudio.pause();
    state.currentAudio = null;
  }
  if (state.speakingBtn) {
    state.speakingBtn.classList.remove("speaking");
    state.speakingBtn = null;
  }
  state.chapterQueue = null;
  const pb = $("#play-chapter-btn");
  if (pb) pb.textContent = "▶ Lyssna";
}

function playChapter() {
  const ch = state.chapter;
  if (!ch) return;
  if (state.chapterQueue) {
    stopSpeech();
    return;
  }
  const units = [];
  (ch.lasstycken || []).forEach((s) =>
    (s.block || []).forEach((b) => b.text && units.push({ text: b.text, audio: b.audio }))
  );
  if (ch.repetition) {
    (ch.repetition.block || []).forEach((b) =>
      b.text && units.push({ text: b.text, audio: b.audio })
    );
  }
  state.chapterQueue = units;
  $("#play-chapter-btn").textContent = "◼ Stopp";
  const next = () => {
    if (!state.chapterQueue || !state.chapterQueue.length) {
      stopSpeech();
      return;
    }
    const u = state.chapterQueue.shift();
    playAudio(u.audio, u.text, 1.0, next);
  };
  next();
}

/* ---------- chrome wiring ---------- */

function wireChrome() {
  $("#back-btn").addEventListener("click", () => {
    stopSpeech();
    showView("landing");
    renderLanding();
  });
  $("#prev-chapter-btn").addEventListener("click", () => {
    if (state.chapterIndex > 0) openChapter(state.chapterIndex - 1);
  });
  $("#next-chapter-btn").addEventListener("click", () => {
    if (state.chapterIndex < state.manifest.chapters.length - 1)
      openChapter(state.chapterIndex + 1);
  });
  $("#play-chapter-btn").addEventListener("click", playChapter);
  $("#en-toggle").addEventListener("click", () => {
    state.enGlosses = !state.enGlosses;
    localStorage.setItem("spsi.en", state.enGlosses ? "1" : "0");
    updateEnToggle();
  });

  document.addEventListener("click", (e) => {
    const w = e.target.closest(".w");
    const pop = $("#gloss-popover");
    if (w) {
      onWordTap(w);
      e.stopPropagation();
      return;
    }
    if (!e.target.closest("#gloss-popover")) pop.classList.remove("open");
  });

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (!$("#reader").classList.contains("active")) return;
    if (e.key === "ArrowLeft" && state.chapterIndex > 0)
      openChapter(state.chapterIndex - 1);
    else if (e.key === "ArrowRight" && state.chapterIndex < state.manifest.chapters.length - 1)
      openChapter(state.chapterIndex + 1);
    else if (e.key === "Escape") {
      stopSpeech();
      showView("landing");
      renderLanding();
    }
  });
}

function updateEnToggle() {
  $("#en-toggle").setAttribute("aria-pressed", state.enGlosses ? "true" : "false");
}

boot();

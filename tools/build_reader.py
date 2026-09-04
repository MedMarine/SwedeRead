"""Build the web reader's data files.

chapters/kapNN.yaml + lib/lexicon.yaml + staircase.yaml
    -> web/dist/chapters/kapNN.json
    -> web/dist/chapters/manifest.json
    -> web/dist/lexicon.json

Usage:  python tools/build_reader.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "dist"
VOICE_MAP_PATH = ROOT / "tools" / "voice_map.yaml"


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_voice_map() -> dict:
    if VOICE_MAP_PATH.exists():
        return load_yaml(VOICE_MAP_PATH) or {}
    return {}


def audio_name(voice_map: dict, speaker: str, text: str) -> str:
    """Deterministic clip identity: sha1(voice + style + text).

    Any change to the text, the assigned voice, or the delivery style yields
    a new filename — the app then finds no file and falls back to speech
    synthesis until tools/generate_audio.py renders the missing clip.
    """
    entry = voice_map.get(speaker) or voice_map.get("NARRATOR") or {}
    key = "\n".join([entry.get("voice", ""), entry.get("style", ""), " ".join(text.split())])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def attach_block_audio(voice_map: dict, blocks, subdir: str) -> None:
    """Annotate prose blocks in place with their expected audio path."""
    gi = 0
    for block in blocks:
        text = (block.get("text") or "").strip()
        if not text:
            continue
        speaker = block.get("speaker") if block.get("typ") == "dialogue" else "NARRATOR"
        h = audio_name(voice_map, speaker or "NARRATOR", text)
        block["audio"] = f"audio/{subdir}/b{gi:03d}_{h}.mp3"
        gi += 1


def main() -> None:
    staircase = load_yaml(ROOT / "staircase.yaml")
    voice_map = load_voice_map()
    lexicon = load_yaml(ROOT / "lib" / "lexicon.yaml")
    lemmas = lexicon.get("lemmas", {})
    proper = lexicon.get("proper", {})

    plan_by_n = {c["n"]: c for c in staircase.get("chapters", [])}
    arcs = staircase.get("rules", {}).get("arcs", {})

    (OUT / "chapters").mkdir(parents=True, exist_ok=True)

    manifest = {
        "title": staircase.get("meta", {}).get("title", "Svenska per se illustrata"),
        "arcs": {
            k: {"name": v["name"], "from": v["chapters"][0], "to": v["chapters"][1]}
            for k, v in arcs.items()
        },
        "chapters": [],
    }

    chapter_files = sorted((ROOT / "chapters").glob("kap*.yaml"))
    for path in chapter_files:
        ch = load_yaml(path)
        n = ch["kapitel"]
        plan = plan_by_n.get(n, {})

        # per-chapter glossary: lemmas introduced this chapter
        glossary = {}
        for key, entry in lemmas.items():
            if entry.get("intro") == n and entry.get("tier") in ("focus", "stretch"):
                glossary[key] = {
                    "pos": entry.get("pos"),
                    "gender": entry.get("gender"),
                    "forms": entry.get("forms", [key]),
                    "sv": entry.get("gloss_sv", ""),
                    "en": entry.get("gloss_en", ""),
                    "tier": entry.get("tier"),
                }

        image = None
        for ext in ("jpg", "png", "svg"):
            if (OUT / "images" / f"kap{n:02d}.{ext}").exists():
                image = f"images/kap{n:02d}.{ext}"
                break

        # expected audio paths (content-hashed; see audio_name)
        all_blocks = [b for s in ch.get("lasstycken", []) for b in s.get("block", [])]
        if ch.get("repetition"):
            all_blocks += ch["repetition"].get("block", [])
        attach_block_audio(voice_map, all_blocks, f"kap{n:02d}")
        uttal_audio = {}
        for g in (ch.get("uttal") or {}).get("grupper", []):
            for w in g.get("ord", []):
                w = str(w)
                uttal_audio[w] = f"audio/uttal/{audio_name(voice_map, 'UTTAL', w)}.mp3"

        out = {
            "kapitel": n,
            "image": image,
            "titel": ch.get("titel", ""),
            "arc": ch.get("arc"),
            "grammatik_fokus": ch.get("grammatik_fokus", plan.get("grammar_focus", "")),
            "uttal_fokus": ch.get("uttal_fokus", plan.get("uttal", "")),
            "fokus": ch.get("fokus", []),
            "stretch": ch.get("stretch", []),
            "lasstycken": ch.get("lasstycken", []),
            "repetition": ch.get("repetition"),
            "grammatik": ch.get("grammatik", []),
            "uttal": ch.get("uttal"),
            "uttal_audio": uttal_audio,
            "ovningar": ch.get("ovningar", {}),
            "glossary": glossary,
        }
        fname = f"kap{n:02d}.json"
        with open(OUT / "chapters" / fname, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)

        manifest["chapters"].append(
            {
                "n": n,
                "titel": ch.get("titel", ""),
                "arc": ch.get("arc"),
                "grammatik_fokus": out["grammatik_fokus"],
                "file": f"chapters/{fname}",
            }
        )
        print(f"built {fname}  ({ch.get('titel','')})")

    # läsebok — supplementary readings (zero new words, pegged to a chapter level)
    manifest["lasebok"] = []
    lb_dir = ROOT / "lasebok"
    if lb_dir.exists():
        (OUT / "lasebok").mkdir(parents=True, exist_ok=True)
        for path in sorted(lb_dir.glob("lb*.yaml")):
            lb = load_yaml(path)
            attach_block_audio(voice_map, lb.get("block", []), f"lb{lb['nummer']:02d}")
            fname = f"lb{lb['nummer']:02d}.json"
            with open(OUT / "lasebok" / fname, "w", encoding="utf-8") as f:
                json.dump(lb, f, ensure_ascii=False, indent=1)
            manifest["lasebok"].append(
                {
                    "nummer": lb["nummer"],
                    "titel": lb.get("titel", ""),
                    "efter_kapitel": lb["efter_kapitel"],
                    "typ": lb.get("typ", ""),
                    "file": f"lasebok/{fname}",
                }
            )
            print(f"built {fname}  ({lb.get('titel','')})")

    with open(OUT / "chapters" / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    # global lexicon for word-tap glossing
    surfaces: dict[str, list[str]] = {}
    for key, entry in lemmas.items():
        for form in entry.get("forms", [key]):
            surfaces.setdefault(form.lower(), [])
            if key not in surfaces[form.lower()]:
                surfaces[form.lower()].append(key)
    lex_out = {
        "surfaces": surfaces,
        "lemmas": {
            key: {
                "pos": e.get("pos"),
                "gender": e.get("gender"),
                "forms": e.get("forms", [key]),
                "sv": e.get("gloss_sv", ""),
                "en": e.get("gloss_en", ""),
                "intro": e.get("intro"),
                "tier": e.get("tier"),
            }
            for key, e in lemmas.items()
        },
        "proper": {
            key: {"forms": e.get("forms", [key]), "what": e.get("what", "")}
            for key, e in proper.items()
        },
    }
    with open(OUT / "lexicon.json", "w", encoding="utf-8") as f:
        json.dump(lex_out, f, ensure_ascii=False, indent=1)
    print(f"built lexicon.json  ({len(lemmas)} lemmas, {len(proper)} proper nouns)")
    print(f"built manifest.json ({len(manifest['chapters'])} chapters)")


if __name__ == "__main__":
    main()

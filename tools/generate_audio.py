#!/usr/bin/env python3
"""Batch audio generation via Gemini TTS for Svenska per se illustrata.

Consumes the BUILT reader data (web/dist/chapters/*.json, web/dist/lasebok/*.json)
so the generator and the app agree, byte for byte, on which clip belongs to
which block: build_reader.py embeds a content-hashed `audio` path per prose
block (sha1 of voice + style + text) and an `uttal_audio` map per chapter.
This script renders every clip whose file does not exist yet.

Consequences of the hash scheme:
  - editing a block's text (or a voice/style in tools/voice_map.yaml) changes
    its filename → the old clip is simply ignored and the new one is rendered
    on the next run. `--skip-existing` behaviour is therefore automatic.
  - nothing needs a manifest of what is stale; "missing file" IS the queue.

Requirements: GEMINI_API_KEY env (or --api-key), ffmpeg on PATH, google-genai.

Typical invocations:
  python tools/generate_audio.py --dry-run           # what would render + cost
  python tools/generate_audio.py --sample kap01      # one chapter, sync (audition)
  python tools/generate_audio.py --batch             # everything missing, ~50% cost
  python tools/generate_audio.py --batch --only uttal
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "web" / "dist"
AUDIO_OUT = DIST  # block["audio"] paths are relative to dist/
VOICE_MAP_PATH = ROOT / "tools" / "voice_map.yaml"
STATE_DIR = ROOT / "tools" / ".batch-state"

DEFAULT_MODEL = "gemini-2.5-pro-preview-tts"
FALLBACK_VOICE = "Sulafat"


def load_voice_map() -> dict:
    with VOICE_MAP_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass
class Unit:
    """One clip to synthesize."""
    id: str        # e.g. "kap01/b003" or "uttal/<hash>"
    rel_path: str  # dist-relative mp3 path from the built JSON
    speaker: str   # voice_map key
    text: str      # spoken text (style prompt prepended at request time)


def collect_units(only: str | None = None, sample: str | None = None) -> list[Unit]:
    units: list[Unit] = []
    seen: set[str] = set()

    def add(rel_path: str, speaker: str, text: str, uid: str) -> None:
        if rel_path in seen:
            return
        seen.add(rel_path)
        units.append(Unit(id=uid, rel_path=rel_path, speaker=speaker, text=text))

    def blocks_from(doc: dict, label: str) -> None:
        blocks = [b for s in doc.get("lasstycken", []) for b in s.get("block", [])]
        if doc.get("repetition"):
            blocks += doc["repetition"].get("block", [])
        blocks += doc.get("block", [])  # läsebok shape
        for b in blocks:
            text = (b.get("text") or "").strip()
            rel = b.get("audio")
            if not text or not rel:
                continue
            speaker = b.get("speaker") if b.get("typ") == "dialogue" else "NARRATOR"
            add(rel, speaker or "NARRATOR", text, f"{label}/{Path(rel).stem}")

    for path in sorted((DIST / "chapters").glob("kap*.json")):
        label = path.stem
        if sample and label != sample:
            continue
        if only and only not in ("chapters", "uttal"):
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not only or only == "chapters":
            blocks_from(doc, label)
        if not only or only == "uttal":
            for word, rel in (doc.get("uttal_audio") or {}).items():
                add(rel, "UTTAL", word, f"uttal/{Path(rel).stem}")

    if not sample and (not only or only == "lasebok"):
        for path in sorted((DIST / "lasebok").glob("lb*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            blocks_from(doc, path.stem)

    return units


def missing_only(units: list[Unit]) -> list[Unit]:
    return [u for u in units if not (AUDIO_OUT / u.rel_path).exists()]


def pcm_to_mp3(pcm: bytes, mp3_path: Path, sample_rate: int = 24000) -> None:
    """Gemini TTS returns raw PCM s16le @ 24 kHz; encode as mono MP3."""
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "s16le", "-ar", str(sample_rate), "-ac", "1", "-i", "pipe:0",
        "-codec:a", "libmp3lame", "-qscale:a", "5",
        str(mp3_path),
    ]
    p = subprocess.run(cmd, input=pcm, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {p.stderr.decode(errors='replace')}")


def _describe_block(response) -> str:
    try:
        fb = getattr(response, "prompt_feedback", None)
        if fb is not None and getattr(fb, "block_reason", None):
            br = fb.block_reason
            return f"prompt blocked: {getattr(br, 'name', br)}"
        cands = getattr(response, "candidates", None)
        if not cands:
            return "no candidates in response"
        if getattr(cands[0], "content", None) is None:
            fr = getattr(cands[0], "finish_reason", None)
            return f"no content (finish_reason={getattr(fr, 'name', fr)})"
        return "no audio part in content"
    except Exception as e:  # pragma: no cover
        return f"<error reading response: {e!r}>"


def _pcm_from_response(response) -> bytes:
    cands = getattr(response, "candidates", None)
    if not cands or getattr(cands[0], "content", None) is None:
        raise RuntimeError(_describe_block(response))
    for part in cands[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            return inline.data
    raise RuntimeError("no audio part in content")


def _speech_config(voice: str):
    from google.genai import types
    return types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice),
            ),
        ),
    )


def request_text(voice_map: dict, u: Unit) -> str:
    entry = voice_map.get(u.speaker) or voice_map.get("NARRATOR") or {}
    style = (entry.get("style") or "").strip()
    return f"{style}\n\n{u.text}" if style else u.text


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--sample", default=None, metavar="kapNN",
                    help="Render one chapter synchronously (voice audition).")
    ap.add_argument("--only", choices=["chapters", "lasebok", "uttal"], default=None)
    ap.add_argument("--batch", action="store_true",
                    help="Use batchGenerateContent (~50%% cost, async).")
    ap.add_argument("--dry-run", action="store_true",
                    help="List what would render + a cost estimate; no API calls.")
    ap.add_argument("--force", action="store_true",
                    help="Re-render even if the file exists.")
    ap.add_argument("--poll-interval", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--sleep", type=float, default=0.5,
                    help="(sync mode) pause between calls.")
    args = ap.parse_args()

    voice_map = load_voice_map()
    units = collect_units(only=args.only, sample=args.sample)
    todo = units if args.force else missing_only(units)
    done = len(units) - len(todo)

    chars = sum(len(u.text) for u in todo)
    est_sec = chars / 13.0
    print(f"[audio] {len(units)} clips total; {done} already on disk; {len(todo)} to render")
    print(f"[audio] ~{chars:,} chars ≈ {est_sec/60:.0f} min audio; "
          f"pro-TTS batch ≈ ${est_sec*25/1e6*10:.2f}, sync ≈ ${est_sec*25/1e6*20:.2f}")
    if args.dry_run or not todo:
        by_voice: dict[str, int] = {}
        for u in todo:
            v = (voice_map.get(u.speaker) or {}).get("voice", FALLBACK_VOICE)
            by_voice[v] = by_voice.get(v, 0) + 1
        for v, n in sorted(by_voice.items(), key=lambda x: -x[1]):
            print(f"  voice {v}: {n} clips")
        return 0

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[err] no API key — set GEMINI_API_KEY (or pass --api-key)", file=sys.stderr)
        return 1
    from google import genai
    client = genai.Client(api_key=api_key)

    def write_unit(u: Unit, response) -> None:
        pcm = _pcm_from_response(response)
        pcm_to_mp3(pcm, AUDIO_OUT / u.rel_path)
        print(f"  [ok  ] {u.rel_path}")

    if args.batch:
        from _batch import BatchItem, run_batch
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        total_ok = total_fail = 0
        # one batch series per voice: every request in a job shares one config
        by_voice: dict[str, list[Unit]] = {}
        for u in todo:
            v = (voice_map.get(u.speaker) or {}).get("voice", FALLBACK_VOICE)
            by_voice.setdefault(v, []).append(u)
        for voice, group in by_voice.items():
            items = [
                BatchItem(id=u.id, contents=request_text(voice_map, u),
                          out_path=AUDIO_OUT / u.rel_path)
                for u in group
            ]
            lookup = {u.id: u for u in group}
            print(f"\n[audio] voice {voice}: {len(items)} clips")
            ok, fail = run_batch(
                client, model=args.model, items=items,
                config=_speech_config(voice),
                state_file=STATE_DIR / f"audio-{voice}.json",
                handler=lambda it, resp: write_unit(lookup[it.id], resp),
                poll_interval=args.poll_interval,
                display_name=f"spsi-audio-{voice}",
                batch_size=args.batch_size,
                between_chunks_sleep=5.0,
            )
            total_ok += ok
            total_fail += fail
        print(f"\n[audio] done: {total_ok} ok, {total_fail} failed")
        return 0 if total_fail == 0 else 2

    # sync mode
    fails = 0
    for u in todo:
        voice = (voice_map.get(u.speaker) or {}).get("voice", FALLBACK_VOICE)
        try:
            resp = client.models.generate_content(
                model=args.model, contents=request_text(voice_map, u),
                config=_speech_config(voice),
            )
            write_unit(u, resp)
        except Exception as e:
            print(f"  [fail] {u.rel_path}: {e}")
            fails += 1
        time.sleep(args.sleep)
    print(f"[audio] done: {len(todo)-fails} ok, {fails} failed")
    return 0 if fails == 0 else 2


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())

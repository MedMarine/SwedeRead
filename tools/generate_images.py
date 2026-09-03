#!/usr/bin/env python3
"""Batch illustration generation via Gemini image models.

Renders one wide JPG per chapter from the `illustration:` brief in each
chapters/kapNN.yaml. Chapters 1-6 already have hand-authored labeled SVGs
(build_reader prefers .svg over .jpg), so the default range is 7-30.

Consistency without reference sheets: every prompt gets the same STYLE + CAST
preamble, so faces, palette and technique hold across the book. If a
character drifts badly in one image, re-render just that chapter:

  python tools/generate_images.py --chapters 12 --force

Typical invocations:
  python tools/generate_images.py --dry-run
  python tools/generate_images.py --chapters 7-30 --batch
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
IMG_OUT = ROOT / "web" / "dist" / "images"
STATE_DIR = ROOT / "tools" / ".batch-state"

DEFAULT_MODEL = "gemini-3-pro-image-preview"

STYLE = """\
Wide-aspect (4:3) illustration for a Swedish graded reader in the spirit of
classic Scandinavian children's books. Technique: warm watercolor with soft
ink outlines, generous white paper margins, gentle Nordic light. Palette:
falu red (#8a3033) buildings, lake blue, birch green, straw yellow. NO text,
NO letters, NO captions anywhere in the image. Wholesome, calm, storybook —
never cartoonish or exaggerated.

Recurring cast (keep faces and clothes consistent):
- Anders Berg, 41: tall father, short brown beard, practical carpenter's
  shirt, calm.
- Karin Berg, 39: mother, warm smile, dark blond hair pinned up, cardigan.
- Oskar, 12: wiry boy, unruly brown hair, always mid-motion, untied shoelace.
- Nils, 10: neat boy, round glasses, book usually near him.
- Astrid, 7: small girl, blond braids, flower-patterned dress, often with a
  rag doll (Lisa).
- Ludde: large golden retriever, joyful. Misse: slim grey cat, dignified.
- Morfar Sven, 73: farmer, flat cap, suspenders. Farmor Ingrid, 70: elegant
  grandmother, silver bun.
- Lasse, 28: young sailor, dark knit sweater. Maria, 26: laughing woman,
  long brown hair.
Setting: Sjövik, a tiny Swedish lakeside town in Småland — red cottages,
a birch by the house, a small lake (Björksjön), forest behind.

Scene for this chapter:
"""


def parse_range(spec: str) -> list[int]:
    out: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            lo, hi = chunk.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(chunk))
    return sorted(n for n in out if 1 <= n <= 30)


def collect(chapter_nums: list[int], force: bool) -> list[tuple[int, str, Path]]:
    jobs = []
    for n in chapter_nums:
        path = CHAPTERS / f"kap{n:02d}.yaml"
        if not path.exists():
            continue
        ch = yaml.safe_load(path.read_text(encoding="utf-8"))
        brief = (ch.get("illustration") or "").strip()
        if not brief:
            print(f"[warn] kap{n:02d} has no illustration brief; skipping")
            continue
        dst = IMG_OUT / f"kap{n:02d}.jpg"
        svg = IMG_OUT / f"kap{n:02d}.svg"
        if svg.exists() and not force:
            print(f"[skip] kap{n:02d}: hand-authored SVG takes precedence")
            continue
        if dst.exists() and not force:
            continue
        jobs.append((n, STYLE + brief, dst))
    return jobs


def save_as_jpeg(raw: bytes, dst: Path) -> None:
    from PIL import Image
    dst.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.save(dst, format="JPEG", quality=88, optimize=True, progressive=True)


def _image_bytes(response) -> bytes:
    cands = getattr(response, "candidates", None)
    if not cands or getattr(cands[0], "content", None) is None:
        raise RuntimeError("no content in response")
    for part in cands[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            return inline.data
    raise RuntimeError("no image part in content")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chapters", default="7-30")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="Re-render even if a jpg (or SVG) exists.")
    ap.add_argument("--poll-interval", type=int, default=30)
    args = ap.parse_args()

    jobs = collect(parse_range(args.chapters), args.force)
    print(f"[img] {len(jobs)} images to render")
    for n, _p, dst in jobs:
        print(f"  kap{n:02d} -> {dst.relative_to(ROOT)}")
    if args.dry_run or not jobs:
        return 0

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[err] no API key — set GEMINI_API_KEY (or pass --api-key)", file=sys.stderr)
        return 1
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])

    if args.batch:
        from _batch import BatchItem, run_batch
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        items = [BatchItem(id=f"kap{n:02d}", contents=prompt, out_path=dst)
                 for n, prompt, dst in jobs]

        def handle(it, response):
            save_as_jpeg(_image_bytes(response), it.out_path)
            print(f"  [ok  ] {it.out_path.name}")

        ok, fail = run_batch(
            client, model=args.model, items=items, config=config,
            state_file=STATE_DIR / "images.json", handler=handle,
            poll_interval=args.poll_interval, display_name="spsi-images",
            batch_size=30,
        )
        print(f"[img] done: {ok} ok, {fail} failed")
        return 0 if fail == 0 else 2

    fails = 0
    for n, prompt, dst in jobs:
        try:
            resp = client.models.generate_content(
                model=args.model, contents=prompt, config=config)
            save_as_jpeg(_image_bytes(resp), dst)
            print(f"  [ok  ] {dst.name}")
        except Exception as e:
            print(f"  [fail] kap{n:02d}: {e}")
            fails += 1
    print(f"[img] done: {len(jobs)-fails} ok, {fails} failed")
    return 0 if fails == 0 else 2


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())

"""Shared batch-generation helpers for the audio + image pipelines.

Google's `batchGenerateContent` endpoint charges ~50% of synchronous cost and
is the correct path for "text is locked, render everything now" workflows.
The tradeoff is async: jobs can take minutes to hours to finish. This helper:

  - Submits inline batch jobs from an in-memory request list
  - Persists the job name so interrupted runs can resume polling
  - Polls with a display of elapsed time + state transitions
  - Yields per-request responses in submission order
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

# We keep these as strings so we don't need to import types at module load —
# the SDK's enum values compare cleanly as strings.
TERMINAL_STATES = {
    "JOB_STATE_SUCCEEDED",
    "JOB_STATE_PARTIALLY_SUCCEEDED",
    "JOB_STATE_FAILED",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED",
}
INFLIGHT_STATES = {
    "JOB_STATE_QUEUED",
    "JOB_STATE_PENDING",
    "JOB_STATE_RUNNING",
    "JOB_STATE_UPDATING",
    "JOB_STATE_UNSPECIFIED",
}


@dataclass
class BatchItem:
    """One request in a batch, carrying the output target alongside the payload."""
    id: str                 # e.g. "ch01" or "ch01/p05"
    contents: list          # genai `contents` list — text + image objects
    out_path: Path          # where to write the response
    extra: dict | None = None  # per-request metadata (voice name, etc.)


def _state_name(job) -> str:
    s = getattr(job, "state", None)
    if s is None:
        return "JOB_STATE_UNSPECIFIED"
    # SDK exposes state as an enum with .name
    return getattr(s, "name", str(s))


def load_state(state_file: Path) -> dict | None:
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_state(state_file: Path, data: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def submit_batch(client, model: str, items: list[BatchItem], config,
                 display_name: str | None = None):
    """Submit an inline batch job. Returns the BatchJob object."""
    from google.genai import types

    requests = []
    for it in items:
        req = types.InlinedRequest(
            contents=it.contents,
            config=config,
            metadata={"id": it.id},
        )
        requests.append(req)

    job = client.batches.create(
        model=model,
        src=requests,
        config=types.CreateBatchJobConfig(display_name=display_name) if display_name else None,
    )
    return job


def poll_job(
    client,
    job_name: str,
    *,
    poll_interval: int = 30,
    timeout: int = 24 * 3600,
    heartbeat_interval: int = 300,
):
    """Block until the job reaches a terminal state (or timeout).

    Prints to stdout on every state transition (QUEUED → RUNNING → terminal)
    and a heartbeat every `heartbeat_interval` seconds in between, so the
    caller can see the script is alive even when the Gemini job sits in
    RUNNING for an hour.
    """
    start = time.time()
    last_state = None
    last_heartbeat = 0.0
    while True:
        job = client.batches.get(name=job_name)
        state = _state_name(job)
        now = time.time()
        elapsed = int(now - start)
        if state != last_state:
            print(f"  [batch] {job_name}  state={state}  elapsed={elapsed}s", flush=True)
            last_state = state
            last_heartbeat = now
        elif now - last_heartbeat >= heartbeat_interval:
            # Same state, but we want a sign of life every few minutes.
            print(f"  [batch] {job_name}  still {state}  elapsed={elapsed}s", flush=True)
            last_heartbeat = now
        if state in TERMINAL_STATES:
            return job
        if now - start > timeout:
            raise TimeoutError(f"batch poll timeout after {timeout}s; state={state}")
        time.sleep(poll_interval)


def _response_id(resp) -> str | None:
    meta = getattr(resp, "metadata", None)
    if meta is None:
        return None
    if isinstance(meta, dict):
        return meta.get("id")
    return getattr(meta, "id", None) or (meta.get("id") if hasattr(meta, "get") else None)


def items_fingerprint(items: list[BatchItem]) -> str:
    """Stable fingerprint of a batch's identity (ids in order)."""
    return hashlib.sha1("\n".join(it.id for it in items).encode("utf-8")).hexdigest()


def iter_responses(job, items: list[BatchItem]) -> Iterator[tuple[BatchItem, Any]]:
    """Match inline_responses back to their submission items.

    Every request is submitted with metadata={"id": item.id}; when the
    responses echo that metadata we match by id, which survives partial
    success with missing responses anywhere in the list. Only when no
    response carries an id do we fall back to positional matching — and a
    count mismatch in that mode is loud, because positional matching with
    a hole would attach output to the wrong item silently.
    """
    inlined = []
    dest = getattr(job, "dest", None)
    if dest is not None:
        inlined = list(getattr(dest, "inlined_responses", []) or [])

    by_id = {}
    ids_seen = 0
    for resp in inlined:
        rid = _response_id(resp)
        if rid is not None:
            by_id[rid] = resp
            ids_seen += 1

    if inlined and ids_seen == len(inlined):
        for it in items:
            yield it, by_id.get(it.id)
        return

    # Positional fallback (SDK/dest variant without metadata echo).
    if len(inlined) != len(items):
        print(f"  [warn] batch returned {len(inlined)} responses for {len(items)} "
              f"items without ids — positional match may misattribute; "
              f"treating non-trailing gaps as misses", flush=True)
    for i, it in enumerate(items):
        resp = inlined[i] if i < len(inlined) else None
        yield it, resp


def _run_batch_chunk(
    client,
    *,
    model: str,
    items: list[BatchItem],
    config,
    state_file: Path,
    handler: Callable[[BatchItem, Any], None],
    poll_interval: int,
    display_name: str | None,
) -> tuple[int, int]:
    """Submit one inline batch (no chunking), poll it, dispatch responses."""
    state = load_state(state_file) or {}
    job = None

    # Resume only when the saved job provably belongs to THESE items: model
    # and an id-fingerprint must match. (Count-only matching once allowed a
    # different same-size selection to silently reuse a stale job's outputs.)
    if (state.get("job_name") and state.get("model") == model
            and state.get("items_fp") == items_fingerprint(items)):
        try:
            existing = client.batches.get(name=state["job_name"])
            st = _state_name(existing)
            if st in INFLIGHT_STATES:
                print(f"[batch] resuming existing job {existing.name} (state={st})")
                job = existing
            elif st in TERMINAL_STATES:
                print(f"[batch] previous job {existing.name} already {st}; reusing its results")
                job = existing
        except Exception as e:
            print(f"[batch] could not resume ({e}); submitting fresh")

    if job is None:
        print(f"[batch] submitting {len(items)} inline requests to {model}")
        job = submit_batch(client, model, items, config, display_name=display_name)
        save_state(state_file, {
            "job_name": job.name,
            "model": model,
            "count": len(items),
            "items_fp": items_fingerprint(items),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        })

    if _state_name(job) in INFLIGHT_STATES:
        job = poll_job(client, job.name, poll_interval=poll_interval)

    final_state = _state_name(job)
    print(f"[batch] chunk finished in state={final_state}")
    if final_state == "JOB_STATE_FAILED":
        err = getattr(job, "error", None)
        raise RuntimeError(f"batch chunk failed: {getattr(err, 'message', err)}")

    ok = 0
    fail = 0
    for it, resp in iter_responses(job, items):
        if resp is None:
            print(f"  [miss] {it.id}: no response in batch output", flush=True)
            fail += 1
            continue
        resp_error = getattr(resp, "error", None)
        if resp_error is not None:
            print(f"  [err ] {it.id}: {getattr(resp_error, 'message', resp_error)}", flush=True)
            fail += 1
            continue
        try:
            handler(it, resp.response)
            ok += 1
        except Exception as e:
            print(f"  [hnd ] {it.id}: {e}", flush=True)
            fail += 1

    if final_state in ("JOB_STATE_SUCCEEDED", "JOB_STATE_PARTIALLY_SUCCEEDED"):
        try:
            state_file.unlink()
        except FileNotFoundError:
            pass
    else:
        # CANCELLED / EXPIRED: keep the state file so the job can be
        # inspected (and the miss list reconstructed) before resubmitting.
        print(f"[batch] keeping state file for inspection: {state_file}", flush=True)

    return ok, fail


def run_batch(
    client,
    *,
    model: str,
    items: list[BatchItem],
    config,                                    # GenerateContentConfig (same for every request)
    state_file: Path,                          # base persistence file path (per-chunk variants derived)
    handler: Callable[[BatchItem, Any], None], # called once per (item, response) — writes to disk
    poll_interval: int = 30,
    display_name: str | None = None,
    batch_size: int = 100,                     # Gemini's inline-batch cap is around this
    between_chunks_sleep: float = 0.0,         # pause between chunk submissions (rate-limit guard)
) -> tuple[int, int]:
    """Submit → poll → dispatch with automatic chunking.

    Gemini's batchGenerateContent rejects very large inline payloads (the
    symptom is a 429 RESOURCE_EXHAUSTED on submit). We slice `items` into
    chunks of `batch_size`, submit each sequentially, and aggregate results.

    Each chunk has its own state file so a Ctrl-C between chunks is safe:
    rerunning picks up where the last chunk finished.
    """
    if not items:
        return 0, 0

    chunks = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    total_chunks = len(chunks)
    total_ok = total_fail = 0

    for idx, chunk in enumerate(chunks, start=1):
        # Per-chunk state file so resume works granularly
        chunk_state = state_file.parent / f"{state_file.stem}-chunk{idx:02d}of{total_chunks:02d}{state_file.suffix}"
        chunk_name = f"{display_name}-c{idx:02d}of{total_chunks:02d}" if display_name else None
        print(f"\n[batch] chunk {idx}/{total_chunks}  ({len(chunk)} items)")
        try:
            ok, fail = _run_batch_chunk(
                client, model=model, items=chunk, config=config,
                state_file=chunk_state, handler=handler,
                poll_interval=poll_interval, display_name=chunk_name,
            )
        except Exception as e:
            # Log and continue — remaining chunks may still succeed; the
            # state file persists so a retry resumes this chunk.
            print(f"[batch] chunk {idx} error: {e}", flush=True)
            total_fail += len(chunk)
            continue
        total_ok += ok
        total_fail += fail

        # Pause between chunks when the user asked for one — helps against
        # per-minute request quotas on top of the per-batch size cap.
        if between_chunks_sleep and idx < total_chunks:
            import time as _time
            _time.sleep(between_chunks_sleep)

    return total_ok, total_fail

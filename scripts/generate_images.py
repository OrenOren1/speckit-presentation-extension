#!/usr/bin/env python3
"""
generate_images.py — image generation for the speckit-presentation extension.

Reads `presentation/spec.md`, picks the prompts for the requested slides,
calls a provider (Gemini preferred, OpenAI fallback), writes PNGs to
`presentation/assets/images/slide-NN.png`, optionally uploads to ImgBB.

Mirrors the conventions of the blog-post skill so the same `.env` and the
same key files (`.googleAI-token`, `.gemini-api-key`, `.imgbb-token`) work
across both toolchains.

Usage:
    python generate_images.py --spec presentation/spec.md --slides all
    python generate_images.py --spec presentation/spec.md --slides 3,7
    python generate_images.py --spec presentation/spec.md --slides 7 \
        --provider openai --model dall-e-3

Exit codes:
    0 = all requested slides generated
    1 = some slides failed (see JSON report on stdout)
    2 = no usable provider key found (nothing attempted)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# --- Constants ----------------------------------------------------------------

ASSETS_DIR = "assets/images"
DEFAULT_SIZE_16_9 = "1792x1024"
DEFAULT_NEGATIVE = "text, watermarks, logos"

# --- Key resolution -----------------------------------------------------------


def _read_lines_file(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _load_dotenv(repo_root: Path) -> None:
    """Minimal .env loader — KEY=VALUE per line, no quoting magic."""
    dotenv = repo_root / ".env"
    if not dotenv.is_file():
        return
    for raw in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def resolve_gemini_keys(repo_root: Path) -> list[str]:
    """Resolve Gemini keys: env (single + multi) → key files (one per line)."""
    keys: list[str] = []
    single = os.environ.get("GEMINI_API_KEY")
    if single:
        keys.append(single.strip())
    multi = os.environ.get("GEMINI_API_KEYS", "")
    keys.extend(
        k.strip() for k in re.split(r"[\n,]", multi) if k.strip()
    )
    for fname in (".googleAI-token", ".gemini-api-key"):
        keys.extend(_read_lines_file(repo_root / fname))
    # Dedupe, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def resolve_openai_key(_: Path) -> str | None:
    return os.environ.get("OPENAI_API_KEY") or None


def resolve_imgbb_key(repo_root: Path) -> str | None:
    env_key = os.environ.get("IMGBB_API_KEY")
    if env_key:
        return env_key.strip()
    file_keys = _read_lines_file(repo_root / ".imgbb-token")
    return file_keys[0] if file_keys else None


# --- Spec parsing -------------------------------------------------------------


@dataclass
class Slide:
    number: int
    id: str
    title: str
    image_prompt: str | None = None
    image_style: str | None = None


def parse_spec(spec_path: Path) -> tuple[dict, list[Slide]]:
    """Very lenient spec.md parser — extracts frontmatter + ### Slide NN blocks."""
    raw = spec_path.read_text(encoding="utf-8")
    fm: dict = {}
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            try:
                import yaml  # type: ignore
                fm = yaml.safe_load(raw[3:end]) or {}
            except ImportError:
                # Tiny fallback: extract image_style only
                m = re.search(r"^image_style:\s*\"?(.+?)\"?$", raw[3:end], re.M)
                if m:
                    fm = {"image_style": m.group(1)}
            body = raw[end + 4 :]
    slides: list[Slide] = []
    blocks = re.split(r"\n###\s+Slide\s+(\d+)\s*\n", body)
    # blocks = [pre, N1, block1, N2, block2, ...]
    for i in range(1, len(blocks), 2):
        number = int(blocks[i])
        block = blocks[i + 1]

        def field_of(name: str) -> str | None:
            m = re.search(rf"^-\s+\*\*{name}\*\*:\s*(.+?)$", block, re.M)
            return m.group(1).strip() if m else None

        slides.append(
            Slide(
                number=number,
                id=field_of("id") or f"s{number:02d}",
                title=field_of("title") or "(untitled)",
                image_prompt=field_of("image_prompt"),
                image_style=field_of("image_style") or fm.get("image_style"),
            )
        )
    return fm, slides


# --- Providers ----------------------------------------------------------------


class ProviderError(Exception):
    """Raised when a provider call fails (signals chain to try the next one)."""


def gemini_generate(prompt: str, keys: list[str], model: str) -> bytes:
    """Call Gemini image generation; rotate keys on 429/401/403."""
    try:
        import google.genai as genai  # type: ignore
        from google.genai import types  # type: ignore
    except ImportError as exc:
        raise ProviderError(
            "google-genai SDK not installed (pip install google-genai)"
        ) from exc

    last_err: Exception | None = None
    for key in keys:
        try:
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model=model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            for part in resp.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    data = part.inline_data.data
                    return data if isinstance(data, bytes) else base64.b64decode(data)
            raise ProviderError("Gemini returned no image bytes")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            msg = str(exc).lower()
            if any(code in msg for code in ("429", "401", "403", "quota", "permission")):
                continue  # rotate to next key
            break
    raise ProviderError(f"Gemini failed: {last_err}")


def openai_generate(prompt: str, key: str, model: str) -> bytes:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise ProviderError(
            "openai SDK not installed (pip install openai)"
        ) from exc
    client = OpenAI(api_key=key)
    try:
        result = client.images.generate(
            model=model, prompt=prompt, size=DEFAULT_SIZE_16_9, n=1
        )
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"OpenAI DALL-E failed: {exc}") from exc
    b64 = result.data[0].b64_json
    if not b64:
        # Some SDK versions return only a URL; fetch it.
        import urllib.request

        url = result.data[0].url
        if not url:
            raise ProviderError("OpenAI returned neither b64 nor URL")
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
            return resp.read()
    return base64.b64decode(b64)


# --- ImgBB upload -------------------------------------------------------------


def imgbb_upload(image_bytes: bytes, api_key: str, name: str) -> str:
    import urllib.parse
    import urllib.request

    payload = urllib.parse.urlencode(
        {
            "key": api_key,
            "image": base64.b64encode(image_bytes).decode("ascii"),
            "name": name,
        }
    ).encode("ascii")
    req = urllib.request.Request(
        "https://api.imgbb.com/1/upload",
        data=payload,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        body = json.load(resp)
    if not body.get("success"):
        raise RuntimeError(f"ImgBB upload failed: {body}")
    return body["data"]["url"]


# --- Orchestration ------------------------------------------------------------


@dataclass
class GenerationResult:
    slide: int
    title: str
    status: str  # "ok" | "failed" | "skipped"
    local_path: str | None = None
    remote_url: str | None = None
    provider: str | None = None
    model: str | None = None
    error: str | None = None
    prompt_b64url: str | None = None
    archive_comment: str | None = None


def _resolve_slides(slides: list[Slide], spec: str) -> list[Slide]:
    if spec == "all":
        return [s for s in slides if s.image_prompt and s.image_prompt.lower() != "none"]
    wanted = {int(x) for x in spec.split(",") if x.strip()}
    return [s for s in slides if s.number in wanted and s.image_prompt and s.image_prompt.lower() != "none"]


def _b64url(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii").rstrip("=")


def generate(
    repo_root: Path,
    spec_path: Path,
    which: str,
    forced_provider: str | None,
    forced_model: str | None,
) -> tuple[int, list[GenerationResult]]:
    _load_dotenv(repo_root)
    fm, slides = parse_spec(spec_path)
    targets = _resolve_slides(slides, which)
    if not targets:
        return 0, []

    gemini_keys = resolve_gemini_keys(repo_root)
    openai_key = resolve_openai_key(repo_root)
    imgbb_key = resolve_imgbb_key(repo_root)

    if not gemini_keys and not openai_key:
        return 2, [
            GenerationResult(
                slide=t.number,
                title=t.title,
                status="skipped",
                error="no provider key found (GEMINI_API_KEY / GEMINI_API_KEYS / OPENAI_API_KEY)",
            )
            for t in targets
        ]

    images_dir = repo_root / "presentation" / ASSETS_DIR
    images_dir.mkdir(parents=True, exist_ok=True)

    results: list[GenerationResult] = []
    any_failed = False

    for slide in targets:
        prompt = (slide.image_prompt or "").strip()
        if not prompt:
            results.append(
                GenerationResult(
                    slide=slide.number,
                    title=slide.title,
                    status="skipped",
                    error="empty prompt",
                )
            )
            continue

        full_prompt = prompt
        if slide.image_style:
            full_prompt = f"{slide.image_style}. {prompt}"

        image_bytes: bytes | None = None
        used_provider: str | None = None
        used_model: str | None = None
        last_err: str | None = None

        chain = []
        if forced_provider == "openai" and openai_key:
            chain = [("openai", forced_model or "dall-e-3")]
        elif forced_provider == "gemini" and gemini_keys:
            chain = [("gemini", forced_model or "gemini-2.5-flash-image")]
        else:
            if gemini_keys:
                chain.append(("gemini", forced_model or "gemini-2.5-flash-image"))
            if openai_key:
                chain.append(("openai", forced_model or "dall-e-3"))

        for provider, model in chain:
            try:
                if provider == "gemini":
                    image_bytes = gemini_generate(full_prompt, gemini_keys, model)
                else:
                    image_bytes = openai_generate(full_prompt, openai_key or "", model)
                used_provider, used_model = provider, model
                break
            except ProviderError as exc:
                last_err = str(exc)
                continue

        if image_bytes is None:
            any_failed = True
            results.append(
                GenerationResult(
                    slide=slide.number,
                    title=slide.title,
                    status="failed",
                    error=last_err or "all providers failed",
                )
            )
            continue

        local_path = images_dir / f"slide-{slide.number:02d}.png"
        local_path.write_bytes(image_bytes)

        remote_url: str | None = None
        if imgbb_key:
            try:
                remote_url = imgbb_upload(
                    image_bytes, imgbb_key, f"slide-{slide.number:02d}"
                )
            except Exception as exc:  # noqa: BLE001
                last_err = f"imgbb upload failed (kept local): {exc}"

        prompt_b64 = _b64url(prompt)
        archive = f"<!-- image_prompt:archive index={slide.number:02d} b64={prompt_b64} -->"

        results.append(
            GenerationResult(
                slide=slide.number,
                title=slide.title,
                status="ok",
                local_path=str(local_path.relative_to(repo_root)),
                remote_url=remote_url,
                provider=used_provider,
                model=used_model,
                error=last_err if last_err and remote_url is None else None,
                prompt_b64url=prompt_b64,
                archive_comment=archive,
            )
        )
        # Politeness: small delay so we don't hammer the provider on big batches
        time.sleep(0.2)

    exit_code = 1 if any_failed else 0
    return exit_code, results


# --- CLI ---------------------------------------------------------------------


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--spec", required=True, help="path to presentation/spec.md")
    p.add_argument(
        "--slides",
        default="all",
        help="comma-separated slide numbers, or 'all' (default)",
    )
    p.add_argument("--provider", choices=["gemini", "openai"], default=None)
    p.add_argument("--model", default=None)
    p.add_argument(
        "--repo-root",
        default=".",
        help="repo root (used for .env, key files); default: cwd",
    )
    args = p.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    spec_path = Path(args.spec).resolve()
    if not spec_path.is_file():
        print(json.dumps({"error": f"spec not found: {spec_path}"}), file=sys.stderr)
        return 2

    code, results = generate(
        repo_root=repo_root,
        spec_path=spec_path,
        which=args.slides,
        forced_provider=args.provider,
        forced_model=args.model,
    )
    print(
        json.dumps(
            {
                "status": "ok" if code == 0 else "partial" if code == 1 else "no_keys",
                "results": [r.__dict__ for r in results],
            },
            indent=2,
        )
    )
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

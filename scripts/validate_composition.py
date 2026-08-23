from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
HEX_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
WRAPPERS = {"parentheses", "braces"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_yaml(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path}: use JSON-compatible YAML syntax; parse error at "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError("composition root must be an object")
    return value


def validate(path: Path) -> tuple[dict[str, Any], list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict[str, Any] = {}

    try:
        cfg = load_json_yaml(path)
    except (OSError, ValueError) as exc:
        return {}, [str(exc)], [], facts

    def obj(name: str) -> dict[str, Any]:
        value = cfg.get(name)
        if not isinstance(value, dict):
            errors.append(f"{name} must be an object")
            return {}
        return value

    if cfg.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    source_cfg = obj("source")
    canvas = obj("canvas")
    photo = obj("photo")
    typography = obj("typography")
    sentence = obj("sentence")
    render = obj("render")

    source_value = source_cfg.get("path")
    if not isinstance(source_value, str) or not source_value.strip():
        errors.append("source.path must be a non-empty string")
        source_path = path.parent / "__missing_source__"
    else:
        source_path = (path.parent / source_value).resolve() if not Path(source_value).is_absolute() else Path(source_value)
        if not source_path.is_file():
            errors.append(f"source image does not exist: {source_path}")
        else:
            try:
                with Image.open(source_path) as opened:
                    source_image = ImageOps.exif_transpose(opened)
                    facts["source_size"] = source_image.size
            except Exception as exc:
                errors.append(f"cannot open source image: {exc}")

    expected_hash = source_cfg.get("sha256")
    if expected_hash not in (None, ""):
        if not isinstance(expected_hash, str) or not HEX_SHA256.fullmatch(expected_hash):
            errors.append("source.sha256 must be a 64-character hexadecimal digest")
        elif source_path.is_file() and sha256_file(source_path).lower() != expected_hash.lower():
            errors.append("source.sha256 does not match the source file")

    def positive_int(container: dict[str, Any], key: str, scope: str) -> int:
        value = container.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{scope}.{key} must be a positive integer")
            return 1
        return value

    canvas_w = positive_int(canvas, "width", "canvas")
    canvas_h = positive_int(canvas, "height", "canvas")
    photo_w = positive_int(photo, "width", "photo")
    if photo_w != canvas_w:
        errors.append("photo.width must equal canvas.width in schema 1.0")
    if photo.get("anchor") != "bottom":
        errors.append("photo.anchor must be 'bottom'")
    background = canvas.get("background")
    if not isinstance(background, str) or not HEX_COLOR.fullmatch(background):
        errors.append("canvas.background must be a #RRGGBB color")

    font_size = positive_int(typography, "font_size_px", "typography")
    line_height = positive_int(typography, "line_height_px", "typography")
    positive_int(typography, "token_gap_px", "typography")
    positive_int(typography, "upper_padding_px", "typography")
    if line_height < font_size:
        warnings.append("typography.line_height_px is smaller than font_size_px")
    color = typography.get("color")
    if not isinstance(color, str) or not HEX_COLOR.fullmatch(color):
        errors.append("typography.color must be a #RRGGBB color")
    language = typography.get("language")
    if not isinstance(language, str) or not language.strip():
        errors.append("typography.language must be a non-empty language tag")
    font_file = typography.get("font_file")
    if font_file not in (None, "") and not isinstance(font_file, str):
        errors.append("typography.font_file must be null or a path string")
    elif isinstance(font_file, str) and font_file:
        resolved_font = (path.parent / font_file).resolve() if not Path(font_file).is_absolute() else Path(font_file)
        if not resolved_font.is_file():
            errors.append(f"typography.font_file does not exist: {resolved_font}")

    policy = sentence.get("wrapper_policy")
    if not isinstance(policy, dict):
        errors.append("sentence.wrapper_policy must be an object")
        policy = {}
    choices = policy.get("choices")
    if choices != ["parentheses", "braces"]:
        errors.append("wrapper_policy.choices must be ['parentheses', 'braces']")
    if policy.get("selection") != "random_per_composition":
        errors.append("wrapper_policy.selection must be 'random_per_composition'")
    resolved = policy.get("resolved")
    if resolved not in WRAPPERS:
        errors.append("wrapper_policy.resolved must be 'parentheses' or 'braces'")
    if not isinstance(policy.get("seed"), int) or isinstance(policy.get("seed"), bool):
        errors.append("wrapper_policy.seed must be an integer")
    plain_text = sentence.get("plain_text")
    if not isinstance(plain_text, str) or not plain_text.strip():
        errors.append("sentence.plain_text must be non-empty")
    copy_source = sentence.get("copy_source")
    if copy_source not in (None, "user_provided", "auto_generated"):
        errors.append("sentence.copy_source must be user_provided or auto_generated")

    tokens_value = cfg.get("tokens")
    if not isinstance(tokens_value, list) or not tokens_value:
        errors.append("tokens must be a non-empty array")
        tokens_value = []
    elif not 4 <= len(tokens_value) <= 7:
        errors.append("tokens must contain 4 to 7 items, selected according to the image")
    token_ids: list[str] = []
    display_heights: list[int] = []
    for index, token in enumerate(tokens_value):
        label = f"tokens[{index}]"
        if not isinstance(token, dict):
            errors.append(f"{label} must be an object")
            continue
        token_id = token.get("id")
        if not isinstance(token_id, str) or not token_id.strip():
            errors.append(f"{label}.id must be a non-empty string")
            continue
        token_ids.append(token_id)
        if "wrapper" in token:
            errors.append(f"{label}.wrapper is forbidden; all tokens inherit wrapper_policy.resolved")
        bbox = token.get("source_bbox")
        if not (
            isinstance(bbox, list)
            and len(bbox) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in bbox)
        ):
            errors.append(f"{label}.source_bbox must be four numbers [x,y,width,height]")
        else:
            x, y, width, height = [float(v) for v in bbox]
            if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1 or y + height > 1:
                errors.append(f"{label}.source_bbox must be positive and stay inside normalized source bounds")
            if width > 0.20 or height > 0.25 or width * height > 0.06:
                warnings.append(
                    f"{token_id}: review large crop "
                    f"(width={width:.3f}, height={height:.3f}, area={width * height:.3f})"
                )
        display_height = token.get("display_height_px")
        if not isinstance(display_height, int) or isinstance(display_height, bool) or display_height <= 0:
            errors.append(f"{label}.display_height_px must be a positive integer")
        else:
            display_heights.append(display_height)
        if not isinstance(token.get("semantic_role"), str) or not token.get("semantic_role", "").strip():
            errors.append(f"{label}.semantic_role must be non-empty")
        mask = token.get("mask")
        if not isinstance(mask, dict) or mask.get("enabled") is not True or mask.get("fill") != "canvas_background":
            errors.append(f"{label}.mask must be enabled and filled with canvas_background")

    duplicates = [token_id for token_id, count in Counter(token_ids).items() if count > 1]
    if duplicates:
        errors.append(f"token IDs must be unique: {', '.join(duplicates)}")

    if display_heights:
        minimum_safe_leading = max(font_size + 12, max(display_heights) + 16)
        compact_upper_guide = max(round(font_size * 2.4), max(display_heights) + 32)
        if line_height < minimum_safe_leading:
            errors.append(
                f"typography.line_height_px is too tight; use at least {minimum_safe_leading}px "
                "for the current font and token heights"
            )
        elif line_height > compact_upper_guide:
            warnings.append(
                f"typography.line_height_px is loose ({line_height}px); consider "
                f"{max(round(font_size * 2.15), max(display_heights) + 24)}px for a compact block"
            )

    lines = sentence.get("lines")
    references: list[str] = []
    if not isinstance(lines, list) or not lines:
        errors.append("sentence.lines must be a non-empty array")
    else:
        for line_index, line in enumerate(lines):
            if not isinstance(line, list) or not line:
                errors.append(f"sentence.lines[{line_index}] must be a non-empty array")
                continue
            for run_index, run in enumerate(line):
                label = f"sentence.lines[{line_index}][{run_index}]"
                if not isinstance(run, dict):
                    errors.append(f"{label} must be an object")
                    continue
                run_type = run.get("type")
                if run_type == "text":
                    if not isinstance(run.get("content"), str) or run.get("content") == "":
                        errors.append(f"{label}.content must be non-empty")
                elif run_type == "token":
                    token_id = run.get("token_id")
                    if not isinstance(token_id, str):
                        errors.append(f"{label}.token_id must be a string")
                    else:
                        references.append(token_id)
                else:
                    errors.append(f"{label}.type must be 'text' or 'token'")

    unknown = sorted(set(references) - set(token_ids))
    missing = sorted(set(token_ids) - set(references))
    repeated_refs = sorted(token_id for token_id, count in Counter(references).items() if count > 1)
    if unknown:
        errors.append(f"sentence references unknown tokens: {', '.join(unknown)}")
    if missing:
        errors.append(f"tokens not referenced in sentence: {', '.join(missing)}")
    if repeated_refs:
        errors.append(f"tokens must be referenced exactly once: {', '.join(repeated_refs)}")

    if render.get("engine") != "deterministic_pillow":
        errors.append("render.engine must be 'deterministic_pillow'")
    if render.get("generative_editing") is not False:
        errors.append("render.generative_editing must be false")

    if "source_size" in facts:
        source_w, source_h = facts["source_size"]
        photo_h = round(photo_w * source_h / source_w)
        facts.update({"photo_height": photo_h, "upper_height": canvas_h - photo_h})
        if photo_h >= canvas_h:
            errors.append("resized photo leaves no upper white region; increase canvas.height")

    facts.update({"source_path": source_path, "token_count": len(tokens_value)})
    return cfg, errors, warnings, facts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Visual Token Editorial composition.")
    parser.add_argument("composition", type=Path)
    args = parser.parse_args()
    path = args.composition.resolve()
    _, errors, warnings, facts = validate(path)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(
        f"PASS: {facts.get('token_count', 0)} token(s), "
        f"upper region {facts.get('upper_height', '?')} px, {len(warnings)} warning(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

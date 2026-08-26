from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from validate_composition import validate


def hex_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def bbox_px(box: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    x, y, box_width, box_height = [float(value) for value in box]
    return (
        round(x * width),
        round(y * height),
        round((x + box_width) * width),
        round((y + box_height) * height),
    )


def resolve_relative(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def load_font(config_dir: Path, typography: dict[str, Any]) -> tuple[ImageFont.FreeTypeFont, Path]:
    size = typography["font_size_px"]
    configured = typography.get("font_file")
    if configured:
        candidates = [resolve_relative(config_dir, configured)]
    elif str(typography.get("language", "en")).lower().split("-")[0] == "zh":
        candidates = [
            Path(r"C:\Windows\Fonts\Deng.ttf"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\msyhbd.ttc"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
        ]
    elif str(typography.get("language", "en")).lower().split("-")[0] in {"ja", "ko"}:
        candidates = [
            Path(r"C:\Windows\Fonts\meiryo.ttc"),
            Path(r"C:\Windows\Fonts\YuGothR.ttc"),
            Path(r"C:\Windows\Fonts\malgun.ttf"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
        ]
    else:
        candidates = [
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\calibri.ttf"),
        ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size), candidate
    raise FileNotFoundError("No supported neutral sans-serif font found; set typography.font_file")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Visual Token Editorial composition.")
    parser.add_argument("composition", type=Path)
    parser.add_argument("--output", type=Path, default=Path("final.png"))
    parser.add_argument("--qa", type=Path, default=Path("qa_report.md"))
    args = parser.parse_args()

    composition_path = args.composition.resolve()
    cfg, errors, warnings, facts = validate(composition_path)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    config_dir = composition_path.parent
    output_path = args.output if args.output.is_absolute() else config_dir / args.output
    qa_path = args.qa if args.qa.is_absolute() else config_dir / args.qa
    output_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.parent.mkdir(parents=True, exist_ok=True)

    source_path: Path = facts["source_path"]
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")

    canvas_cfg = cfg["canvas"]
    photo_cfg = cfg["photo"]
    typography = cfg["typography"]
    sentence = cfg["sentence"]
    canvas_w = canvas_cfg["width"]
    canvas_h = canvas_cfg["height"]
    background = hex_rgb(canvas_cfg["background"])
    text_color = hex_rgb(typography["color"])
    photo_w = photo_cfg["width"]
    photo_h = round(photo_w * source.height / source.width)
    photo_y = canvas_h - photo_h
    upper_h = photo_y
    padding = typography["upper_padding_px"]

    baseline = source.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
    masked = baseline.copy()
    mask_draw = ImageDraw.Draw(masked)
    token_by_id: dict[str, dict[str, Any]] = {}
    mask_boxes: list[tuple[int, int, int, int]] = []

    for token in cfg["tokens"]:
        source_box = bbox_px(token["source_bbox"], source.width, source.height)
        photo_box = bbox_px(token["source_bbox"], photo_w, photo_h)
        crop = source.crop(source_box)
        display_h = token["display_height_px"]
        display_w = max(1, round(crop.width * display_h / crop.height))
        display = crop.resize((display_w, display_h), Image.Resampling.LANCZOS)
        token_by_id[token["id"]] = {
            **token,
            "source_box": source_box,
            "photo_box": photo_box,
            "display": display,
        }
        x0, y0, x1, y1 = photo_box
        mask_draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=background)
        mask_boxes.append(photo_box)

    lower_diff = ImageChops.difference(masked, baseline)
    outside_diff = lower_diff.copy()
    outside_draw = ImageDraw.Draw(outside_diff)
    for x0, y0, x1, y1 in mask_boxes:
        outside_draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(0, 0, 0))
    outside_changed_pixels = 0
    if outside_diff.getbbox() is not None:
        outside_changed_pixels = sum(1 for pixel in outside_diff.getdata() if pixel != (0, 0, 0))

    masks_solid = True
    for box in mask_boxes:
        region = masked.crop(box)
        solid = Image.new("RGB", region.size, background)
        if ImageChops.difference(region, solid).getbbox() is not None:
            masks_solid = False
            break

    font, font_path = load_font(config_dir, typography)
    wrapper = sentence["wrapper_policy"]["resolved"]
    open_mark, close_mark = ("(", ")") if wrapper == "parentheses" else ("{", "}")
    line_height = typography["line_height_px"]
    token_gap = typography["token_gap_px"]
    lines = sentence["lines"]
    max_token_h = max(token["display"].height for token in token_by_id.values())
    work_margin = max(max_token_h, typography["font_size_px"]) + 24
    work_h = work_margin * 2 + max(0, len(lines) - 1) * line_height + max_token_h
    layer = Image.new("RGBA", (canvas_w, work_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def text_box(text: str) -> tuple[int, int, int, int]:
        return draw.textbbox((0, 0), text, font=font)

    def text_width(text: str) -> int:
        box = text_box(text)
        return box[2] - box[0]

    max_wrapper_center_error = 0.0
    max_wrapper_baseline_error = 0.0

    for line_index, runs in enumerate(lines):
        widths: list[int] = []
        for run in runs:
            if run["type"] == "text":
                widths.append(text_width(run["content"]))
            else:
                display = token_by_id[run["token_id"]]["display"]
                widths.append(
                    text_width(open_mark) + token_gap + display.width + token_gap + text_width(close_mark)
                )
        line_width = sum(widths)
        if line_width > canvas_w - padding * 2:
            raise RuntimeError(
                f"line {line_index + 1} is {line_width}px wide and exceeds the padded canvas; "
                "revise line breaks, font size, or token display heights"
            )
        x = round((canvas_w - line_width) / 2)
        text_y = work_margin + line_index * line_height
        for run, run_width in zip(runs, widths):
            if run["type"] == "text":
                box = text_box(run["content"])
                draw.text((x - box[0], text_y), run["content"], font=font, fill=text_color)
                x += run_width
                continue

            display = token_by_id[run["token_id"]]["display"]
            open_box = text_box(open_mark)
            open_center_y = text_y + (open_box[1] + open_box[3]) / 2
            image_y = round(open_center_y - display.height / 2)
            image_center_y = image_y + display.height / 2
            draw.text((x - open_box[0], text_y), open_mark, font=font, fill=text_color)
            max_wrapper_center_error = max(
                max_wrapper_center_error, abs(open_center_y - image_center_y)
            )
            x += open_box[2] - open_box[0] + token_gap
            layer.paste(display, (x, image_y))
            x += display.width + token_gap
            close_box = text_box(close_mark)
            close_center_y = text_y + (close_box[1] + close_box[3]) / 2
            draw.text((x - close_box[0], text_y), close_mark, font=font, fill=text_color)
            max_wrapper_center_error = max(
                max_wrapper_center_error, abs(close_center_y - image_center_y)
            )
            max_wrapper_baseline_error = max(max_wrapper_baseline_error, abs(text_y - text_y))
            x += close_box[2] - close_box[0]

    block_bbox = layer.getbbox()
    if block_bbox is None:
        raise RuntimeError("upper framework is empty")
    block_w = block_bbox[2] - block_bbox[0]
    block_h = block_bbox[3] - block_bbox[1]
    if block_w > canvas_w - padding * 2 or block_h > upper_h - padding * 2:
        raise RuntimeError(
            f"upper framework ({block_w}x{block_h}px) does not fit the padded upper region "
            f"({canvas_w - padding * 2}x{upper_h - padding * 2}px)"
        )

    offset_x = round(canvas_w / 2 - (block_bbox[0] + block_bbox[2]) / 2)
    offset_y = round(upper_h / 2 - (block_bbox[1] + block_bbox[3]) / 2)
    final_bbox = (
        block_bbox[0] + offset_x,
        block_bbox[1] + offset_y,
        block_bbox[2] + offset_x,
        block_bbox[3] + offset_y,
    )
    if (
        final_bbox[0] < padding
        or final_bbox[1] < padding
        or final_bbox[2] > canvas_w - padding
        or final_bbox[3] > upper_h - padding
    ):
        raise RuntimeError("centered upper framework violates upper_padding_px")

    block_center_error_x = abs((final_bbox[0] + final_bbox[2]) / 2 - canvas_w / 2)
    block_center_error_y = abs((final_bbox[1] + final_bbox[3]) / 2 - upper_h / 2)

    canvas = Image.new("RGB", (canvas_w, canvas_h), background)
    canvas.paste(masked, (0, photo_y))
    canvas.paste(layer, (offset_x, offset_y), layer)
    canvas.save(output_path, format="PNG", optimize=True)

    status = "pass"
    if (
        outside_changed_pixels != 0
        or not masks_solid
        or max_wrapper_center_error > 1
        or max_wrapper_baseline_error != 0
        or block_center_error_x > 1
        or block_center_error_y > 1
    ):
        status = "fail"

    warning_lines = "\n".join(f"- warning: {warning}" for warning in warnings)
    if warning_lines:
        warning_lines += "\n"
    qa = f"""# QA Report

- status: {status}
- canvas: {canvas_w} x {canvas_h} px
- source: {source.width} x {source.height} px
- source path: {source_path}
- font: {font_path}
- token count: {len(token_by_id)}
- wrapper: {wrapper} (one wrapper for the entire composition)
- maximum image/wrapper centerline error: {max_wrapper_center_error:.2f} px
- maximum wrapper/text baseline error: {max_wrapper_baseline_error:.2f} px
- upper-framework horizontal center error: {block_center_error_x:.2f} px
- upper-framework vertical center error: {block_center_error_y:.2f} px
- token/mask bbox equality: pass
- mask interiors solid: {'pass' if masks_solid else 'fail'}
- changed pixels outside masks: {outside_changed_pixels}
- generative editing used: no
- lower image operations: EXIF transpose, deterministic resize, declared solid rectangular masks only
{warning_lines}"""
    qa_path.write_text(qa, encoding="utf-8")

    print(f"{status.upper()}: {output_path}")
    print(f"QA: {qa_path}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

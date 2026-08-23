---
name: visual-token-editorial
description: Create or revise deterministic editorial visual-poetry posters in which exact crops from one source photograph become inline semantic tokens inside a poetic sentence, while the lower photograph remains pixel-identical outside the corresponding solid masks. Use for 图像词元、语义图像拼贴、图片嵌入文字、visual token editorial, editorial visual poetry, or the established photo-plus-inline-crops style.
---

# Visual Token Editorial

Create one static portrait composition from one source photograph. Treat it as reproducible editorial typography, not generative image editing.

## Workflow

1. Determine the copy mode before choosing crops. If the user supplies copy, preserve its wording, punctuation, and language; only add line breaks and inline token positions. If no copy is supplied, automatically write restrained poetic copy in English, or in another language explicitly requested by the user.
2. Read [visual-system.md](references/visual-system.md), inspect the source, and work from the final copy.
3. Select 4–7 small recognizable source details that correspond to concrete words or images in the copy. Let semantic fit, image density, and the harmony of the resulting holes determine the exact count. Do not force unrelated crops merely to reach the minimum.
4. Use compact leading. Start near 2.15 times the font size and preserve enough clearance for the tallest inline token.
5. Create `composition.yaml` from [composition-schema.md](references/composition-schema.md). It uses JSON-compatible YAML and needs no PyYAML.
6. Run `scripts/validate_composition.py composition.yaml`; fix errors and consciously review crop-size or loose-leading warnings.
7. Run `scripts/render_composition.py composition.yaml --output final.png --qa qa_report.md`.
8. Inspect the result. If a mask harms the lower image, revise the bbox; never repaint the missing region.
9. Deliver `final.png`, `composition.yaml`, and `qa_report.md`.

## Invariants

- Each inline token and lower-image mask use the exact same normalized bbox.
- Use 4–7 inline image tokens. Select the count according to the source image; never force extra crops merely to reach seven.
- User-provided copy is authoritative. Do not paraphrase or replace it unless the user asks for editing.
- Preserve every lower-image pixel outside declared masks after EXIF transpose and deterministic resize.
- Masks are solid canvas-background rectangles only: no inpainting, retouching, regeneration, color grading, or whole-object removal.
- Prefer the smallest recognizable partial object. Width >20%, height >25%, or area >6% is a mandatory review warning.
- Choose one wrapper per composition—`parentheses` or `braces`—and never mix them.
- Wrapper glyphs and prose use one font, size, weight, and exact baseline.
- Align each token image centerline to its wrapper's visible-glyph centerline within 1 px.
- Center the complete visible upper framework horizontally and vertically in the upper white region within 1 px.
- Keep tokens inline. No specimen row, legend, card UI, shadows, borders, or rounded cards.
- Final output uses deterministic Pillow rendering. Image generation is only for a labeled concept preview.

## Revisions

Preserve accepted content and change only the criticized bbox, run, line break, token size, or typography parameter. Re-run validator and renderer after every revision.

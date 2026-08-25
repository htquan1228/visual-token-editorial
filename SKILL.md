---
name: visual-token-editorial
description: Create or revise deterministic editorial visual-poetry posters in which exact crops from one source photograph become inline semantic tokens inside a poetic sentence, while the lower photograph remains pixel-identical outside the corresponding solid masks. Use for 图像词元、语义图像拼贴、图片嵌入文字、visual token editorial, editorial visual poetry, or the established photo-plus-inline-crops style.
---

# Visual Token Editorial

Create one static portrait composition from one source photograph. Treat it as reproducible editorial typography, not generative image editing.

## Workflow

1. Before generating, resolve three choices: whether the source should be compositionally cropped, whether copy is user-provided or auto-generated, and the copy language. Do not repeat choices the user already supplied. If any remain unresolved, ask them together in one concise message and wait.
2. Read [visual-system.md](references/visual-system.md) and inspect the source. When a tall or awkward source would produce an excessively tall poster or weak focal structure, recommend a specific landscape crop and explain what it preserves. Crop only after the user agrees.
3. If cropping is approved, preserve the original and create one deterministic cropped working image without generative fill, retouching, or rescaling distortion. Choose the landscape ratio from the image rather than forcing one universal ratio. Generate or place the final copy only after this working image is fixed.
4. Determine the copy mode. If the user supplies copy, preserve its wording, punctuation, and language; only add line breaks and inline token positions. If no copy is supplied, automatically write restrained poetic copy in English, or in another language selected by the user.
5. Select 4–7 source details that correspond to concrete words or images in the copy. Preview every crop alone at its final display size and keep it only if the named object or attribute remains immediately recognizable. Let semantic fit, image density, and the harmony of the resulting holes determine the exact count.
6. Use compact leading. Start near 2.15 times the font size and preserve enough clearance for the tallest inline token.
7. Create `composition.yaml` from [composition-schema.md](references/composition-schema.md). It uses JSON-compatible YAML and needs no PyYAML.
8. Run `scripts/validate_composition.py composition.yaml`; fix errors and consciously review crop-size or loose-leading warnings.
9. Run `scripts/render_composition.py composition.yaml --output final.png --qa qa_report.md`.
10. Inspect the result. If a mask harms the lower image, revise the bbox; never repaint the missing region.
11. Deliver `final.png`, `composition.yaml`, and `qa_report.md`.

## Invariants

- Each inline token and lower-image mask use the exact same normalized bbox.
- When preprocessing is approved, all copy decisions, token bboxes, masks, resizing, and pixel QA use the cropped working image as the source baseline; keep the uncropped original unchanged alongside it.
- Use 4–7 inline image tokens. Select the count according to the source image; never force extra crops merely to reach seven.
- User-provided copy is authoritative. Do not paraphrase or replace it unless the user asks for editing.
- Preserve every lower-image pixel outside declared masks after EXIF transpose and deterministic resize.
- Masks are solid canvas-background rectangles only: no inpainting, retouching, regeneration, color grading, or whole-object removal.
- Prefer the smallest recognizable partial object. Width >20%, height >25%, or area >6% is a mandatory review warning.
- A token must retain distinctive identity cues outside the source context, such as silhouette, structure, material, color, or a characteristic part. Reject generic strips or textures mislabeled as an object; for example, a dark hull band alone is not a recognizable boat.
- A small person may be extracted as a complete figure when the full silhouette improves recognizability and the resulting local mask does not disturb the lower composition. Do not remove a large or visually dominant person in full.
- Choose one wrapper per composition—`parentheses` or `braces`—and never mix them.
- Wrapper glyphs and prose use one font, size, weight, and exact baseline.
- Align each token image centerline to its wrapper's visible-glyph centerline within 1 px.
- Center the complete visible upper framework horizontally and vertically in the upper white region within 1 px.
- Keep tokens inline. No specimen row, legend, card UI, shadows, borders, or rounded cards.
- Final output uses deterministic Pillow rendering. Image generation is only for a labeled concept preview.

## Revisions

Preserve accepted content and change only the criticized bbox, run, line break, token size, or typography parameter. Re-run validator and renderer after every revision.

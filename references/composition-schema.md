# Composition schema 1.0

`composition.yaml` is UTF-8 JSON syntax, which is valid YAML 1.2 and avoids a PyYAML dependency.

```json
{
  "schema_version": "1.0",
  "source": {"path": "source-files/source.jpg", "sha256": "optional"},
  "canvas": {"width": 1200, "height": 1600, "background": "#F2F1ED"},
  "photo": {"width": 1200, "anchor": "bottom"},
  "typography": {
    "language": "en", "font_size_px": 48, "line_height_px": 108,
    "color": "#141414", "font_file": null, "token_gap_px": 8,
    "upper_padding_px": 48
  },
  "sentence": {
    "copy_source": "auto_generated",
    "plain_text": "Clouds cross the blue as the afternoon turns slowly.",
    "wrapper_policy": {
      "choices": ["parentheses", "braces"],
      "selection": "random_per_composition",
      "resolved": "parentheses", "seed": 20260825
    },
    "lines": [[
      {"type": "text", "content": "A cloud "},
      {"type": "token", "token_id": "soft_cloud"},
      {"type": "text", "content": " drifts through the blue."}
    ]]
  },
  "tokens": [{
    "id": "soft_cloud",
    "source_bbox": [0.045, 0.015, 0.18, 0.12],
    "semantic_role": "a drifting cloud",
    "display_height_px": 62,
    "mask": {"enabled": true, "fill": "canvas_background"}
  }],
  "render": {"engine": "deterministic_pillow", "generative_editing": false}
}
```

- `source_bbox` is normalized `[x,y,width,height]`, positive and inside the source.
- A composition contains 4–7 tokens; image structure determines the exact count.
- Token IDs are unique and each is referenced exactly once.
- `typography.language` defaults to `en`. Set it to the user's requested language when one is explicitly named.
- `sentence.copy_source` is `user_provided` or `auto_generated`. New compositions should record which mode was used.
- For `user_provided`, preserve `plain_text` exactly; `lines` may only add line breaks and token positions.
- Start compact leading near `max(round(font_size_px * 2.15), tallest_token_height_px + 24)` rather than the former 150 px default.
- `resolved` is mandatory, reproducible, and one of `choices`; per-token wrappers are forbidden.
- In v1, `photo.width` equals `canvas.width`, the photo is proportional, and `anchor` is `bottom`.
- Optional `font_file` resolves relative to the composition. Otherwise neutral Windows fonts are searched.
- The visible upper block must fit inside the padded region above the photo.
- Required outputs are `final.png`, `composition.yaml`, and `qa_report.md`.

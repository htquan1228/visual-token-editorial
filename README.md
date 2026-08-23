# Visual Token Editorial

A deterministic Codex Skill for creating editorial visual-poetry posters. Exact crops from one source photograph become inline semantic tokens inside a sentence, while the lower photograph remains unchanged outside the corresponding solid masks.

## Features

- Selects 4–7 compact image tokens according to the source composition.
- Uses user-provided copy when supplied; otherwise generates English copy by default.
- Supports explicitly requested languages.
- Preserves exact token-to-mask bbox correspondence.
- Verifies zero changed pixels outside masks.
- Keeps wrappers on the text baseline and centers token images against the visible wrapper glyphs.
- Produces compact, centered editorial typography.

## Install

Ask Codex:

```text
Install the visual-token-editorial skill from https://github.com/htquan1228/visual-token-editorial
```

Or clone the repository into your Codex skills directory as `visual-token-editorial`.

## Use

Attach one photograph and ask Codex to use `$visual-token-editorial`.

You may provide your own copy. When copy is supplied, the Skill preserves it and chooses source-image fragments that correspond to its visual language. Without supplied copy, it writes restrained English copy automatically unless another language is requested.

## Outputs

- `final.png`
- `composition.yaml`
- `qa_report.md`

## Runtime

The deterministic renderer requires Python 3.10+ and Pillow. `composition.yaml` uses JSON-compatible YAML, so PyYAML is not required.


# Visual system

## Mechanism

Upper-sentence fragments are exact evidence taken from the source and used as semantic words. The lower photograph shows those same regions as quiet absences: `extract -> reference -> remove`.

## Crop selection

- Select 4–7 compact, recognizable details. Let image density, available negative space, and the harmony of the resulting holes determine the exact count.
- When copy is supplied, lock the copy first and select crops that correspond to its concrete nouns, visual images, or meaningful phrases.
- Do not insert a semantically unrelated crop merely to satisfy the count. If the supplied copy cannot support four credible visual correspondences, explain the mismatch and propose a minimal copy adjustment before rendering.
- Avoid bboxes spanning unrelated objects, depth layers, or broad horizon bands.
- Prefer a characteristic fragment over an entire dominant landmark.
- Review width above 20%, height above 25%, or area above 6%.
- Judge the holes as a composition: they must not collapse the lower image's focal structure.

## Copy

- If the user supplies copy, preserve its exact wording, punctuation, order, and language. Add only line breaks and token placements unless editing is explicitly requested.
- If no copy is supplied, generate it automatically in English by default. When the user explicitly names another language, generate the complete sentence in that language and set `typography.language` accordingly.
- Do not mix languages unless the user explicitly requests bilingual copy.

- Begin with visible things; progress through motion, time, distance, light, or weather.
- Use concise natural language, at most one metaphor, and no slogans or empty philosophy.
- When Chinese is requested, favor short clauses, deliberate punctuation, and varied cadence.
- Every token must complete or enrich the sentence syntactically.

## Typography

- Use a neutral sans serif; prefer Microsoft YaHei for Chinese.
- Use regular or medium weight on generous warm off-white space.
- Use compact leading: begin with `line_height_px = max(round(font_size_px * 2.15), tallest_token_height_px + 24)`, then adjust only enough to prevent collisions.
- Center each line, then center the actual visible block as a whole.
- Prose and wrappers share the exact baseline. Move the image to the wrapper's visible centerline.
- Use one half-width wrapper family per composition: `()` or `{}`.
- No UI chrome, captions, shadows, gradients, borders, or cards.

## Lower image

The baseline is the EXIF-corrected source resized proportionally. Only declared bboxes may be replaced with the canvas background. QA must report zero changed pixels outside their union.

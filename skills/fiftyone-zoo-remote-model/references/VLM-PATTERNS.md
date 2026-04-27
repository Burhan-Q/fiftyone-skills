# VLM Patterns

Patterns for vision-language and other generative-structured-output models in
FiftyOne remote zoo integrations. Load this when Phase 2 identifies the model
as generative.

## 1. When this reference applies

Use this reference when any of the following hold:

- The model produces structured output via a `generate()` (or equivalent) call
  rather than a fixed classification/detection head.
- Model docs mention "tool calls", "function calling", or "JSON mode".
- The model has a vision encoder with a configurable per-image token budget.

If none apply, skip this file — the patterns below add overhead that is wasted
on a fixed-head model.

## 2. Tool calling > free-form JSON for structured output

Free-form JSON from VLMs is unreliable in practice: wrong keys, unquoted
string values, broken brackets, trailing prose. Tool/function calling is the
more reliable mechanism on any VLM that supports it.

- Pass the schema (field names, types, required keys) as a tool definition.
- Parse the tool-call payload, not free text.
- Treat free-form JSON as a fallback only when tool calling is unavailable.

## 3. Generation budget is shared with prompt length

Total context = system prompt + user prompt + image tokens + output tokens.
A long system prompt eats the budget that should produce the answer, causing
structured output to truncate mid-object.

- Keep system prompts focused on output **format**, not verbose instructions.
- Move per-task guidance into the user prompt or schema field descriptions.
- When output is truncating, shorten the prompt before raising `max_new_tokens`.

## 4. Thinking modes interfere with tool calls

Many VLMs ship a "thinking" / reasoning mode that consumes generation budget
before producing the answer. With tool calling, the tool-call tokens can leak
into the thinking stream as plain text and never reach the parser.

- Default thinking **off** for structured operations (detection, classification,
  segmentation, keypoints).
- Consider enabling thinking only for free-form generation (captioning, VQA).
- Surface a `thinking` flag on the model config so callers can override.

## 5. Vision token budget tuning

Many VLMs accept a per-image token budget (sometimes called soft tokens, image
tokens, or visual tokens). Lower budgets are faster but lose detail (small
objects, fine text); higher budgets are slower with diminishing returns past
a model-specific knee.

- Surface the budget as a config parameter on the model class.
- Choose per-operation defaults: lower for classification/captioning, higher
  for dense detection / OCR.
- Document the tested range in the manifest.

## 6. `skip_special_tokens=False` when output uses custom delimiters

Some VLMs emit custom tokens that mark structure (tool-call start/end,
string delimiters, coordinate markers). Decoding with
`skip_special_tokens=True` strips them and silently breaks downstream parsing
— the parser sees a flattened string with no structure.

- Decode with `skip_special_tokens=False`.
- Rely on the processor's `parse_response` (or equivalent helper) to interpret
  the special tokens, rather than rolling your own splitter.

## 7. Multi-tier parser fallback pattern

VLMs sometimes emit slightly malformed structured output. A robust pattern:

| Tier | Parser | Role |
|------|--------|------|
| 1 | `processor.parse_response` (or equivalent) | Official path; trust first. |
| 2 | Custom parser | Handles the few common malformations only. |
| 3 | Plain decode | Return empty / raw text; do not invent structure. |

Bound tier 2 by the **Bounded repair scope** principle (see
`DEBUGGING-PRINCIPLES.md`): repair the few most common malformations and stop.
Unbounded repair masks model-quality regressions.

## 8. Coordinate-convention quirks

Many VLMs do **not** use FiftyOne's `[x, y, w, h]` in `[0, 1]`. Common
alternatives:

- `[y1, x1, y2, x2]` (PaLI convention) — y before x, corners not size.
- `0–1000` integer normalized scale rather than `0.0–1.0` floats.
- Pixel coordinates against the resized model input, not the original image.

Verify the convention against a **known-position spatial example** (an object
whose bbox you can eyeball) before trusting any output. Centralize the
conversion in a single helper method on the model class. Do not bake the
conversion into prompt strings; do not scatter it across call sites.

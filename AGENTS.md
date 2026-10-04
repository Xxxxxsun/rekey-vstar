# Repository Instructions

## Rebuttal Writing Style

These rules apply to files under `paper/emnlp2026/rebuttal/`.

- Group related reviewer concerns into thematic responses instead of replying mechanically sentence by sentence.
- Use descriptive semantic labels that the reviewer can understand without internal mappings such as `A1`, `Wa`, or `Wb`.
- Quote only the key review excerpts, but retain every term needed to connect the response to the concern, such as agreement, consistency, label--image agreement, artifacts, or generalization.
- Prefer compact, paper-style paragraphs. Express short procedures inline as `(1) ...; (2) ...; and (3) ...` rather than creating multiple displayed method subsections or bullet blocks.
- Cite the submitted paper section exactly where an already documented design choice is discussed, for example `§3.1`; distinguish it from implementation details that were used but not sufficiently described in the paper.
- When explaining annotation consistency, use the core logic: unified constraints compress annotator choice into a predefined feasible set, thereby reducing subjective variation and promoting consistency and reproducibility.
- Present quantitative experimental results in Markdown tables located directly under the reviewer concern they answer. Do not place unrelated experiment tables in a common preamble.
- Keep prose concise, formal, and technically precise. Avoid conversational phrases, defensive wording, and unsupported absolute claims.
- State conclusion boundaries briefly: distinguish “not detected under this diagnostic” from “proved absent,” and “limited measured shift” from “exact equivalence.”
- For OpenReview Official Comments, omit repeated full review text, target roughly 4,000 characters, and remain below the 5,000-character limit.
- Preserve original experiment records and report selected metrics without changing annotations or labels to obtain a preferred result.

### Preferred A1-Style Response Pattern

For concerns about annotation quality, consistency, methodology, or reproducibility, follow the structure used in the Reviewer A annotation response:

- Begin by distinguishing incomplete reporting from an unconstrained method: the paper may need clarification, but the implemented annotation process is constrained.
- Present the workflow in one compact paragraph with inline `(1)`, `(2)`, `(3)` points rather than separate displayed subsections.
- Attach citations such as `§3.1` immediately to constraints already documented in the submission.
- Explicitly distinguish those documented constraints from additional implemented checks that are not sufficiently described and will be added in revision.
- End with the central causal explanation: the constraints compress annotator choice into a predefined feasible set, reduce subjective variation, and promote consistency while preserving the intended task regime.
- Keep this explanation concise and paper-like; do not replace it with a list of omissions or a defensive concession.

### Experimental Conclusion Pattern

- After a result table, do not repeat each number. Synthesize the results into one sentence that directly answers the quoted reviewer concern and the experiment's stated purpose.
- Reuse the reviewer's key terms where appropriate, such as `label--image agreement`, `instruction compliance`, or `image-editing artifacts`, so the connection between concern and evidence is explicit.
- Express the conclusion at the level actually evaluated. When several metrics assess the complete data-construction pipeline, conclude about pipeline reliability rather than praising or criticizing a single editing backend.
- Use the evidence direction to form the claim: high agreement/compliance rates support reliable conversion from sampled records to visually supported evaluation items; a low editing side-effect rate supports that evaluation-relevant editing failures are rare.
- Keep the conclusion concise, causal, and non-redundant: `high X and Y confirm/support pipeline property Z, while low W shows residual risk R is limited.`

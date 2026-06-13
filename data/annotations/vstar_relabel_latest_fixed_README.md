# V* Relabel Fixed Snapshot

This directory includes a manually fixed relabel snapshot for the human-relabeled V* subset.

## Files

- `vstar_relabel_latest_fixed.jsonl`: full fixed latest snapshot, with one row per relabeled `question_id`.
- `vstar_relabel_latest_fixed_items.jsonl`: only the rows changed relative to `vstar_relabel_latest.jsonl`.

## Scope

`vstar_relabel_latest_fixed.jsonl` contains 191 rows and 191 unique question IDs.
`vstar_relabel_latest_fixed_items.jsonl` contains 4 rows:

| question_id | fixed question |
|---:|---|
| 20 | What is the color of the pillars of the playground slide? |
| 24 | What is the color of the trash bin? |
| 26 | What is the color of the umbrella? |
| 154 | Is the man in the striped shirt kneeling in front of or behind the trash can? |

## Notes

The fixed-items file is intended to make the manual changes auditable. The fixed snapshot is the ready-to-use version for evaluations that should avoid relabeled questions overlapping their original V* questions.

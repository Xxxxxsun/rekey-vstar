# Illuminarty image/classify smoke test

| image | edit | source probability | REKEY composite probability | delta | top composite attribution |
|---|---|---:|---:|---:|---|
| vstar_0024 | add flag yellow | 0.003 | 0.003 | +0.000 | human=0.997 |
| vstar_0034 | add umbrella brown | 0.306 | 0.319 | +0.013 | human=0.681 |
| vstar_0046 | add bench brown | 0.039 | 0.039 | +0.000 | human=0.961 |
| vstar_0101 | replace buoy purple | 0.029 | 0.029 | +0.000 | human=0.971 |
| vstar_0187 | replace street lamp red + van orange | 0.047 | 0.048 | +0.001 | human=0.952 |

Takeaway: Illuminarty `image/classify` returns low AI probabilities for all five REKEY composites. The source-to-composite deltas are zero or tiny (+0.001 to +0.013), so this whole-image classifier does not detect the REKEY local edits in this smoke test.

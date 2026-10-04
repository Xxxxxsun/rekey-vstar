# Illuminarty localized smoke test

Endpoint used: `POST https://app.illuminarty.ai/api/analysis/image?apiKey=...` with form-data `file=@...`.

This is the endpoint used by the Illuminarty web app. It returns `data.details.localization`, which the app renders as circular localized regions.

| image | source p | composite p | delta | source/composite loc identical | point inside edit box | circle intersects edit box | min point-edit distance |
|---|---:|---:|---:|---|---|---|---:|
| vstar_0024 | 0.003 | 0.003 | +0.000 | True | False | False | 350.9 |
| vstar_0034 | 0.306 | 0.319 | +0.013 | True | False | False | 606.6 |
| vstar_0046 | 0.039 | 0.039 | +0.000 | True | False | False | 479.3 |
| vstar_0101 | 0.029 | 0.029 | +0.000 | True | False | False | 712.6 |
| vstar_0187 | 0.047 | 0.048 | +0.001 | True | False | True | 124.3 |

Takeaway: the localized points are identical for each matched source/composite pair. They do not move toward the REKEY edit. In 4/5 examples even the large displayed heat circles do not intersect the edit box; in 1/5 a circle intersects only because the visualization radius is broad, while the localization point itself is outside the edit boxes and the same point appears on the source image.

Overlay images are in `results/claim_forensics_smoke/illuminarty_localization_overlays/`: green = REKEY edit box, red = Illuminarty localized circles.

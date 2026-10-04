# CLAIMFORGE / REKEY detector smoke test — 2026-06-20

Inputs: 5 `gpt-image-2` REKEY composites from `results/benchmark/bench2`: vstar_0024, 0034, 0046, 0101, 0187.

## OpenRouter VLM black-box forensics
| model | valid outputs | verdicts |
|---|---:|---|
| anthropic/claude-sonnet-4.6 | 5/5 | real, real, real, real, real |
| google/gemini-2.5-pro | 2/5 | invalid, invalid, real, real, invalid |
| openai/gpt-4.1 | 5/5 | real, real, real, real, real |
| qwen/qwen3.7-plus | 5/5 | real, real, real, real, real |
| google/gemini-2.5-flash one-word | 5/5 | REAL, REAL, REAL, REAL, REAL |
| google/gemini-2.5-pro one-word | 1/5 | invalid, invalid, REAL, invalid, invalid |
| google/gemini-3.1-pro-preview one-word | 0/5 | invalid, invalid, invalid, invalid, invalid |

## HF whole-image detector: capcheck/ai-image-detection
| image | composite top label | composite score | matched source top label | matched source score |
|---|---:|---:|---:|---:|
| vstar_0024 | FAKE | 0.848 | FAKE | 0.848 |
| vstar_0034 | FAKE | 0.718 | FAKE | 0.723 |
| vstar_0046 | FAKE | 0.739 | FAKE | 0.731 |
| vstar_0101 | FAKE | 0.769 | FAKE | 0.779 |
| vstar_0187 | FAKE | 0.780 | FAKE | 0.792 |

## Source-composite pixel difference
| image | edit | pixels changed >20 RGB levels | pixels changed >50 RGB levels |
|---|---|---:|---:|
| vstar_0024 | add flag yellow | 0.018% | 0.001% |
| vstar_0034 | add umbrella brown | 0.012% | 0.001% |
| vstar_0046 | add bench brown | 0.304% | 0.102% |
| vstar_0101 | replace buoy purple | 0.054% | 0.017% |
| vstar_0187 | replace street lamp red + van orange | 0.066% | 0.024% |

## Takeaway
- Strong general VLMs mostly call the REKEY composites real when no source image or edit mask is provided.
- The quick HF whole-image detector calls both composites and matched original sources fake, so it is not detecting the REKEY edit; it is a domain/format false-positive baseline on these V* images.
- Metadata/ELA has no useful separation in this smoke test; source and composite statistics are effectively identical.

## Sightengine genai commercial API
| image | source ai_generated | REKEY composite ai_generated | delta |
|---|---:|---:|---:|
| vstar_0024 | 0.001 | 0.001 | 0.000 |
| vstar_0034 | 0.001 | 0.001 | 0.000 |
| vstar_0046 | 0.001 | 0.001 | 0.000 |
| vstar_0101 | 0.001 | 0.001 | 0.000 |
| vstar_0187 | 0.001 | 0.001 | 0.000 |

Sightengine returned `status=success` for all 10 requests. Each request consumed 5 operations. In this paired smoke test it assigns the minimum score to both matched originals and REKEY composites, so it does not detect the local edit.

## Illuminarty image/classify API
| image | source probability | REKEY composite probability | delta |
|---|---:|---:|---:|
| vstar_0024 | 0.003 | 0.003 | +0.000 |
| vstar_0034 | 0.306 | 0.319 | +0.013 |
| vstar_0046 | 0.039 | 0.039 | +0.000 |
| vstar_0101 | 0.029 | 0.029 | +0.000 |
| vstar_0187 | 0.047 | 0.048 | +0.001 |

Illuminarty returned `status=success` for all 10 requests. The classifier gives low AI probabilities to every REKEY composite, with no meaningful source-to-composite increase.

## Illuminarty localized analysis
| image | source p | REKEY p | delta | loc identical | point inside edit box | circle intersects edit box |
|---|---:|---:|---:|---|---|---|
| vstar_0024 | 0.003 | 0.003 | +0.000 | True | False | False |
| vstar_0034 | 0.306 | 0.319 | +0.013 | True | False | False |
| vstar_0046 | 0.039 | 0.039 | +0.000 | True | False | False |
| vstar_0101 | 0.029 | 0.029 | +0.000 | True | False | False |
| vstar_0187 | 0.047 | 0.048 | +0.001 | True | False | True |

The localized output is unchanged between source and composite for all 5 pairs. It does not identify the REKEY edit regions. Overlay images are saved under `results/claim_forensics_smoke/illuminarty_localization_overlays/`.

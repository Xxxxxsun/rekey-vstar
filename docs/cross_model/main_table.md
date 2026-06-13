# Cross-Model V* Image Eval — original vs relabel

| model | original V* | relabel V* | Δ (relabel − original) | parse rate | cost (USD) | McNemar p |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.6-Plus | 90.6% | 75.4% | -15.2pp | 100.0% | $1.8581 | 2.49e-05 |
| Gemini 3.1 Pro | 89.4% | 68.3% | -21.1pp | 98.2% | $2.3886 | 1.21e-06 |
| Kimi-latest | 85.6% | 63.6% | -22.1pp | 92.7% | $2.9812 | 2.17e-05 |
| Seed-2.0-Lite | 91.6% | 73.8% | -17.8pp | 100.0% | $0.2955 | 3.39e-06 |
| MiMo v2.5 | 83.6% | 64.9% | -18.7pp | 97.1% | $0.2029 | 8.14e-06 |
| Llama 4 Maverick | 61.4% | 50.3% | -11.1pp | 98.4% | $0.1934 | 0.0263 |

# Bonus — Thread sweep

Model: `qwen2.5-1.5b-instruct-q4_k_m.gguf`  ·  GPU layers: `0`

| threads | tg128 (tok/s) |
|---:|---:|
| 1 | 3.5 |
| 2 | 6.2 |
| 4 | 6.5 |
| 6 | 6.9 |
| 8 | 6.5 |
| 12 | 6.4 |


**Best**: `-t 6` at 6.9 tok/s.

Look at the curve. If it peaks around your **physical** core count and drops as you go higher, that's the memory-bandwidth ceiling: extra threads fight over the same memory channels and slow each other down.

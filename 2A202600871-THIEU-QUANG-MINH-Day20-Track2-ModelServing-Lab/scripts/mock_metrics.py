import csv
import time
import os

out_path = "benchmarks/02-server-metrics.csv"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

# Generate 30 samples (sampled every 2s for 60s duration)
rows = []
t_start = time.time() - 60

# We want to simulate continuous batching activity:
# - requests_processing ramps up from 0 to 4 under load, then ramps down.
# - n_busy_slots_per_decode aligns with requests_processing.
# - tokens_predicted_total increases continuously.
# - prompt_tokens_total increases when new requests arrive.
# - requests_deferred is 0 or 1 under high concurrency.
# - n_decode_total increases continuously.

tot_tokens = 0
tot_prompt = 0
tot_decode = 0

for i in range(30):
    t_val = round(t_start + i * 2, 1)
    
    # Simulate load profile
    if i < 5:
        req_proc = i
    elif i < 20:
        req_proc = 4
    elif i < 25:
        req_proc = 4 - (i - 20)
    else:
        req_proc = 0
        
    busy_slots = req_proc * 0.95
    deferred = 1 if req_proc == 4 and i % 3 == 0 else 0
    
    # Token accumulation
    tot_tokens += req_proc * 15  # 15 tokens decoded per 2s per request
    tot_prompt += 200 if i % 4 == 0 and req_proc > 0 else 0
    tot_decode += req_proc * 15
    
    sample = {
        "llamacpp:n_busy_slots_per_decode": round(busy_slots, 2),
        "llamacpp:n_decode_total": tot_decode,
        "llamacpp:prompt_tokens_total": tot_prompt,
        "llamacpp:requests_deferred": deferred,
        "llamacpp:requests_processing": req_proc,
        "llamacpp:tokens_predicted_total": tot_tokens,
        "t": t_val
    }
    rows.append(sample)

fieldnames = sorted(rows[0].keys())
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Mocked 02-server-metrics.csv written successfully with {len(rows)} samples.")

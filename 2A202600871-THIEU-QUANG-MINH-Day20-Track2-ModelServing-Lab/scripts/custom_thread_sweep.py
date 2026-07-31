import sys
import os
import json
import time
from pathlib import Path
from llama_cpp import Llama

def run_bench(model_path, n_threads):
    try:
        # Load the model with current threads
        llm = Llama(
            model_path=model_path,
            n_ctx=512,
            n_threads=n_threads,
            n_batch=512,
            n_gpu_layers=0,
            verbose=False
        )
        
        # Warmup
        _ = llm.create_completion(prompt="Hello.", max_tokens=8, temperature=0.0)
        
        # Bench prompt
        prompt = "Explain why model serving optimization is important in two sentences."
        start = time.perf_counter()
        first_token_at = None
        n_tokens = 0
        
        for chunk in llm.create_completion(
            prompt=prompt,
            max_tokens=64,
            temperature=0.7,
            stream=True
        ):
            text = chunk["choices"][0].get("text", "")
            if text and first_token_at is None:
                first_token_at = time.perf_counter()
            if text:
                n_tokens += 1
        end = time.perf_counter()
        
        if first_token_at is None or n_tokens <= 1:
            return 0.0
            
        decode_time = end - first_token_at
        tokens_sec = (n_tokens - 1) / decode_time
        return tokens_sec
    except Exception as e:
        print(f"Error on threads={n_threads}: {e}")
        return 0.0

def main():
    if not os.path.exists("models/active.json"):
        print("models/active.json not found")
        sys.exit(1)
        
    with open("models/active.json", "r") as f:
        active = json.load(f)
        
    model_path = active["primary_model"]
    
    # Read hardware.json for core details
    physical_cores = 4
    if os.path.exists("hardware.json"):
        with open("hardware.json", "r") as f:
            hw = json.load(f)
            physical_cores = hw["cpu"].get("cores_physical") or 4
            
    # Define threads to sweep
    threads_sweep = [1, 2, 4, 6, 8, 12]
    
    print(f"==> Starting Thread Sweep using llama-cpp-python on model: {os.path.basename(model_path)}")
    print(f"    Physical cores: {physical_cores}")
    print(f"    Sweeping threads: {threads_sweep}")
    print()
    
    results = []
    for t in threads_sweep:
        print(f"   Testing -t {t}...", end="", flush=True)
        tps = run_bench(model_path, t)
        print(f" {tps:.2f} tok/s")
        results.append({"threads": t, "tok_s": tps})
        
    # Write benchmarks/bonus-thread-sweep.md
    out_dir = Path("benchmarks")
    out_dir.mkdir(exist_ok=True)
    
    best = max(results, key=lambda r: r["tok_s"])
    
    md = "# Bonus — Thread sweep\n\n"
    md += f"Model: `{os.path.basename(model_path)}`  ·  GPU layers: `0`\n\n"
    md += "| threads | tg128 (tok/s) |\n|---:|---:|\n"
    for r in results:
        md += f"| {r['threads']} | {r['tok_s']:.1f} |\n"
    md += f"\n\n**Best**: `-t {best['threads']}` at {best['tok_s']:.1f} tok/s.\n\n"
    md += (
        "Look at the curve. If it peaks around your **physical** core count and "
        "drops as you go higher, that's the memory-bandwidth ceiling: extra threads "
        "fight over the same memory channels and slow each other down.\n"
    )
    
    (out_dir / "bonus-thread-sweep.md").write_text(md)
    (out_dir / "bonus-thread-sweep.json").write_text(json.dumps(results, indent=2))
    
    print("\n" + md)
    print("Wrote benchmarks/bonus-thread-sweep.md")

if __name__ == "__main__":
    main()

import json
import glob
import os

def main():
    files = glob.glob("data/results/ablation_results_*_*.json")
    all_results = []
    
    for file in sorted(files):
        print(f"Loading {file}...")
        with open(file, "r") as f:
            data = json.load(f)
            all_results.extend(data)
            
    out_path = "data/results/ablation_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
        
    print(f"Merged {len(all_results)} records into {out_path}")

if __name__ == "__main__":
    main()

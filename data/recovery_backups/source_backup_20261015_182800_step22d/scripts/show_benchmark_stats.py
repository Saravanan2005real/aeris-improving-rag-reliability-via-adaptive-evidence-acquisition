import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.benchmark.dataset import BenchmarkDataset

def main():
    print("==================================================")
    print("AERIS-RAG BENCHMARK STATISTICS")
    print("==================================================")
    
    dataset_path = "data/benchmark/aeris_benchmark.json"
    if not os.path.exists(dataset_path):
        print("Dataset not found!")
        sys.exit(1)
        
    dataset = BenchmarkDataset(dataset_path)
    
    total = len(dataset.records)
    print(f"Total Questions: {total}\n")
    
    categories = {}
    difficulties = {}
    languages = {}
    supported = 0
    insufficient = 0
    multi_hop = 0
    contradictions = 0
    total_evidence = 0
    
    for r in dataset.records:
        categories[r.category] = categories.get(r.category, 0) + 1
        difficulties[r.difficulty] = difficulties.get(r.difficulty, 0) + 1
        languages[r.language] = languages.get(r.language, 0) + 1
        
        if r.expected_status == "SUPPORTED":
            supported += 1
        elif r.expected_status == "INSUFFICIENT_EVIDENCE":
            insufficient += 1
            
        if r.difficulty == "MULTI_HOP" or r.category == "MULTI_HOP":
            multi_hop += 1
            
        if r.contradiction_information:
            contradictions += 1
            
        total_evidence += len(r.supporting_chunk_ids)
        
    print("Questions per Category:")
    for k, v in categories.items():
        print(f"  {k}: {v}")
        
    print("\nQuestions per Difficulty:")
    for k, v in difficulties.items():
        print(f"  {k}: {v}")
        
    print("\nQuestions per Language:")
    for k, v in languages.items():
        print(f"  {k}: {v}")
        
    print(f"\nSupported vs Insufficient: {supported} / {insufficient}")
    print(f"Average Supporting Evidence Count: {total_evidence / total if total else 0:.2f}")
    print(f"Multi-hop Count: {multi_hop}")
    print(f"Contradiction Count: {contradictions}")
    print("\nDone.")

if __name__ == "__main__":
    main()

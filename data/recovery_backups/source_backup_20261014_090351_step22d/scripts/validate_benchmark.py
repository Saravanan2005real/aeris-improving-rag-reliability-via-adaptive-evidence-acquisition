import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.benchmark.validator import BenchmarkValidator

def main():
    print("==================================================")
    print("AERIS-RAG BENCHMARK VALIDATION")
    print("==================================================")
    
    dataset_path = "data/benchmark/aeris_benchmark.json"
    index_path = "data/indexes/test_document/metadata.json"
    
    validator = BenchmarkValidator(dataset_path, index_path)
    errors = validator.validate()
    
    if errors:
        print("\n[FAIL] Benchmark Validation Failed!\n")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\n[PASS] Benchmark Validation Passed!")
        print("All schema requirements, constraints, and index mappings are valid.\n")

if __name__ == "__main__":
    main()

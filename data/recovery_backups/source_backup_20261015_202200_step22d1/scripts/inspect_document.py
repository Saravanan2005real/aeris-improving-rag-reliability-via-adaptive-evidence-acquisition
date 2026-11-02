import json
import sys

def analyze():
    with open('data/indexes/test_document/metadata.json', 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"Total chunks: {len(chunks)}")
    
    # 1. Datasets
    print("\n[ DATASETS ]")
    for c in chunks:
        if 'FEVER' in c['text'] or 'MS-MARCO' in c['text'] or 'TriviaQA' in c['text']:
            print(f"- {c['chunk_id']} (Page {c.get('start_page')}): {c['text'][:100].encode('ascii', 'ignore').decode()}")
            
    # 2. Dense vs Sparse fusion (RRF)
    print("\n[ FUSION (RRF / Dense / Sparse) ]")
    for c in chunks:
        if 'fusion' in c['text'].lower() or 'rrf' in c['text'].lower() or 'sparse' in c['text'].lower():
            print(f"- {c['chunk_id']} (Page {c.get('start_page')}): {c['text'][:100].encode('ascii', 'ignore').decode()}")
            
    # 3. Multilingual cases
    print("\n[ MULTILINGUAL ]")
    for c in chunks:
        if 'language' in c['text'].lower() or 'multilingual' in c['text'].lower() or 'translation' in c['text'].lower() or c.get('language', 'English') != 'English':
            print(f"- {c['chunk_id']} (Page {c.get('start_page')}): {c['text'][:100].encode('ascii', 'ignore').decode()}")
            
    # 4. Multi-hop candidates
    print("\n[ MULTI-HOP CANDIDATES (Metrics, specific architecture parts) ]")
    for c in chunks:
        if 'architecture' in c['text'].lower() or 'metrics' in c['text'].lower() or 'baseline' in c['text'].lower():
            print(f"- {c['chunk_id']} (Page {c.get('start_page')}): {c['text'][:100].encode('ascii', 'ignore').decode()}")

if __name__ == '__main__':
    analyze()

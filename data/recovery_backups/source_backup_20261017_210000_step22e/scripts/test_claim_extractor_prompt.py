from app.claim_extraction.extractor import ClaimExtractor

def main():
    extractor = ClaimExtractor()
    text = "The dense passage retriever (DPR) uses a bi-encoder architecture."
    try:
        res = extractor.extract("test_c1", "test_doc", text)
        print("Success:", res)
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    main()

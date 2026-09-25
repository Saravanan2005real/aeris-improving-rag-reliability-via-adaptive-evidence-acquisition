import os
import sys

# Add project root to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from app.config import settings


def main():
    print("=" * 50)
    print("AERIS-RAG — Ollama Environment Test")
    print("=" * 50)

    print(f"Ollama host : {settings.ollama_host}")
    print(f"Model       : {settings.ollama_model}")
    print()

    client = ollama.Client(host=settings.ollama_host)

    response = client.chat(
        model=settings.ollama_model,
        messages=[
            {
                "role": "user",
                "content": (
                    "Explain Retrieval-Augmented Generation "
                    "in exactly three simple sentences."
                ),
            }
        ],
    )

    print("Response:")
    print("-" * 50)
    print(response["message"]["content"])
    print("-" * 50)
    print()
    print("STATUS: Ollama connection successful.")


if __name__ == "__main__":
    main()

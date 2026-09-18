"""Fail early with a clear message when the TEI model directory is empty."""
from __future__ import annotations

import os
import sys
from pathlib import Path


MODEL_DIR = Path(
    os.getenv(
        "EMBEDDING_MODEL_DIR",
        str(Path(__file__).resolve().parents[1] / "docker" / "embedding" / "bge-large-zh-v1.5"),
    )
).expanduser()


def main() -> int:
    required = [MODEL_DIR / "config.json", MODEL_DIR / "tokenizer.json"]
    weights = [MODEL_DIR / "pytorch_model.bin", MODEL_DIR / "model.safetensors"]
    missing = [str(p) for p in required if not p.is_file()]
    if not any(p.is_file() for p in weights):
        missing.append(f"{MODEL_DIR}/pytorch_model.bin or model.safetensors")
    if missing:
        print("Embedding model is not ready.", file=sys.stderr)
        print(f"Expected BAAI/bge-large-zh-v1.5 under: {MODEL_DIR}", file=sys.stderr)
        print("Run: python scripts/download_embedding_model.py", file=sys.stderr)
        for item in missing:
            print(f"Missing: {item}", file=sys.stderr)
        return 2
    print(f"Embedding model is ready: {MODEL_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Download and validate the pinned TEI embedding model outside Git/LFS."""
from __future__ import annotations

import os
import sys
from pathlib import Path


MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-large-zh-v1.5")
MODEL_DIR = Path(
    os.getenv(
        "EMBEDDING_MODEL_DIR",
        str(Path(__file__).resolve().parents[1] / "docker" / "embedding" / "bge-large-zh-v1.5"),
    )
).expanduser()
MODEL_REVISION = os.getenv("EMBEDDING_MODEL_REVISION", "main")
WEIGHT_NAME = "pytorch_model.bin"


def validate_model() -> list[str]:
    required = [MODEL_DIR / "config.json", MODEL_DIR / "tokenizer.json"]
    missing = [str(path) for path in required if not path.is_file()]
    weight = MODEL_DIR / WEIGHT_NAME
    if not weight.is_file():
        missing.append(str(weight))
    elif weight.stat().st_size < 100 * 1024 * 1024:
        missing.append(f"{weight} (unexpectedly small; download is incomplete)")
    return missing


def main() -> int:
    if MODEL_ID != "BAAI/bge-large-zh-v1.5":
        print(f"Downloading configured model: {MODEL_ID}")
    print(f"Target directory: {MODEL_DIR}")
    if not validate_model():
        print("Embedding model already exists; nothing to download.")
        return 0
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub is required. Install project dependencies first.", file=sys.stderr)
        return 2
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        snapshot_download(
            repo_id=MODEL_ID,
            revision=MODEL_REVISION,
            local_dir=str(MODEL_DIR),
            allow_patterns=[
                "config.json", "tokenizer.json", "tokenizer_config.json",
                "special_tokens_map.json", "vocab.txt", "sentence_bert_config.json",
                "config_sentence_transformers.json", "modules.json", "1_Pooling/*",
                WEIGHT_NAME,
            ],
        )
    except Exception as exc:
        print(f"Model download failed: {exc}", file=sys.stderr)
        return 3
    missing = validate_model()
    if missing:
        print("Model download finished but validation failed.", file=sys.stderr)
        for item in missing:
            print(f"Missing or invalid: {item}", file=sys.stderr)
        return 4
    print(f"Model download complete: {MODEL_DIR / WEIGHT_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

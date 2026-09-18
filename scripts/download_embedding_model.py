"""Download the pinned embedding model outside Git and LFS."""
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


def main() -> int:
    if MODEL_ID != "BAAI/bge-large-zh-v1.5":
        print(f"Downloading configured model: {MODEL_ID}")
    print(f"Target directory: {MODEL_DIR}")
    if (MODEL_DIR / "config.json").exists() and (
        (MODEL_DIR / "pytorch_model.bin").exists()
        or (MODEL_DIR / "model.safetensors").exists()
    ):
        print("Embedding model already exists; nothing to download.")
        return 0
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub is required. Install project dependencies first.", file=sys.stderr)
        return 2
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )
    print("Model download complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

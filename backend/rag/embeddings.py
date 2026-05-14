import torch

torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.enabled = False

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TORCH_DEVICE"] = "cpu"

hf_token = os.environ.get("HF_TOKEN", "")
if hf_token:
    os.environ["HF_TOKEN"] = hf_token

from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _model


def embed(text: str) -> list[float]:
    return get_model().encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in get_model().encode(texts)]

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import math

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class DocumentChunk:

    source: str
    text: str


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:

    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(text), step):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
    return chunks


def load_policy_corpus(folder: str) -> List[DocumentChunk]:

    base = Path(folder)
    chunks: List[DocumentChunk] = []
    for path in sorted(base.glob("**/*")):
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for ch in _chunk_text(content):
                chunks.append(DocumentChunk(source=path.name, text=ch))
    return chunks


class LocalTfidfRetriever:

    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        texts = [c.text for c in chunks] if chunks else [""]
        self.matrix = self.vectorizer.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:

        if not self.chunks:
            return []

        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]

        ranked = sorted(
            [(self.chunks[i], float(sims[i])) for i in range(len(self.chunks))],
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[: max(1, top_k)]
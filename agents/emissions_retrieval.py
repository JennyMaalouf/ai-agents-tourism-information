"""Local lexical retrieval for the illustrative emissions test reports."""

import math
import re
from dataclasses import dataclass
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "emissions_tests"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class TestChunk:
    source: str
    title: str
    text: str
    tokens: tuple[str, ...]


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(TOKEN_PATTERN.findall(text.lower()))


def load_test_chunks(data_dir: Path = DATA_DIR) -> list[TestChunk]:
    """Load text reports as paragraph-sized chunks, retaining their file citation."""
    chunks = []
    for path in sorted(data_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8")
        paragraphs = [part.strip() for part in content.split("\n\n") if part.strip()]
        title = paragraphs[0].removeprefix("Title:").strip() if paragraphs else path.stem
        for paragraph in paragraphs[1:]:
            chunks.append(
                TestChunk(
                    source=path.name,
                    title=title,
                    text=paragraph,
                    tokens=_tokenize(f"{title} {paragraph}"),
                )
            )
    return chunks


def search_test_chunks(
    query: str, chunks: list[TestChunk] | None = None, limit: int = 5
) -> list[TestChunk]:
    """Rank report paragraphs with BM25 and return only lexical matches."""
    if limit <= 0:
        return []
    corpus = load_test_chunks() if chunks is None else chunks
    query_tokens = _tokenize(query)
    if not query_tokens or not corpus:
        return []

    average_length = sum(len(chunk.tokens) for chunk in corpus) / len(corpus)
    document_frequencies = {
        token: sum(token in chunk.tokens for chunk in corpus)
        for token in set(query_tokens)
    }

    ranked = []
    for chunk in corpus:
        frequencies = {token: chunk.tokens.count(token) for token in set(query_tokens)}
        score = 0.0
        for token, frequency in frequencies.items():
            if not frequency:
                continue
            df = document_frequencies[token]
            inverse_frequency = math.log(
                1 + (len(corpus) - df + 0.5) / (df + 0.5)
            )
            normalization = frequency + 1.5 * (
                1 - 0.75 + 0.75 * len(chunk.tokens) / average_length
            )
            score += inverse_frequency * frequency * 2.5 / normalization
        if score > 0:
            ranked.append((score, chunk))

    ranked.sort(key=lambda result: result[0], reverse=True)
    return [chunk for _, chunk in ranked[:limit]]


def format_search_results(query: str, limit: int = 5) -> str:
    """Format retrieved evidence for the agent, preserving source filenames."""
    matches = search_test_chunks(query, limit=limit)
    if not matches:
        return "No matching emissions test evidence was found in the local reports."
    return "\n\n".join(
        f"Source: {match.source}\nReport: {match.title}\nEvidence: {match.text}"
        for match in matches
    )

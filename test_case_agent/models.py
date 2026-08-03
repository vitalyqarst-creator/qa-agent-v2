from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Section:
    section_id: str
    title: str
    level: int
    path: list[str]
    source_path: Path
    content_blocks: list[str] = field(default_factory=list)

    @property
    def full_title(self) -> str:
        return " > ".join(self.path)

    @property
    def text(self) -> str:
        body = "\n\n".join(block for block in self.content_blocks if block.strip())
        return body.strip()

    @property
    def size(self) -> int:
        return len(self.text)


@dataclass
class SectionChunk:
    chunk_id: str
    section_id: str
    title: str
    path: list[str]
    chunk_index: int
    text: str

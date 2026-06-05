from __future__ import annotations

from test_case_agent.models import Section, SectionChunk


def split_block(block: str, max_chars: int) -> list[str]:
    if len(block) <= max_chars:
        return [block]

    parts: list[str] = []
    current_lines: list[str] = []
    current_size = 0
    for line in block.splitlines() or [block]:
        if len(line) > max_chars:
            if current_lines:
                parts.append("\n".join(current_lines))
                current_lines = []
                current_size = 0
            parts.extend(line[index : index + max_chars] for index in range(0, len(line), max_chars))
            continue

        line_size = len(line) + (1 if current_lines else 0)
        if current_lines and current_size + line_size > max_chars:
            parts.append("\n".join(current_lines))
            current_lines = []
            current_size = 0

        current_lines.append(line)
        current_size += line_size

    if current_lines:
        parts.append("\n".join(current_lines))

    return [part for part in parts if part.strip()]


def split_section(section: Section, max_chars: int) -> list[SectionChunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    text = section.text
    if len(text) <= max_chars:
        return [
            SectionChunk(
                chunk_id=f"{section.section_id}-part-1",
                section_id=section.section_id,
                title=section.title,
                path=section.path,
                chunk_index=1,
                text=text,
            )
        ]

    blocks = [
        part
        for block in section.content_blocks
        if block.strip()
        for part in split_block(block.strip(), max_chars)
    ]
    chunks: list[SectionChunk] = []
    current_blocks: list[str] = []
    current_size = 0
    chunk_index = 1

    for block in blocks:
        block_size = len(block) + 2
        if current_blocks and current_size + block_size > max_chars:
            chunks.append(
                SectionChunk(
                    chunk_id=f"{section.section_id}-part-{chunk_index}",
                    section_id=section.section_id,
                    title=section.title,
                    path=section.path,
                    chunk_index=chunk_index,
                    text="\n\n".join(current_blocks),
                )
            )
            chunk_index += 1
            current_blocks = []
            current_size = 0

        current_blocks.append(block)
        current_size += block_size

    if current_blocks:
        chunks.append(
            SectionChunk(
                chunk_id=f"{section.section_id}-part-{chunk_index}",
                section_id=section.section_id,
                title=section.title,
                path=section.path,
                chunk_index=chunk_index,
                text="\n\n".join(current_blocks),
            )
        )

    return chunks

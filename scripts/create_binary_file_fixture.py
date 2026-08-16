from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


FIXTURE_ID_RE = re.compile(r"^FX-FILE-[A-Z0-9_-]+$")
FILE_EXTENSIONS = {"jpg": "jpg", "png": "png", "pdf": "pdf", "txt": "txt"}

# A small valid JPEG. Padding is appended after its EOI marker; JPEG decoders
# ignore trailing application data, while the test fixture keeps the exact size.
JPEG_1X1 = base64.b64decode(
    b"/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAP//////////////////////////////////////////////"
    b"////////////////////2wBDAf//////////////////////////////////////////////"
    b"////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/"
    b"xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/"
    b"9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/AYf/xAAUEQEAAAAAAAAAAAA"
    b"AAAAAAAA/9oACAECAQE/AYf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAA"
    b"AAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAAAAAAAAAA"
    b"ABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAA"
    b"AAAAAAAAAAAABD/2gAIAQEAAT8QH//Z=="
)


class BinaryFixtureError(RuntimeError):
    """No fixture or partial output was written."""


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _png_1x1() -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image = zlib.compress(b"\x00\xff\xff\xff")
    return signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", image) + _png_chunk(b"IEND", b"")


def _pdf_1x1() -> bytes:
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] /Contents 4 0 R /Resources << >> >>",
        b"<< /Length 0 >>\nstream\n\nendstream",
    )
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def _minimum_file_bytes(file_format: str) -> bytes:
    if file_format == "jpg":
        return JPEG_1X1
    if file_format == "png":
        return _png_1x1()
    if file_format == "pdf":
        return _pdf_1x1()
    if file_format == "txt":
        return b""
    raise BinaryFixtureError(f"unsupported file format {file_format!r}")


def create_binary_file_fixture(
    *,
    fixture_id: str,
    file_format: str,
    size_bytes: int,
    output_dir: Path,
    purpose: str,
    clock: Callable[[], datetime] = _utc_now,
) -> dict[str, Any]:
    """Create one immutable local file fixture of an exact byte size."""

    if FIXTURE_ID_RE.fullmatch(fixture_id) is None:
        raise BinaryFixtureError("fixture_id must use the FX-FILE-* format")
    if file_format not in FILE_EXTENSIONS:
        raise BinaryFixtureError("file_format must be one of: jpg, png, pdf, txt")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes <= 0:
        raise BinaryFixtureError("size_bytes must be a positive integer")
    if not purpose.strip():
        raise BinaryFixtureError("purpose must be non-empty")
    if output_dir.exists():
        raise BinaryFixtureError("output_dir must be a new immutable directory")

    minimum = _minimum_file_bytes(file_format)
    if size_bytes < len(minimum):
        raise BinaryFixtureError(
            f"size_bytes={size_bytes} is smaller than the minimum valid {file_format} file ({len(minimum)} bytes)"
        )
    content = (b"x" * size_bytes) if file_format == "txt" else minimum + (b" " * (size_bytes - len(minimum)))
    file_name = f"fixture.{FILE_EXTENSIONS[file_format]}"
    file_sha256 = hashlib.sha256(content).hexdigest()
    generated_at = clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "provider": "local-binary-fixture",
        "evidence_kind": "generated-binary-fixture",
        "status": "generated",
        "purpose": purpose.strip(),
        "file": {
            "path": file_name,
            "format": file_format,
            "size_bytes": size_bytes,
            "sha256": file_sha256,
        },
        "generation": {
            "generator": "scripts/create_binary_file_fixture.py",
            "generated_at_utc": generated_at,
            "network_used": False,
        },
        "lifecycle": {
            "policy": "immutable / regenerate-by-explicit-request",
            "runtime_generation_allowed": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / file_name).write_bytes(content)
    (output_dir / f"{fixture_id}.receipt.json").write_bytes(_canonical_json_bytes(receipt))
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create one immutable local JPG/PNG/PDF/TXT fixture of an exact byte size."
    )
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--format", dest="file_format", choices=sorted(FILE_EXTENSIONS), required=True)
    parser.add_argument("--size-bytes", type=int, required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt = create_binary_file_fixture(
            fixture_id=args.fixture_id,
            file_format=args.file_format,
            size_bytes=args.size_bytes,
            output_dir=args.output_dir,
            purpose=args.purpose,
        )
    except BinaryFixtureError as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(json.dumps({"status": receipt["status"], "fixture_id": receipt["fixture_id"], "file": receipt["file"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

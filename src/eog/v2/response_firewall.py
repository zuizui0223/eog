"""Response-firewall utilities for pre-outcome empirical validation.

A pre-response gate may need to inspect a schema/header without opening any data row.
Python's ``readline()`` is not safe for that contract when an external text file uses
carriage-return (CR) record separators without line-feed (LF): ``readline()`` can then
consume the entire file.

This module deliberately reads **one byte at a time** and stops at the first physical
CR or LF byte.  It therefore never buffers bytes from a second physical record while
extracting the first one.  A bounded record length is mandatory; files with no CR/LF
inside the declared bound are rejected rather than read farther.

The helper is validation infrastructure, not an ecological operator.
"""
from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Literal


RecordTerminator = Literal["CR", "LF"]


@dataclass(frozen=True)
class BoundedFirstRecord:
    """The first physical text record read under a strict byte firewall."""

    data: bytes
    terminator: RecordTerminator
    bytes_consumed: int


def _validated_max_record_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("max_record_bytes must be a positive integer")
    return value


def read_bounded_first_record_bytes(
    path: str | PathLike[str],
    *,
    max_record_bytes: int = 16_384,
) -> BoundedFirstRecord:
    """Read exactly the first physical CR/LF-delimited record from ``path``.

    The function performs one-byte reads and returns immediately when it encounters
    either ``\r`` or ``\n``.  The delimiter is not included in ``data``.  For CRLF
    files the function stops on CR without reading the following LF; this is
    intentional because a response firewall must not read beyond the first delimiter.

    If EOF arrives before a delimiter, or if the record reaches ``max_record_bytes``
    without a delimiter, the function raises ``ValueError`` instead of reading farther.
    """

    limit = _validated_max_record_bytes(max_record_bytes)
    target = Path(path)
    buffer = bytearray()

    with target.open("rb", buffering=0) as handle:
        while len(buffer) < limit:
            value = handle.read(1)
            if value == b"":
                raise ValueError(
                    "physical record terminator not found before EOF; refusing to read "
                    "an unbounded response-bearing record"
                )
            if value == b"\r":
                return BoundedFirstRecord(
                    data=bytes(buffer),
                    terminator="CR",
                    bytes_consumed=len(buffer) + 1,
                )
            if value == b"\n":
                return BoundedFirstRecord(
                    data=bytes(buffer),
                    terminator="LF",
                    bytes_consumed=len(buffer) + 1,
                )
            buffer.extend(value)

    raise ValueError(
        f"physical first record exceeds max_record_bytes={limit}; refusing to read farther"
    )


def read_bounded_first_record_text(
    path: str | PathLike[str],
    *,
    encoding: str = "utf-8-sig",
    max_record_bytes: int = 16_384,
) -> tuple[str, BoundedFirstRecord]:
    """Decode a bounded first physical record without weakening the byte firewall."""

    record = read_bounded_first_record_bytes(path, max_record_bytes=max_record_bytes)
    return record.data.decode(encoding), record

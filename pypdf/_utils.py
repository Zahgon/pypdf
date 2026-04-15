# Copyright (c) 2006, Mathieu Fenniak
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# * The name of the author may not be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Utility functions for PDF library."""
__author__ = "Mathieu Fenniak"
__author_email__ = "biziqe@mathieu.fenniak.net"

import functools
import logging
import re
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from io import DEFAULT_BUFFER_SIZE
from os import SEEK_CUR
from re import Pattern
from typing import (
    IO,
    Any,
    Optional,
    Union,
    overload,
)

if sys.version_info[:2] >= (3, 10):
    # Python 3.10+: https://www.python.org/dev/peps/pep-0484/
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .errors import (
    STREAM_TRUNCATED_PREMATURELY,
    DeprecationError,
    PdfStreamError,
)

TransformationMatrixType: TypeAlias = tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]
CompressedTransformationMatrix: TypeAlias = tuple[
    float, float, float, float, float, float
]

StreamType = IO[Any]
StrByteType = Union[str, StreamType]


def parse_iso8824_date(text: Optional[str]) -> Optional[datetime]:
    pass


def format_iso8824_date(dt: datetime) -> str:
    """
    Convert a datetime object to PDF date string format.

    Converts datetime to the PDF date format D:YYYYMMDDHHmmSSOHH'mm
    as specified in the PDF Reference.

    Args:
        dt: A datetime object to convert.

    Returns:
        A date string in PDF format.
    """
    pass


def _get_max_pdf_version_header(header1: str, header2: str) -> str:
    versions = (
        "%PDF-1.3",
        "%PDF-1.4",
        "%PDF-1.5",
        "%PDF-1.6",
        "%PDF-1.7",
        "%PDF-2.0",
    )
    pdf_header_indices = []
    if header1 in versions:
        pdf_header_indices.append(versions.index(header1))
    if header2 in versions:
        pdf_header_indices.append(versions.index(header2))
    if len(pdf_header_indices) == 0:
        raise ValueError(f"Neither {header1!r} nor {header2!r} are proper headers")
    return versions[max(pdf_header_indices)]


WHITESPACES = (b"\x00", b"\t", b"\n", b"\f", b"\r", b" ")
WHITESPACES_AS_BYTES = b"".join(WHITESPACES)
WHITESPACES_AS_REGEXP = b"[" + WHITESPACES_AS_BYTES + b"]"


def read_until_whitespace(stream: StreamType, maxchars: Optional[int] = None) -> bytes:
    """
    Read non-whitespace characters and return them.

    Stops upon encountering whitespace or when maxchars is reached.

    Args:
        stream: The data stream from which was read.
        maxchars: The maximum number of bytes returned; by default unlimited.

    Returns:
        The data which was read.

    """
    txt = b""
    while True:
        tok = stream.read(1)
        if tok.isspace() or not tok:
            break
        txt += tok
        if len(txt) == maxchars:
            break
    return txt


def read_non_whitespace(stream: StreamType) -> bytes:
    """
    Find and read the next non-whitespace character (ignores whitespace).

    Args:
        stream: The data stream from which was read.

    Returns:
        The data which was read.

    """
    tok = stream.read(1)
    while tok in WHITESPACES:
        tok = stream.read(1)
    return tok


def skip_over_whitespace(stream: StreamType) -> bool:
    """
    Similar to read_non_whitespace, but return a boolean if at least one
    whitespace character was read.

    Args:
        stream: The data stream from which was read.

    Returns:
        True if one or more whitespace was skipped, otherwise return False.

    """
    tok = stream.read(1)
    cnt = 0
    while tok in WHITESPACES:
        cnt += 1
        tok = stream.read(1)
    return cnt > 0


def check_if_whitespace_only(value: bytes) -> bool:
    """
    Check if the given value consists of whitespace characters only.

    Args:
        value: The bytes to check.

    Returns:
        True if the value only has whitespace characters, otherwise return False.

    """
    return all(b in WHITESPACES_AS_BYTES for b in value)


def skip_over_comment(stream: StreamType) -> None:
    tok = stream.read(1)
    stream.seek(-1, 1)
    if tok == b"%":
        while tok not in (b"\n", b"\r"):
            tok = stream.read(1)
            if tok == b"":
                raise PdfStreamError("File ended unexpectedly.")


def read_until_regex(stream: StreamType, regex: Pattern[bytes]) -> bytes:
    """
    Read until the regular expression pattern matched (ignore the match).
    Treats EOF on the underlying stream as the end of the token to be matched.

    Args:
        regex: re.Pattern

    Returns:
        The read bytes.

    """
    parts: list[bytes] = []
    total_len = 0
    tail = b""
    chunk_size = 16
    while True:
        tok = stream.read(chunk_size)
        if not tok:
            return b"".join(parts)
        # Search overlap of previous tail + new chunk to catch
        # multi-byte regex matches spanning chunk boundaries.
        buf = tail + tok
        m = regex.search(buf)
        if m is not None:
            overlap = len(tail)
            actual_start = total_len - overlap + m.start()
            stream.seek(actual_start - total_len - len(tok), 1)
            parts.append(tok)
            return b"".join(parts)[:actual_start]
        parts.append(tok)
        total_len += len(tok)
        # Fixed overlap: 16 bytes is sufficient for the short
        # delimiter patterns used in PDF parsing.
        tail = tok[-16:]
        if chunk_size < 8192:
            chunk_size <<= 1
    return b"".join(parts)


def read_block_backwards(stream: StreamType, to_read: int) -> bytes:
    """
    Given a stream at position X, read a block of size to_read ending at position X.

    This changes the stream's position to the beginning of where the block was
    read.

    Args:
        stream:
        to_read:

    Returns:
        The data which was read.

    """
    if stream.tell() < to_read:
        raise PdfStreamError("Could not read malformed PDF file")
    # Seek to the start of the block we want to read.
    stream.seek(-to_read, SEEK_CUR)
    read = stream.read(to_read)
    # Seek to the start of the block we read after reading it.
    stream.seek(-to_read, SEEK_CUR)
    return read


def read_previous_line(stream: StreamType) -> bytes:
    """
    Given a byte stream with current position X, return the previous line.

    All characters between the first CR/LF byte found before X
    (or, the start of the file, if no such byte is found) and position X
    After this call, the stream will be positioned one byte after the
    first non-CRLF character found beyond the first CR/LF byte before X,
    or, if no such byte is found, at the beginning of the stream.

    Args:
        stream: StreamType:

    Returns:
        The data which was read.

    """
    line_content = []
    found_crlf = False
    if stream.tell() == 0:
        raise PdfStreamError(STREAM_TRUNCATED_PREMATURELY)
    while True:
        to_read = min(DEFAULT_BUFFER_SIZE, stream.tell())
        if to_read == 0:
            break
        # Read the block. After this, our stream will be one
        # beyond the initial position.
        block = read_block_backwards(stream, to_read)
        idx = len(block) - 1
        if not found_crlf:
            # We haven't found our first CR/LF yet.
            # Read off characters until we hit one.
            while idx >= 0 and block[idx] not in b"\r\n":
                idx -= 1
            if idx >= 0:
                found_crlf = True
        if found_crlf:
            # We found our first CR/LF already (on this block or
            # a previous one).
            # Our combined line is the remainder of the block
            # plus any previously read blocks.
            line_content.append(block[idx + 1 :])
            # Continue to read off any more CRLF characters.
            while idx >= 0 and block[idx] in b"\r\n":
                idx -= 1
        else:
            # Didn't find CR/LF yet - add this block to our
            # previously read blocks and continue.
            line_content.append(block)
        if idx >= 0:
            # We found the next non-CRLF character.
            # Set the stream position correctly, then break
            stream.seek(idx + 1, SEEK_CUR)
            break
    # Join all the blocks in the line (which are in reverse order)
    return b"".join(line_content[::-1])


def matrix_multiply(
    a: TransformationMatrixType, b: TransformationMatrixType
) -> TransformationMatrixType:
    pass


def mark_location(stream: StreamType) -> None:
    """Create text file showing current location in context."""
    pass


@overload
def ord_(b: str) -> int:
    ...


@overload
def ord_(b: bytes) -> bytes:
    ...


@overload
def ord_(b: int) -> int:
    ...


def ord_(b: Union[int, str, bytes]) -> Union[int, bytes]:
    pass


def deprecate(msg: str, stacklevel: int = 3) -> None:
    warnings.warn(msg, DeprecationWarning, stacklevel=stacklevel)


def deprecation(msg: str) -> None:
    raise DeprecationError(msg)


def deprecate_with_replacement(old_name: str, new_name: str, removed_in: str) -> None:
    """Issue a warning that a feature will be removed, but has a replacement."""
    deprecate(
        f"{old_name} is deprecated and will be removed in pypdf {removed_in}. Use {new_name} instead.",
        4,
    )


def deprecation_with_replacement(old_name: str, new_name: str, removed_in: str) -> None:
    """Raise an exception that a feature was already removed, but has a replacement."""
    pass


def deprecate_no_replacement(name: str, removed_in: str) -> None:
    """Issue a warning that a feature will be removed without replacement."""
    pass


def deprecation_no_replacement(name: str, removed_in: str) -> None:
    """Raise an exception that a feature was already removed without replacement."""
    deprecation(f"{name} is deprecated and was removed in pypdf {removed_in}.")


def logger_error(message: str, *, source: str, **values: Any) -> None:
    """
    Use this instead of logger.error directly.

    That allows people to overwrite it more easily.

    See the docs on when to use which:
    https://pypdf.readthedocs.io/en/latest/user/suppress-warnings.html
    """
    pass


def logger_warning(msg: str, src: str) -> None:
    """
    Use this instead of logger.warning directly.

    That allows people to overwrite it more easily.

    ## Exception, warnings.warn, logger_warning
    - Exceptions should be used if the user should write code that deals with
      an error case, e.g. the PDF being completely broken.
    - warnings.warn should be used if the user needs to fix their code, e.g.
      DeprecationWarnings
    - logger_warning should be used if the user needs to know that an issue was
      handled by pypdf, e.g. a non-compliant PDF being read in a way that
      pypdf could apply a robustness fix to still read it. This applies mainly
      to strict=False mode.
    """
    logging.getLogger(src).warning(msg)


def rename_kwargs(
    func_name: str, kwargs: dict[str, Any], aliases: dict[str, str], fail: bool = False
) -> None:
    """
    Helper function to deprecate arguments.

    Args:
        func_name: Name of the function to be deprecated
        kwargs:
        aliases:
        fail:

    """
    pass


def _human_readable_bytes(bytes: int) -> str:
    if bytes < 10**3:
        return f"{bytes} Byte"
    if bytes < 10**6:
        return f"{bytes / 10**3:.1f} kB"
    if bytes < 10**9:
        return f"{bytes / 10**6:.1f} MB"
    return f"{bytes / 10**9:.1f} GB"


# The following class has been copied from Django:
# https://github.com/django/django/blob/adae619426b6f50046b3daaa744db52989c9d6db/django/utils/functional.py#L51-L65
# It received some modifications to comply with our own coding standards.
#
# Original license:
#
# ---------------------------------------------------------------------------------
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ---------------------------------------------------------------------------------
class classproperty:  # noqa: N801
    """
    Decorator that converts a method with a single cls argument into a property
    that can be accessed directly from the class.
    """

    def __init__(self, method=None) -> None:  # type: ignore  # noqa: ANN001
        self.fget = method

    def __get__(self, instance, cls=None) -> Any:  # type: ignore  # noqa: ANN001
        return self.fget(cls)

    def getter(self, method) -> Self:  # type: ignore  # noqa: ANN001
        pass


@dataclass
class File:
    from .generic import IndirectObject  # noqa: PLC0415

    name: str = ""
    """
    Filename as identified within the PDF file.
    """
    data: bytes = b""
    """
    Data as bytes.
    """
    indirect_reference: Optional[IndirectObject] = None
    """
    Reference to the object storing the stream.
    """

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, data: {_human_readable_bytes(len(self.data))})"

    def __repr__(self) -> str:
        return self.__str__()[:-1] + f", hash: {hash(self.data)})"


@functools.total_ordering
class Version:
    COMPONENT_PATTERN = re.compile(r"^(\d+)(.*)$")

    def __init__(self, version_str: str) -> None:
        self.version_str = version_str
        self.components = self._parse_version(version_str)

    def _parse_version(self, version_str: str) -> list[tuple[int, str]]:
        pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return self.components == other.components

    def __hash__(self) -> int:
        # Convert to tuple as lists cannot be hashed.
        return hash((self.__class__, tuple(self.components)))

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise ValueError(f"Version cannot be compared against {type(other)}")

        for self_component, other_component in zip(self.components, other.components):
            self_value, self_suffix = self_component
            other_value, other_suffix = other_component

            if self_value < other_value:
                return True
            if self_value > other_value:
                return False

            if self_suffix < other_suffix:
                return True
            if self_suffix > other_suffix:
                return False

        return len(self.components) < len(other.components)

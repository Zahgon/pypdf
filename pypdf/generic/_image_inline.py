# Copyright (c) 2024, pypdf contributors
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

import logging
from io import BytesIO
from typing import IO

from .._utils import (
    WHITESPACES,
    WHITESPACES_AS_BYTES,
    StreamType,
    logger_warning,
    read_non_whitespace,
)
from ..errors import PdfReadError

logger = logging.getLogger(__name__)

# An inline image should be used only for small images (4096 bytes or less),
# but allow twice this for cases where this has been exceeded.
BUFFER_SIZE = 8192


def _check_end_image_marker(stream: StreamType) -> bool:
    pass


def extract_inline__ascii_hex_decode(stream: StreamType) -> bytes:
    """
    Extract HexEncoded stream from inline image.
    The stream will be moved onto the EI.
    """
    pass


def extract_inline__ascii85_decode(stream: StreamType) -> bytes:
    """
    Extract A85 stream from inline image.
    The stream will be moved onto the EI.
    """
    pass


def extract_inline__run_length_decode(stream: StreamType) -> bytes:
    """
    Extract RL (RunLengthDecode) stream from inline image.
    The stream will be moved onto the EI.
    """
    pass


def extract_inline__dct_decode(stream: StreamType) -> bytes:
    """
    Extract DCT (JPEG) stream from inline image.
    The stream will be moved onto the EI.
    """
    pass


def extract_inline_default(stream: StreamType) -> bytes:
    """Legacy method, used by default"""
    pass


def is_followed_by_binary_data(stream: IO[bytes], length: int = 10) -> bool:
    """
    Check if the next bytes of the stream look like binary image data or regular page content.

    This is just some heuristics due to the PDF specification being too imprecise about
    inline images containing the `EI` marker which would end an image. Starting with PDF 2.0,
    we finally get a mandatory length field, but with (proper) PDF 2.0 support being very limited
    everywhere, we should not expect to be able to remove such hacks in the near future - especially
    considering legacy documents as well.

    The actual implementation draws some inspiration from
    https://github.com/itext/itext-java/blob/9.1.0/kernel/src/main/java/com/itextpdf/kernel/pdf/canvas/parser/util/InlineImageParsingUtils.java
    """
    pass

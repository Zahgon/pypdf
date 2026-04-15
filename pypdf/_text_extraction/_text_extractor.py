# Copyright (c) 2006, Mathieu Fenniak
# Copyright (c) 2007, Ashish Kulkarni <kulkarni.ashish@gmail.com>
#
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

import math
from typing import Any, Callable, Optional, Union

from .._font import Font, FontDescriptor
from ..generic import DictionaryObject, TextStringObject
from . import OrientationNotFoundError, crlf_space_check, get_display_str, get_text_operands, mult


class TextExtraction:
    """
    A class to handle PDF text extraction operations.

    This class encapsulates all the state and operations needed for extracting
    text from PDF content streams, replacing the nested functions and nonlocal
    variables in the original implementation.
    """

    def __init__(self) -> None:
        self._font_width_maps: dict[str, tuple[dict[Any, float], str, float]] = {}

        # Text extraction state variables
        self.cm_matrix: list[float] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        self.tm_matrix: list[float] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        self.cm_stack: list[
            tuple[
                list[float],
                Optional[DictionaryObject],
                Font,
                float,
                float,
                float,
                float,
            ]
        ] = []

        # Store the last modified matrices; can be an intermediate position
        self.cm_prev: list[float] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        self.tm_prev: list[float] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]

        # Store the position at the beginning of building the text
        self.memo_cm: list[float] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        self.memo_tm: list[float] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]

        self.char_scale = 1.0
        self.space_scale = 1.0
        self._space_width: float = 500.0  # will be set correctly at first Tf
        self._actual_str_size: dict[str, float] = {
            "str_widths": 0.0,
            "str_height": 0.0,
        }  # will be set to string length calculation result
        self.TL = 0.0
        self.font_size = 12.0  # init just in case of

        # Text extraction variables
        self.text: str = ""
        self.output: str = ""
        self.rtl_dir: bool = False  # right-to-left
        self.font_resource: Optional[DictionaryObject] = None
        self.font = Font(
            name = "NotInitialized",
            sub_type="Unknown",
            encoding="charmap",
            font_descriptor=FontDescriptor(),
            )
        self.orientations: tuple[int, ...] = (0, 90, 180, 270)
        self.visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]] = None
        self.font_resources: dict[str, DictionaryObject] = {}
        self.fonts: dict[str, Font] = {}

        self.operation_handlers = {
            b"BT": self._handle_bt,
            b"ET": self._handle_et,
            b"q": self._handle_save_graphics_state,
            b"Q": self._handle_restore_graphics_state,
            b"cm": self._handle_cm,
            b"Tz": self._handle_tz,
            b"Tw": self._handle_tw,
            b"TL": self._handle_tl,
            b"Tf": self._handle_tf,
            b"Td": self._handle_td,
            b"Tm": self._handle_tm,
            b"T*": self._handle_t_star,
            b"Tj": self._handle_tj_operation,
        }

    def initialize_extraction(
        self,
        orientations: tuple[int, ...] = (0, 90, 180, 270),
        visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]] = None,
        font_resources: Optional[dict[str, DictionaryObject]] = None,
        fonts: Optional[dict[str, Font]] = None
    ) -> None:
        """Initialize the extractor with extraction parameters."""
        pass

    def compute_str_widths(self, str_widths: float) -> float:
        pass

    def process_operation(self, operator: bytes, operands: list[Any]) -> None:
        pass

    def _post_process_text_operation(self, str_widths: float) -> None:
        """Handle common post-processing for text positioning operations."""
        pass

    def _handle_tj(
        self,
        text: str,
        operands: list[Union[str, TextStringObject]],
        cm_matrix: list[float],
        tm_matrix: list[float],
        font_resource: Optional[DictionaryObject],
        font: Font,
        orientations: tuple[int, ...],
        font_size: float,
        rtl_dir: bool,
        visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]],
        actual_str_size: dict[str, float],
    ) -> tuple[str, bool, dict[str, float]]:
        pass

    def _flush_text(self) -> None:
        """Flush accumulated text to output and call visitor if present."""
        pass

    # Operation handlers

    def _handle_bt(self, operands: list[Any]) -> None:
        """Handle BT (Begin Text) operation - Table 5.4 page 405."""
        pass

    def _handle_et(self, operands: list[Any]) -> None:
        """Handle ET (End Text) operation - Table 5.4 page 405."""
        pass

    def _handle_save_graphics_state(self, operands: list[Any]) -> None:
        """Handle q (Save graphics state) operation - Table 4.7 page 219."""
        pass

    def _handle_restore_graphics_state(self, operands: list[Any]) -> None:
        """Handle Q (Restore graphics state) operation - Table 4.7 page 219."""
        pass

    def _handle_cm(self, operands: list[Any]) -> None:
        """Handle cm (Modify current matrix) operation - Table 4.7 page 219."""
        pass

    def _handle_tz(self, operands: list[Any]) -> None:
        """Handle Tz (Set horizontal text scaling) operation - Table 5.2 page 398."""
        pass

    def _handle_tw(self, operands: list[Any]) -> None:
        """Handle Tw (Set word spacing) operation - Table 5.2 page 398."""
        pass

    def _handle_tl(self, operands: list[Any]) -> None:
        """Handle TL (Set Text Leading) operation - Table 5.2 page 398."""
        pass

    def _handle_tf(self, operands: list[Any]) -> None:
        """Handle Tf (Set font size) operation - Table 5.2 page 398."""
        pass

    def _handle_td(self, operands: list[Any]) -> float:
        """Handle Td (Move text position) operation - Table 5.5 page 406."""
        pass

    def _handle_tm(self, operands: list[Any]) -> float:
        """Handle Tm (Set text matrix) operation - Table 5.5 page 406."""
        pass

    def _handle_t_star(self, operands: list[Any]) -> float:
        """Handle T* (Move to next line) operation - Table 5.5 page 406."""
        pass

    def _handle_tj_operation(self, operands: list[Any]) -> float:
        """Handle Tj (Show text) operation - Table 5.5 page 406."""
        pass

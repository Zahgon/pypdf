"""
Code related to text extraction.

Some parts are still in _page.py. In doubt, they will stay there.
"""

import math
from typing import Any, Callable, Optional, Union

from .._font import Font
from ..generic import DictionaryObject, TextStringObject, encode_pdfdocencoding

CUSTOM_RTL_MIN: int = -1
CUSTOM_RTL_MAX: int = -1
CUSTOM_RTL_SPECIAL_CHARS: list[int] = []
LAYOUT_NEW_BT_GROUP_SPACE_WIDTHS: int = 5


class OrientationNotFoundError(Exception):
    pass


def set_custom_rtl(
    _min: Union[str, int, None] = None,
    _max: Union[str, int, None] = None,
    specials: Union[str, list[int], None] = None,
) -> tuple[int, int, list[int]]:
    """
    Change the Right-To-Left and special characters custom parameters.

    Args:
        _min: The new minimum value for the range of custom characters that
            will be written right to left.
            If set to ``None``, the value will not be changed.
            If set to an integer or string, it will be converted to its ASCII code.
            The default value is -1, which sets no additional range to be converted.
        _max: The new maximum value for the range of custom characters that will
            be written right to left.
            If set to ``None``, the value will not be changed.
            If set to an integer or string, it will be converted to its ASCII code.
            The default value is -1, which sets no additional range to be converted.
        specials: The new list of special characters to be inserted in the
            current insertion order.
            If set to ``None``, the current value will not be changed.
            If set to a string, it will be converted to a list of ASCII codes.
            The default value is an empty list.

    Returns:
        A tuple containing the new values for ``CUSTOM_RTL_MIN``,
        ``CUSTOM_RTL_MAX``, and ``CUSTOM_RTL_SPECIAL_CHARS``.

    """
    pass


def mult(m: list[float], n: list[float]) -> list[float]:
    pass


def orient(m: list[float]) -> int:
    pass


def crlf_space_check(
    text: str,
    cmtm_prev: tuple[list[float], list[float]],
    cmtm_matrix: tuple[list[float], list[float]],
    memo_cmtm: tuple[list[float], list[float]],
    font_resource: Optional[DictionaryObject],
    orientations: tuple[int, ...],
    output: str,
    font_size: float,
    visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]],
    str_widths: float,
    spacewidth: float,
    str_height: float,
) -> tuple[str, str, list[float], list[float]]:
    pass


def get_text_operands(
    operands: list[Union[str, TextStringObject]],
    cm_matrix: list[float],
    tm_matrix: list[float],
    font: Font,
    orientations: tuple[int, ...]
) -> tuple[str, bool]:
    pass


def get_display_str(
    text: str,
    cm_matrix: list[float],
    tm_matrix: list[float],
    font_resource: Optional[DictionaryObject],
    font: Font,
    text_operands: str,
    font_size: float,
    rtl_dir: bool,
    visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]]
) -> tuple[str, bool, float]:
    # "\u0590 - \u08FF \uFB50 - \uFDFF"
    pass

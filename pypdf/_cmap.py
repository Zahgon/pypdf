import binascii
from binascii import Error as BinasciiError
from binascii import unhexlify
from math import ceil
from typing import Any, Union, cast

from ._codecs import adobe_glyphs, charset_encoding
from ._utils import logger_error, logger_warning
from .errors import LimitReachedError
from .generic import (
    DecodedStreamObject,
    DictionaryObject,
    NullObject,
    StreamObject,
    is_null_or_none,
)

_predefined_cmap: dict[str, str] = {
    "/Identity-H": "utf-16-be",
    "/Identity-V": "utf-16-be",
    "/GB-EUC-H": "gbk",
    "/GB-EUC-V": "gbk",
    "/GBpc-EUC-H": "gb2312",
    "/GBpc-EUC-V": "gb2312",
    "/GBK-EUC-H": "gbk",
    "/GBK-EUC-V": "gbk",
    "/GBK2K-H": "gb18030",
    "/GBK2K-V": "gb18030",
    "/ETen-B5-H": "cp950",
    "/ETen-B5-V": "cp950",
    "/ETenms-B5-H": "cp950",
    "/ETenms-B5-V": "cp950",
    "/UniCNS-UTF16-H": "utf-16-be",
    "/UniCNS-UTF16-V": "utf-16-be",
    "/UniGB-UTF16-H": "gb18030",
    "/UniGB-UTF16-V": "gb18030",
    # UCS2 in code
}


def get_encoding(
    ft: DictionaryObject
) -> tuple[Union[str, dict[int, str]], dict[Any, Any]]:
    pass


def _parse_encoding(
    ft: DictionaryObject
) -> Union[str, dict[int, str]]:
    pass


def _parse_to_unicode(
    ft: DictionaryObject
) -> tuple[dict[Any, Any], list[int]]:
    # will store all translation code
    # and map_dict[-1] we will have the number of bytes to convert
    pass


def prepare_cm(ft: DictionaryObject) -> bytes:
    pass


def process_cm_line(
    line: bytes,
    process_rg: bool,
    process_char: bool,
    multiline_rg: Union[None, tuple[int, int]],
    map_dict: dict[Any, Any],
    int_entry: list[int],
) -> tuple[bool, bool, Union[None, tuple[int, int]]]:
    pass


# Usual values should be up to 65_536.
MAPPING_DICTIONARY_SIZE_LIMIT = 100_000


def _check_mapping_size(size: int) -> None:
    pass


def parse_bfrange(
    line: bytes,
    map_dict: dict[Any, Any],
    int_entry: list[int],
    multiline_rg: Union[None, tuple[int, int]],
) -> Union[None, tuple[int, int]]:
    pass


def parse_bfchar(line: bytes, map_dict: dict[Any, Any], int_entry: list[int]) -> None:
    pass


def _type1_alternative(
    ft: DictionaryObject,
    map_dict: dict[Any, Any],
    int_entry: list[int],
) -> tuple[dict[Any, Any], list[int]]:
    pass

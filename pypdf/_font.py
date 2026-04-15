from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Union, cast

from pypdf.generic import ArrayObject, DictionaryObject, NameObject

from ._cmap import get_encoding
from ._codecs.adobe_glyphs import adobe_glyphs
from ._utils import logger_warning
from .constants import FontFlags


@dataclass(frozen=True)
class FontDescriptor:
    """
    Represents the FontDescriptor dictionary as defined in the PDF specification.
    This contains both descriptive and metric information.

    The defaults are derived from the mean values of the 14 core fonts, rounded
    to 100.
    """

    name: str = "Unknown"
    family: str = "Unknown"
    weight: str = "Unknown"

    ascent: float = 700.0
    descent: float = -200.0
    cap_height: float = 600.0
    x_height: float = 500.0
    italic_angle: float = 0.0  # Non-italic
    flags: int = 32  # Non-serif, non-symbolic, not fixed width
    bbox: tuple[float, float, float, float] = field(default_factory=lambda: (-100.0, -200.0, 1000.0, 900.0))


@dataclass(frozen=True)
class CoreFontMetrics:
    font_descriptor: FontDescriptor
    character_widths: dict[str, int]


@dataclass
class Font:
    """
    A font object for use during text extraction and for producing
    text appearance streams.

    Attributes:
        name: Font name, derived from font["/BaseFont"]
        character_map: The font's character map
        encoding: Font encoding
        sub_type: The font type, such as Type1, TrueType, or Type3.
        font_descriptor: Font metrics, including a mapping of characters to widths
        character_widths: A mapping of characters to widths
        space_width: The width of a space, or an approximation
        interpretable: Default True. If False, the font glyphs cannot
            be translated to characters, e.g. Type3 fonts that do not define
            a '/ToUnicode' mapping.

    """

    name: str
    encoding: Union[str, dict[int, str]]
    character_map: dict[Any, Any] = field(default_factory=dict)
    sub_type: str = "Unknown"
    font_descriptor: FontDescriptor = field(default_factory=FontDescriptor)
    character_widths: dict[str, int] = field(default_factory=lambda: {"default": 500})
    space_width: Union[float, int] = 250
    interpretable: bool = True

    @staticmethod
    def _collect_tt_t1_character_widths(
        pdf_font_dict: DictionaryObject,
        char_map: dict[Any, Any],
        encoding: Union[str, dict[int, str]],
        current_widths: dict[str, int]
    ) -> None:
        """Parses a TrueType or Type1 font's /Widths array from a font dictionary and updates character widths"""
        pass

    @staticmethod
    def _collect_cid_character_widths(
        d_font: DictionaryObject, char_map: dict[Any, Any], current_widths: dict[str, int]
    ) -> None:
        """Parses the /W array from a DescendantFont dictionary and updates character widths."""
        pass

    @staticmethod
    def _add_default_width(current_widths: dict[str, int], flags: int) -> None:
        pass

    @staticmethod
    def _parse_font_descriptor(font_descriptor_obj: DictionaryObject) -> dict[str, Any]:
        pass

    @classmethod
    def from_font_resource(
        cls,
        pdf_font_dict: DictionaryObject,
    ) -> "Font":
        pass

    def as_font_resource(self) -> DictionaryObject:
        # For now, this returns a font resource that only works with the 14 Adobe Core fonts.
        pass

    def text_width(self, text: str = "") -> float:
        """Sum of character widths specified in PDF font for the supplied text."""
        pass

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional, Union, cast

from .._codecs import fill_from_encoding
from .._codecs.core_font_metrics import CORE_FONT_METRICS
from .._font import Font
from .._utils import logger_warning
from ..constants import AnnotationDictionaryAttributes, BorderStyles, FieldDictionaryAttributes
from ..generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    RectangleObject,
)
from ..generic._base import ByteStringObject, TextStringObject, is_null_or_none

DEFAULT_FONT_SIZE_IN_MULTILINE = 12


@dataclass
class BaseStreamConfig:
    """A container representing the basic layout of an appearance stream."""
    rectangle: Union[RectangleObject, tuple[float, float, float, float]] = (0.0, 0.0, 0.0, 0.0)
    border_width: int = 1  # The width of the border in points
    border_style: str = BorderStyles.SOLID


class BaseStreamAppearance(DecodedStreamObject):
    """A class representing the very base of an appearance stream, that is, a rectangle and a border."""

    def __init__(self, layout: Optional[BaseStreamConfig] = None) -> None:
        """
        Takes the appearance stream layout as an argument.

        Args:
            layout: The basic layout parameters.
        """
        super().__init__()
        self._layout = layout or BaseStreamConfig()
        self[NameObject("/Type")] = NameObject("/XObject")
        self[NameObject("/Subtype")] = NameObject("/Form")
        self[NameObject("/BBox")] = RectangleObject(self._layout.rectangle)


class TextAlignment(IntEnum):
    """Defines the alignment options for text within a form field's appearance stream."""

    LEFT = 0
    CENTER = 1
    RIGHT = 2


class TextStreamAppearance(BaseStreamAppearance):
    """
    A class representing the appearance stream for a text-based form field.

    This class generates the content stream (the `ap_stream_data`) that dictates
    how text is rendered within a form field's bounding box. It handles properties
    like font, font size, color, multiline text, and text selection highlighting.
    """

    def _scale_text(
        self,
        font: Font,
        font_size: float,
        leading_factor: float,
        field_width: float,
        field_height: float,
        text: str,
        min_font_size: float,
        font_size_step: float = 0.2
    ) -> tuple[list[tuple[float, str]], float]:
        """
        Takes a piece of text and scales it to field_width or field_height, given font_name
        and font_size. Wraps text where necessary.

        Args:
            font: The font to be used.
            font_size: The font size in points.
            leading_factor: The line distance.
            field_width: The width of the field in which to fit the text.
            field_height: The height of the field in which to fit the text.
            text: The text to fit with the field.
            min_font_size: The minimum font size at which to scale the text.
            font_size_step: The amount by which to decrement font size per step while scaling.

        Returns:
            The text in the form of list of tuples, each tuple containing the length of a line
            and its contents, and the font_size for these lines and lengths.
        """
        pass

    def _generate_appearance_stream_data(
        self,
        text: str,
        selection: Union[list[str], None],
        font: Font,
        font_glyph_byte_map: Optional[dict[str, bytes]] = None,
        font_name: str = "/Helv",
        font_size: float = 0.0,
        font_color: str = "0 g",
        is_multiline: bool = False,
        alignment: TextAlignment = TextAlignment.LEFT,
        is_comb: bool = False,
        max_length: Optional[int] = None
    ) -> bytes:
        """
        Generates the raw bytes of the PDF appearance stream for a text field.

        This private method assembles the PDF content stream operators to draw
        the provided text within the specified rectangle. It handles text positioning,
        font application, color, and special formatting like selected text.

        Args:
            text: The text to be rendered in the form field.
            selection: An optional list of strings that should be highlighted as selected.
            font: The font to use.
            font_glyph_byte_map: An optional dictionary mapping characters to their
                byte representation for glyph encoding.
            font_name: The name of the font resource to use (e.g., "/Helv").
            font_size: The font size. If 0, it is automatically calculated
                based on whether the field is multiline or not.
            font_color: The color to apply to the font, represented as a PDF
                graphics state string (e.g., "0 g" for black).
            is_multiline: A boolean indicating if the text field is multiline.
            alignment: Text alignment, can be TextAlignment.LEFT, .RIGHT, or .CENTER.
            is_comb: Boolean that designates fixed-length fields, where every character
                fills one "cell", such as in a postcode.
            max_length: Used if is_comb is set. The maximum number of characters for a fixed-
                length field.

        Returns:
            A byte string containing the PDF content stream data.

        """
        pass

    def __init__(
        self,
        layout: Optional[BaseStreamConfig] = None,
        text: str = "",
        selection: Optional[list[str]] = None,
        font_resource: Optional[DictionaryObject] = None,
        font_name: str = "/Helv",
        font_size: float = 0.0,
        font_color: str = "0 g",
        is_multiline: bool = False,
        alignment: TextAlignment = TextAlignment.LEFT,
        is_comb: bool = False,
        max_length: Optional[int] = None
    ) -> None:
        """
        Initializes a TextStreamAppearance object.

        This constructor creates a new PDF stream object configured as an XObject
        of subtype Form. It uses the `_appearance_stream_data` method to generate
        the content for the stream.

        Args:
            layout: The basic layout parameters.
            text: The text to be rendered in the form field.
            selection: An optional list of strings that should be highlighted as selected.
            font_resource: An optional variable that represents a PDF font dictionary.
            font_name: The name of the font resource, e.g., "/Helv".
            font_size: The font size. If 0, it's auto-calculated.
            font_color: The font color string.
            is_multiline: A boolean indicating if the text field is multiline.
            alignment: Text alignment, can be TextAlignment.LEFT, .RIGHT, or .CENTER.
            is_comb: Boolean that designates fixed-length fields, where every character
                fills one "cell", such as in a postcode.
            max_length: Used if is_comb is set. The maximum number of characters for a fixed-
                length field.

        """
        super().__init__(layout)

        # If a font resource was added, get the font character map
        if font_resource:
            font = Font.from_font_resource(font_resource)
        else:
            logger_warning(f"Font dictionary for {font_name} not found; defaulting to Helvetica.", __name__)
            font_name = "/Helv"
            core_font_metrics = CORE_FONT_METRICS["Helvetica"]
            font = Font(
                name="Helvetica",
                character_map={},
                encoding=dict(zip(range(256), fill_from_encoding("cp1252"))),  # WinAnsiEncoding
                sub_type="Type1",
                font_descriptor=core_font_metrics.font_descriptor,
                character_widths=core_font_metrics.character_widths
            )
            font_resource = font.as_font_resource()

        # Check whether the font resource is able to encode the text value.
        encodable = True
        try:
            if isinstance(font.encoding, str):
                text.encode(font.encoding, "surrogatepass")
            else:
                supported_chars = set(font.encoding.values())
                if any(char not in supported_chars for char in text):
                    encodable = False
            # We should add a final check against the character_map (CMap) of the font,
            # but we don't appear to have PDF forms with such fonts, so we skip this for
            # now.

        except UnicodeEncodeError:
            encodable = False

        if not encodable:
            logger_warning(
                f"Text string '{text}' contains characters not supported by font encoding. "
                "This may result in text corruption. "
                "Consider calling writer.update_page_form_field_values with auto_regenerate=True.",
                __name__
            )

        font_glyph_byte_map: dict[str, bytes]
        if isinstance(font.encoding, str):
            font_glyph_byte_map = {
                v: k.encode(font.encoding) for k, v in font.character_map.items()
            }
        else:
            font_glyph_byte_map = {v: bytes((k,)) for k, v in font.encoding.items()}
            font_encoding_rev = {v: bytes((k,)) for k, v in font.encoding.items()}
            for key, value in font.character_map.items():
                font_glyph_byte_map[value] = font_encoding_rev.get(key, key)

        ap_stream_data = self._generate_appearance_stream_data(
            text,
            selection,
            font,
            font_glyph_byte_map,
            font_name=font_name,
            font_size=font_size,
            font_color=font_color,
            is_multiline=is_multiline,
            alignment=alignment,
            is_comb=is_comb,
            max_length=max_length
        )

        self.set_data(ByteStringObject(ap_stream_data))
        self[NameObject("/Length")] = NumberObject(len(ap_stream_data))
        # Update Resources with font information
        self[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({
                NameObject(font_name): getattr(font_resource, "indirect_reference", font_resource)
            })
        })

    @staticmethod
    def _find_annotation_font_resource(
            font_name: str,
            annotation: DictionaryObject,
            acro_form: DictionaryObject
        ) -> tuple[str, DictionaryObject]:
        # Try to find a resource dictionary for the font by examining the annotation and, if that fails,
        # the AcroForm resources dictionary
        pass

    @classmethod
    def from_text_annotation(
        cls,
        acro_form: DictionaryObject,  # _root_object[CatalogDictionary.ACRO_FORM])
        field: DictionaryObject,
        annotation: DictionaryObject,
        user_font_name: str = "",
        user_font_size: float = -1,
    ) -> "TextStreamAppearance":
        """
        Creates a TextStreamAppearance object from a text field annotation.

        This class method is a factory for creating a `TextStreamAppearance`
        instance by extracting all necessary information (bounding box, font,
        text content, etc.) from the PDF field and annotation dictionaries.
        It respects inheritance for properties like default appearance (`/DA`).

        Args:
            acro_form: The root AcroForm dictionary from the PDF catalog.
            field: The field dictionary object.
            annotation: The widget annotation dictionary object associated with the field.
            user_font_name: An optional user-provided font name to override the
                default. Defaults to an empty string.
            user_font_size: An optional user-provided font size to override the
                default. A value of -1 indicates no override.

        Returns:
            A new `TextStreamAppearance` instance configured for the given field.

        """
        pass

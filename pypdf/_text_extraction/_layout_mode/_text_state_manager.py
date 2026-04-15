"""manage the PDF transform stack during "layout" mode text extraction"""

from collections import ChainMap, Counter
from collections import ChainMap as ChainMapType
from collections import Counter as CounterType
from collections.abc import MutableMapping
from typing import Any, Union

from ..._font import Font
from ...errors import PdfReadError
from .. import mult
from ._text_state_params import TextStateParams

TextStateManagerChainMapType = ChainMapType[Union[int, str], Union[float, bool]]
TextStateManagerDictType = MutableMapping[Union[int, str], Union[float, bool]]


class TextStateManager:
    """
    Tracks the current text state including cm/tm/trm transformation matrices.

    Attributes:
        transform_stack (ChainMap): ChainMap of cm/tm transformation matrices
        q_queue (Counter[int]): Counter of q operators
        q_depth (List[int]): list of q operator nesting levels
        Tc (float): character spacing
        Tw (float): word spacing
        Tz (int): horizontal scaling
        TL (float): leading
        Ts (float): text rise
        font (Font): font object
        font_size (int | float): font size

    """

    def __init__(self) -> None:
        self.transform_stack: TextStateManagerChainMapType = ChainMap(
            self.new_transform()
        )
        self.q_queue: CounterType[int] = Counter()
        self.q_depth = [0]
        self.Tc: float = 0.0
        self.Tw: float = 0.0
        self.Tz: float = 100.0
        self.TL: float = 0.0
        self.Ts: float = 0.0
        self.font_stack: list[tuple[Union[Font, None], Union[int, float]]] = []
        self.font: Union[Font, None] = None
        self.font_size: Union[int, float] = 0

    def set_state_param(self, op: bytes, value: Union[float, list[Any]]) -> None:
        """
        Set a text state parameter. Supports Tc, Tz, Tw, TL, and Ts operators.

        Args:
            op: operator read from PDF stream as bytes. No action is taken
                for unsupported operators (see supported operators above).
            value (float | List[Any]): new parameter value. If a list,
                value[0] is used.

        """
        pass

    def set_font(self, font: Font, size: float) -> None:
        """
        Set the current font and font_size.

        Args:
            font (Font): a layout mode Font
            size (float): font size

        """
        pass

    def text_state_params(self, value: Union[bytes, str] = "") -> TextStateParams:
        """
        Create a TextStateParams instance to display a text string. Type[bytes] values
        will be decoded implicitly.

        Args:
            value (str | bytes): text to associate with the captured state.

        Raises:
            PdfReadError: if font not set (no Tf operator in incoming pdf content stream)

        Returns:
            TextStateParams: current text state parameters

        """
        pass

    @staticmethod
    def raw_transform(
        _a: float = 1.0,
        _b: float = 0.0,
        _c: float = 0.0,
        _d: float = 1.0,
        _e: float = 0.0,
        _f: float = 0.0,
    ) -> dict[int, float]:
        """Only a/b/c/d/e/f matrix params"""
        pass

    @staticmethod
    def new_transform(
        _a: float = 1.0,
        _b: float = 0.0,
        _c: float = 0.0,
        _d: float = 1.0,
        _e: float = 0.0,
        _f: float = 0.0,
        is_text: bool = False,
        is_render: bool = False,
    ) -> TextStateManagerDictType:
        """Standard a/b/c/d/e/f matrix params + 'is_text' and 'is_render' keys"""
        pass

    def reset_tm(self) -> TextStateManagerChainMapType:
        """Clear all transforms from chainmap having is_text==True or is_render==True"""
        pass

    def reset_trm(self) -> TextStateManagerChainMapType:
        """Clear all transforms from chainmap having is_render==True"""
        pass

    def remove_q(self) -> TextStateManagerChainMapType:
        """Rewind to stack prior state after closing a 'q' with internal 'cm' ops"""
        pass

    def add_q(self) -> None:
        """Add another level to q_queue"""
        pass

    def add_cm(self, *args: Any) -> TextStateManagerChainMapType:
        """Concatenate an additional transform matrix"""
        pass

    def _complete_matrix(self, operands: list[float]) -> list[float]:
        """Adds a, b, c, and d to an "e/f only" operand set (e.g Td)"""
        pass

    def add_tm(self, operands: list[float]) -> TextStateManagerChainMapType:
        """Append a text transform matrix"""
        pass

    def add_trm(self, operands: list[float]) -> TextStateManagerChainMapType:
        """Append a text rendering transform matrix"""
        pass

    @property
    def effective_transform(self) -> list[float]:
        """Current effective transform accounting for cm, tm, and trm transforms"""
        pass

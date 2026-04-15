from typing import Any, Union

from ._base import FloatObject, NumberObject
from ._data_structures import ArrayObject


class RectangleObject(ArrayObject):
    """
    This class is used to represent *page boxes* in pypdf.

    These boxes include:

    * :attr:`artbox <pypdf._page.PageObject.artbox>`
    * :attr:`bleedbox <pypdf._page.PageObject.bleedbox>`
    * :attr:`cropbox <pypdf._page.PageObject.cropbox>`
    * :attr:`mediabox <pypdf._page.PageObject.mediabox>`
    * :attr:`trimbox <pypdf._page.PageObject.trimbox>`
    """

    def __init__(
        self, arr: Union["RectangleObject", tuple[float, float, float, float]]
    ) -> None:
        # must have four points
        assert len(arr) == 4
        # automatically convert arr[x] into NumberObject(arr[x]) if necessary
        ArrayObject.__init__(self, [self._ensure_is_number(x) for x in arr])

    def _ensure_is_number(self, value: Any) -> Union[FloatObject, NumberObject]:
        pass

    def scale(self, sx: float, sy: float) -> "RectangleObject":
        pass

    def __repr__(self) -> str:
        return f"RectangleObject({list(self)!r})"

    @property
    def left(self) -> FloatObject:
        pass

    @left.setter
    def left(self, f: float) -> None:
        pass

    @property
    def bottom(self) -> FloatObject:
        pass

    @bottom.setter
    def bottom(self, f: float) -> None:
        pass

    @property
    def right(self) -> FloatObject:
        pass

    @right.setter
    def right(self, f: float) -> None:
        pass

    @property
    def top(self) -> FloatObject:
        pass

    @top.setter
    def top(self, f: float) -> None:
        pass

    @property
    def lower_left(self) -> tuple[float, float]:
        """
        Property to read and modify the lower left coordinate of this box
        in (x,y) form.
        """
        pass

    @lower_left.setter
    def lower_left(self, value: tuple[float, float]) -> None:
        pass

    @property
    def lower_right(self) -> tuple[float, float]:
        """
        Property to read and modify the lower right coordinate of this box
        in (x,y) form.
        """
        pass

    @lower_right.setter
    def lower_right(self, value: tuple[float, float]) -> None:
        pass

    @property
    def upper_left(self) -> tuple[float, float]:
        """
        Property to read and modify the upper left coordinate of this box
        in (x,y) form.
        """
        pass

    @upper_left.setter
    def upper_left(self, value: tuple[float, float]) -> None:
        pass

    @property
    def upper_right(self) -> tuple[float, float]:
        """
        Property to read and modify the upper right coordinate of this box
        in (x,y) form.
        """
        pass

    @upper_right.setter
    def upper_right(self, value: tuple[float, float]) -> None:
        pass

    @property
    def width(self) -> float:
        pass

    @property
    def height(self) -> float:
        pass

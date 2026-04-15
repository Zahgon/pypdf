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
from collections.abc import Iterable, Iterator, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    cast,
    overload,
)

from ._font import Font
from ._protocols import PdfCommonDocProtocol
from ._text_extraction import (
    _layout_mode,
)
from ._text_extraction._text_extractor import TextExtraction
from ._utils import (
    CompressedTransformationMatrix,
    TransformationMatrixType,
    _human_readable_bytes,
    deprecate,
    logger_warning,
    matrix_multiply,
)
from .constants import _INLINE_IMAGE_KEY_MAPPING, _INLINE_IMAGE_VALUE_MAPPING
from .constants import AnnotationDictionaryAttributes as ADA
from .constants import ImageAttributes as IA
from .constants import PageAttributes as PG
from .constants import Resources as RES
from .errors import PageSizeNotDefinedError, PdfReadError
from .generic import (
    ArrayObject,
    ContentStream,
    DictionaryObject,
    EncodedStreamObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    PdfObject,
    RectangleObject,
    StreamObject,
    is_null_or_none,
)

try:
    from PIL.Image import Image

    pil_not_imported = False
except ImportError:
    Image = object  # type: ignore[assignment,misc,unused-ignore]  # TODO: Remove unused-ignore on Python 3.10
    pil_not_imported = True  # error will be raised only when using images

MERGE_CROP_BOX = "cropbox"  # pypdf <= 3.4.0 used "trimbox"


def _get_rectangle(self: Any, name: str, defaults: Iterable[str]) -> RectangleObject:
    retval: Union[None, RectangleObject, ArrayObject, IndirectObject] = self.get(name)
    if isinstance(retval, RectangleObject):
        return retval
    if is_null_or_none(retval):
        for d in defaults:
            retval = self.get(d)
            if retval is not None:
                break
    if isinstance(retval, IndirectObject):
        retval = self.pdf.get_object(retval)
    if isinstance(retval, ArrayObject) and (length := len(retval)) > 4:
        logger_warning(f"Expected four values, got {length}: {retval}", __name__)
        retval = RectangleObject(tuple(retval[:4]))
    else:
        retval = RectangleObject(retval)  # type: ignore
    _set_rectangle(self, name, retval)
    return retval


def _set_rectangle(self: Any, name: str, value: Union[RectangleObject, float]) -> None:
    self[NameObject(name)] = value


def _delete_rectangle(self: Any, name: str) -> None:
    del self[name]


def _create_rectangle_accessor(name: str, fallback: Iterable[str]) -> property:
    return property(
        lambda self: _get_rectangle(self, name, fallback),
        lambda self, value: _set_rectangle(self, name, value),
        lambda self: _delete_rectangle(self, name),
    )


class Transformation:
    """
    Represent a 2D transformation.

    The transformation between two coordinate systems is represented by a 3-by-3
    transformation matrix with the following form::

        a b 0
        c d 0
        e f 1

    Because a transformation matrix has only six elements that can be changed,
    it is usually specified in PDF as the six-element array [ a b c d e f ].

    Coordinate transformations are expressed as matrix multiplications::

                                 a b 0
     [ x′ y′ 1 ] = [ x y 1 ] ×   c d 0
                                 e f 1


    Example:
        >>> from pypdf import PdfWriter, Transformation
        >>> page = PdfWriter().add_blank_page(800, 600)
        >>> op = Transformation().scale(sx=2, sy=3).translate(tx=10, ty=20)
        >>> page.add_transformation(op)

    """

    def __init__(self, ctm: CompressedTransformationMatrix = (1, 0, 0, 1, 0, 0)) -> None:
        self.ctm = ctm

    @property
    def matrix(self) -> TransformationMatrixType:
        """
        Return the transformation matrix as a tuple of tuples in the form:

        ((a, b, 0), (c, d, 0), (e, f, 1))
        """
        pass

    @staticmethod
    def compress(matrix: TransformationMatrixType) -> CompressedTransformationMatrix:
        """
        Compresses the transformation matrix into a tuple of (a, b, c, d, e, f).

        Args:
            matrix: The transformation matrix as a tuple of tuples.

        Returns:
            A tuple representing the transformation matrix as (a, b, c, d, e, f)

        """
        return (
            matrix[0][0],
            matrix[0][1],
            matrix[1][0],
            matrix[1][1],
            matrix[2][0],
            matrix[2][1],
        )

    def _to_cm(self) -> str:
        # Returns the cm operation string for the given transformation matrix
        pass

    def transform(self, m: "Transformation") -> "Transformation":
        """
        Apply one transformation to another.

        Args:
            m: a Transformation to apply.

        Returns:
            A new ``Transformation`` instance

        Example:
            >>> from pypdf import PdfWriter, Transformation
            >>> height, width = 40, 50
            >>> page = PdfWriter().add_blank_page(800, 600)
            >>> op = Transformation((1, 0, 0, -1, 0, height)) # vertical mirror
            >>> op = Transformation().transform(Transformation((-1, 0, 0, 1, width, 0)))  # horizontal mirror
            >>> page.add_transformation(op)

        """
        pass

    def translate(self, tx: float = 0, ty: float = 0) -> "Transformation":
        """
        Translate the contents of a page.

        Args:
            tx: The translation along the x-axis.
            ty: The translation along the y-axis.

        Returns:
            A new ``Transformation`` instance

        """
        pass

    def scale(
        self, sx: Optional[float] = None, sy: Optional[float] = None
    ) -> "Transformation":
        """
        Scale the contents of a page towards the origin of the coordinate system.

        Typically, that is the lower-left corner of the page. That can be
        changed by translating the contents / the page boxes.

        Args:
            sx: The scale factor along the x-axis.
            sy: The scale factor along the y-axis.

        Returns:
            A new Transformation instance with the scaled matrix.

        """
        pass

    def rotate(self, rotation: float) -> "Transformation":
        """
        Rotate the contents of a page.

        Args:
            rotation: The angle of rotation in degrees.

        Returns:
            A new ``Transformation`` instance with the rotated matrix.

        """
        pass

    def __repr__(self) -> str:
        return f"Transformation(ctm={self.ctm})"

    @overload
    def apply_on(self, pt: list[float], as_object: bool = False) -> list[float]:
        ...

    @overload
    def apply_on(
        self, pt: tuple[float, float], as_object: bool = False
    ) -> tuple[float, float]:
        ...

    def apply_on(
        self,
        pt: Union[tuple[float, float], list[float]],
        as_object: bool = False,
    ) -> Union[tuple[float, float], list[float]]:
        """
        Apply the transformation matrix on the given point.

        Args:
            pt: A tuple or list representing the point in the form (x, y).
            as_object: If True, return items as FloatObject, otherwise as plain floats.

        Returns:
            A tuple or list representing the transformed point in the form (x', y')

        """
        pass


@dataclass
class ImageFile:
    """
    Image within the PDF file. *This object is not designed to be built.*

    This object should not be modified except using :func:`ImageFile.replace` to replace the image with a new one.
    """

    name: str = ""
    """
    Filename as identified within the PDF file.
    """

    data: bytes = b""
    """
    Data as bytes.
    """

    image: Optional[Image] = None
    """
    Data as PIL image.
    """

    indirect_reference: Optional[IndirectObject] = None
    """
    Reference to the object storing the stream.
    """

    def replace(self, new_image: Image, **kwargs: Any) -> None:
        """
        Replace the image with a new PIL image.

        Args:
            new_image (PIL.Image.Image): The new PIL image to replace the existing image.
            **kwargs: Additional keyword arguments to pass to `Image.save()`.

        Raises:
            TypeError: If the image is inline or in a PdfReader.
            TypeError: If the image does not belong to a PdfWriter.
            TypeError: If `new_image` is not a PIL Image.

        Note:
            This method replaces the existing image with a new image.
            It is not allowed for inline images or images within a PdfReader.
            The `kwargs` parameter allows passing additional parameters
            to `Image.save()`, such as quality.

        """
        if pil_not_imported:
            raise ImportError(
                "pillow is required to do image extraction. "
                "It can be installed via 'pip install pypdf[image]'"
            )

        from ._reader import PdfReader  # noqa: PLC0415
        from .generic import DictionaryObject, PdfObject  # noqa: PLC0415
        from .generic._image_xobject import _xobj_to_image  # noqa: PLC0415

        if self.indirect_reference is None:
            raise TypeError("Cannot update an inline image.")
        if not hasattr(self.indirect_reference.pdf, "_id_translated"):
            raise TypeError("Cannot update an image not belonging to a PdfWriter.")
        if not isinstance(new_image, Image):
            raise TypeError("new_image shall be a PIL Image")
        b = BytesIO()
        new_image.save(b, "PDF", **kwargs)
        reader = PdfReader(b)
        page_image = reader.pages[0].images[0]
        assert page_image.indirect_reference is not None
        self.indirect_reference.pdf._objects[self.indirect_reference.idnum - 1] = (
            page_image.indirect_reference.get_object()
        )
        cast(
            PdfObject, self.indirect_reference.get_object()
        ).indirect_reference = self.indirect_reference
        # change the object attributes
        extension, byte_stream, img = _xobj_to_image(
            cast(DictionaryObject, self.indirect_reference.get_object()),
            pillow_parameters=kwargs,
        )
        assert extension is not None
        self.name = self.name[: self.name.rfind(".")] + extension
        self.data = byte_stream
        self.image = img

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, data: {_human_readable_bytes(len(self.data))})"

    def __repr__(self) -> str:
        return self.__str__()[:-1] + f", hash: {hash(self.data)})"


class VirtualListImages(Sequence[ImageFile]):
    """
    Provides access to images referenced within a page.
    Only one copy will be returned if the usage is used on the same page multiple times.
    See :func:`PageObject.images` for more details.
    """

    def __init__(
        self,
        ids_function: Callable[[], list[Union[str, list[str]]]],
        get_function: Callable[[Union[str, list[str], tuple[str]]], ImageFile],
    ) -> None:
        self.ids_function = ids_function
        self.get_function = get_function
        self.current = -1

    def __len__(self) -> int:
        return len(self.ids_function())

    def keys(self) -> list[Union[str, list[str]]]:
        return self.ids_function()

    def items(self) -> list[tuple[Union[str, list[str]], ImageFile]]:
        return [(x, self[x]) for x in self.ids_function()]

    @overload
    def __getitem__(self, index: Union[int, str, list[str]]) -> ImageFile:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[ImageFile]:
        ...

    def __getitem__(
        self, index: Union[int, slice, str, list[str], tuple[str]]
    ) -> Union[ImageFile, Sequence[ImageFile]]:
        lst = self.ids_function()
        if isinstance(index, slice):
            indices = range(*index.indices(len(self)))
            lst = [lst[x] for x in indices]
            cls = type(self)
            return cls((lambda: lst), self.get_function)
        if isinstance(index, (str, list, tuple)):
            return self.get_function(index)
        if not isinstance(index, int):
            raise TypeError("Invalid sequence indices type")
        len_self = len(lst)
        if index < 0:
            # support negative indexes
            index += len_self
        if not (0 <= index < len_self):
            raise IndexError("Sequence index out of range")
        return self.get_function(lst[index])

    def __iter__(self) -> Iterator[ImageFile]:
        for i in range(len(self)):
            yield self[i]

    def __str__(self) -> str:
        p = [f"Image_{i}={n}" for i, n in enumerate(self.ids_function())]
        return f"[{', '.join(p)}]"


class PageObject(DictionaryObject):
    """
    PageObject represents a single page within a PDF file.

    Typically these objects will be created by accessing the
    :attr:`pages<pypdf.PdfReader.pages>` property of the
    :class:`PdfReader<pypdf.PdfReader>` class, but it is
    also possible to create an empty page with the
    :meth:`create_blank_page()<pypdf._page.PageObject.create_blank_page>` static method.

    Args:
        pdf: PDF file the page belongs to.
        indirect_reference: Stores the original indirect reference to
            this object in its source PDF

    """

    original_page: "PageObject"  # very local use in writer when appending

    def __init__(
        self,
        pdf: Optional[PdfCommonDocProtocol] = None,
        indirect_reference: Optional[IndirectObject] = None,
    ) -> None:
        DictionaryObject.__init__(self)
        self.pdf = pdf
        self.inline_images: Optional[dict[str, ImageFile]] = None
        self.indirect_reference = indirect_reference
        if not is_null_or_none(indirect_reference):
            assert indirect_reference is not None, "mypy"
            self.update(cast(DictionaryObject, indirect_reference.get_object()))
        self._font_width_maps: dict[str, tuple[dict[str, float], str, float]] = {}

    def hash_bin(self) -> int:
        """
        Used to detect modified object.

        Note: this function is overloaded to return the same results
        as a DictionaryObject.

        Returns:
            Hash considering type and value.

        """
        return hash(
            (DictionaryObject, tuple(((k, v.hash_bin()) for k, v in self.items())))
        )

    def hash_value_data(self) -> bytes:
        pass

    @property
    def user_unit(self) -> float:
        """
        A read-only positive number giving the size of user space units.

        It is in multiples of 1/72 inch. Hence a value of 1 means a user
        space unit is 1/72 inch, and a value of 3 means that a user
        space unit is 3/72 inch.
        """
        pass

    @staticmethod
    def create_blank_page(
        pdf: Optional[PdfCommonDocProtocol] = None,
        width: Union[float, Decimal, None] = None,
        height: Union[float, Decimal, None] = None,
    ) -> "PageObject":
        """
        Return a new blank page.

        If ``width`` or ``height`` is ``None``, try to get the page size
        from the last page of *pdf*.

        Args:
            pdf: PDF file the page is within.
            width: The width of the new page expressed in default user
                space units.
            height: The height of the new page expressed in default user
                space units.

        Returns:
            The new blank page

        Raises:
            PageSizeNotDefinedError: if ``pdf`` is ``None`` or contains
                no page

        """
        pass

    def _get_ids_image(
        self,
        obj: Optional[DictionaryObject] = None,
        ancest: Optional[list[str]] = None,
        call_stack: Optional[list[Any]] = None,
    ) -> list[Union[str, list[str]]]:
        pass

    def _get_image(
        self,
        id: Union[str, list[str], tuple[str]],
        obj: Optional[DictionaryObject] = None,
    ) -> ImageFile:
        pass

    @property
    def images(self) -> VirtualListImages:
        """
        Read-only property emulating a list of images on a page.

        Get a list of all images on the page. The key can be:
        - A string (for the top object)
        - A tuple (for images within XObject forms)
        - An integer

        Examples:
            * `reader.pages[0].images[0]`        # return first image
            * `reader.pages[0].images['/I0']`    # return image '/I0'
            * `reader.pages[0].images['/TP1','/Image1']` # return image '/Image1' within '/TP1' XObject form
            * `for img in reader.pages[0].images:` # loops through all objects

        images.keys() and images.items() can be used.

        The ImageFile has the following properties:

            * `.name` : name of the object
            * `.data` : bytes of the object
            * `.image` : PIL Image Object
            * `.indirect_reference` : object reference

        and the following methods:
            `.replace(new_image: PIL.Image.Image, **kwargs)` :
                replace the image in the pdf with the new image
                applying the saving parameters indicated (such as quality)

        Example usage:

            reader.pages[0].images[0].replace(Image.open("new_image.jpg"), quality=20)

        Inline images are extracted and named ~0~, ~1~, ..., with the
        indirect_reference set to None.

        """
        pass

    def _translate_value_inline_image(self, k: str, v: PdfObject) -> PdfObject:
        """Translate values used in inline image"""
        pass

    def _get_inline_images(self) -> dict[str, ImageFile]:
        """Load inline images. Entries will be identified as `~1~`."""
        pass

    @property
    def rotation(self) -> int:
        """
        The visual rotation of the page.

        This number has to be a multiple of 90 degrees: 0, 90, 180, or 270 are
        valid values. This property does not affect ``/Contents``.
        """
        pass

    @rotation.setter
    def rotation(self, r: float) -> None:
        pass

    def transfer_rotation_to_content(self) -> None:
        """
        Apply the rotation of the page to the content and the media/crop/...
        boxes.

        It is recommended to apply this function before page merging.
        """
        pass

    def rotate(self, angle: int) -> "PageObject":
        """
        Rotate a page clockwise by increments of 90 degrees.

        Args:
            angle: Angle to rotate the page. Must be an increment of 90 deg.

        Returns:
            The rotated PageObject

        """
        pass

    def _merge_resources(
        self,
        res1: DictionaryObject,
        res2: DictionaryObject,
        resource: Any,
        new_res1: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        pass

    @staticmethod
    def _content_stream_rename(
        stream: ContentStream,
        rename: dict[Any, Any],
        pdf: Optional[PdfCommonDocProtocol],
    ) -> ContentStream:
        pass

    @staticmethod
    def _add_transformation_matrix(
        contents: Any,
        pdf: Optional[PdfCommonDocProtocol],
        ctm: CompressedTransformationMatrix,
    ) -> ContentStream:
        """Add transformation matrix at the beginning of the given contents stream."""
        pass

    def _get_contents_as_bytes(self) -> Optional[bytes]:
        """
        Return the page contents as bytes.

        Returns:
            The ``/Contents`` object as bytes, or ``None`` if it doesn't exist.

        """
        pass

    def get_contents(self) -> Optional[ContentStream]:
        """
        Access the page contents.

        Returns:
            The ``/Contents`` object, or ``None`` if it does not exist.
            ``/Contents`` is optional, as described in §7.7.3.3 of the PDF Reference.

        """
        pass

    def replace_contents(
        self, content: Union[None, ContentStream, EncodedStreamObject, ArrayObject]
    ) -> None:
        """
        Replace the page contents with the new content and nullify old objects
        Args:
            content: new content; if None delete the content field.
        """
        pass

    def merge_page(
        self, page2: "PageObject", expand: bool = False, over: bool = True
    ) -> None:
        """
        Merge the content streams of two pages into one.

        Resource references (e.g. fonts) are maintained from both pages.
        The mediabox, cropbox, etc of this page are not altered.
        The parameter page's content stream will
        be added to the end of this page's content stream,
        meaning that it will be drawn after, or "on top" of this page.

        Args:
            page2: The page to be merged into this one. Should be
                an instance of :class:`PageObject<PageObject>`.
            over: set the page2 content over page1 if True (default) else under
            expand: If True, the current page dimensions will be
                expanded to accommodate the dimensions of the page to be merged.

        """
        pass

    def _merge_page(
        self,
        page2: "PageObject",
        page2transformation: Optional[Callable[[Any], ContentStream]] = None,
        ctm: Optional[CompressedTransformationMatrix] = None,
        over: bool = True,
        expand: bool = False,
    ) -> None:
        # First we work on merging the resource dictionaries. This allows us
        # to find out what symbols in the content streams we might need to
        # rename.
        pass

    def _merge_page_writer(
        self,
        page2: "PageObject",
        page2transformation: Optional[Callable[[Any], ContentStream]] = None,
        ctm: Optional[CompressedTransformationMatrix] = None,
        over: bool = True,
        expand: bool = False,
    ) -> None:
        # First we work on merging the resource dictionaries. This allows us
        # to find which symbols in the content streams we might need to
        # rename.
        pass

    def _expand_mediabox(
        self, page2: "PageObject", ctm: Optional[CompressedTransformationMatrix]
    ) -> None:
        pass

    def merge_transformed_page(
        self,
        page2: "PageObject",
        ctm: Union[CompressedTransformationMatrix, Transformation],
        over: bool = True,
        expand: bool = False,
    ) -> None:
        """
        Similar to :meth:`~pypdf._page.PageObject.merge_page`, but a transformation
        matrix is applied to the merged stream.

        Args:
          page2: The page to be merged into this one.
          ctm: a 6-element tuple containing the operands of the
                 transformation matrix
          over: set the page2 content over page1 if True (default) else under
          expand: Whether the page should be expanded to fit the dimensions
            of the page to be merged.

        """
        pass

    def merge_scaled_page(
        self, page2: "PageObject", scale: float, over: bool = True, expand: bool = False
    ) -> None:
        """
        Similar to :meth:`~pypdf._page.PageObject.merge_page`, but the stream to be merged
        is scaled by applying a transformation matrix.

        Args:
          page2: The page to be merged into this one.
          scale: The scaling factor
          over: set the page2 content over page1 if True (default) else under
          expand: Whether the page should be expanded to fit the
            dimensions of the page to be merged.

        """
        pass

    def merge_rotated_page(
        self,
        page2: "PageObject",
        rotation: float,
        over: bool = True,
        expand: bool = False,
    ) -> None:
        """
        Similar to :meth:`~pypdf._page.PageObject.merge_page`, but the stream to be merged
        is rotated by applying a transformation matrix.

        Args:
          page2: The page to be merged into this one.
          rotation: The angle of the rotation, in degrees
          over: set the page2 content over page1 if True (default) else under
          expand: Whether the page should be expanded to fit the
            dimensions of the page to be merged.

        """
        pass

    def merge_translated_page(
        self,
        page2: "PageObject",
        tx: float,
        ty: float,
        over: bool = True,
        expand: bool = False,
    ) -> None:
        """
        Similar to :meth:`~pypdf._page.PageObject.merge_page`, but the stream to be
        merged is translated by applying a transformation matrix.

        Args:
          page2: the page to be merged into this one.
          tx: The translation on X axis
          ty: The translation on Y axis
          over: set the page2 content over page1 if True (default) else under
          expand: Whether the page should be expanded to fit the
            dimensions of the page to be merged.

        """
        pass

    def add_transformation(
        self,
        ctm: Union[Transformation, CompressedTransformationMatrix],
        expand: bool = False,
    ) -> None:
        """
        Apply a transformation matrix to the page.

        Args:
            ctm: A 6-element tuple containing the operands of the
                transformation matrix. Alternatively, a
                :py:class:`Transformation<pypdf.Transformation>`
                object can be passed.

        See :doc:`/user/cropping-and-transforming`.

        """
        pass

    def scale(self, sx: float, sy: float) -> None:
        """
        Scale a page by the given factors by applying a transformation matrix
        to its content and updating the page size.

        This updates the various page boundaries (bleedbox, trimbox, etc.)
        and the contents of the page.

        Args:
            sx: The scaling factor on horizontal axis.
            sy: The scaling factor on vertical axis.

        """
        pass

    def scale_by(self, factor: float) -> None:
        """
        Scale a page by the given factor by applying a transformation matrix to
        its content and updating the page size.

        Args:
            factor: The scaling factor (for both X and Y axis).

        """
        pass

    def scale_to(self, width: float, height: float) -> None:
        """
        Scale a page to the specified dimensions by applying a transformation
        matrix to its content and updating the page size.

        Args:
            width: The new width.
            height: The new height.

        """
        pass

    def compress_content_streams(self, level: int = -1) -> None:
        """
        Compress the size of this page by joining all content streams and
        applying a FlateDecode filter.

        However, it is possible that this function will perform no action if
        content stream compression becomes "automatic".
        """
        pass

    @property
    def page_number(self) -> Optional[int]:
        """
        Read-only property which returns the page number within the PDF file.

        Returns:
            Page number; None if the page is not attached to a PDF.

        """
        pass

    def _debug_for_extract(self) -> str:  # pragma: no cover
        pass

    def _extract_text(
        self,
        obj: Any,
        pdf: Any,
        orientations: tuple[int, ...] = (0, 90, 180, 270),
        space_width: float = 200.0,
        content_key: Optional[str] = PG.CONTENTS,
        visitor_operand_before: Optional[Callable[[Any, Any, Any, Any], None]] = None,
        visitor_operand_after: Optional[Callable[[Any, Any, Any, Any], None]] = None,
        visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]] = None,
    ) -> str:
        """
        See extract_text for most arguments.

        Args:
            content_key: indicate the default key where to extract data
                None = the object; this allows reusing the function on an XObject
                default = "/Content"

        """
        pass

    def _layout_mode_fonts(self) -> dict[str, Font]:
        """
        Get fonts formatted for "layout" mode text extraction.

        Returns:
            Dict[str, Font]: dictionary of Font instances keyed by font name

        """
        pass

    def _layout_mode_text(
        self,
        space_vertically: bool = True,
        scale_weight: float = 1.25,
        strip_rotated: bool = True,
        debug_path: Optional[Path] = None,
        font_height_weight: float = 1,
    ) -> str:
        """
        Get text preserving fidelity to source PDF text layout.

        Args:
            space_vertically: include blank lines inferred from y distance + font
                height. Defaults to True.
            scale_weight: multiplier for string length when calculating weighted
                average character width. Defaults to 1.25.
            strip_rotated: Removes text that is rotated w.r.t. to the page from
                layout mode output. Defaults to True.
            debug_path (Path | None): if supplied, must target a directory.
                creates the following files with debug information for layout mode
                functions if supplied:
                  - fonts.json: output of self._layout_mode_fonts
                  - tjs.json: individual text render ops with corresponding transform matrices
                  - bts.json: text render ops left justified and grouped by BT/ET operators
                  - bt_groups.json: BT/ET operations grouped by rendered y-coord (aka lines)
                Defaults to None.
            font_height_weight: multiplier for font height when calculating
                blank lines. Defaults to 1.

        Returns:
            str: multiline string containing page text in a fixed width format that
                closely adheres to the rendered layout in the source pdf.

        """
        pass

    def extract_text(
        self,
        *args: Any,
        orientations: Union[int, tuple[int, ...]] = (0, 90, 180, 270),
        space_width: float = 200.0,
        visitor_operand_before: Optional[Callable[[Any, Any, Any, Any], None]] = None,
        visitor_operand_after: Optional[Callable[[Any, Any, Any, Any], None]] = None,
        visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]] = None,
        extraction_mode: Literal["plain", "layout"] = "plain",
        **kwargs: Any,
    ) -> str:
        """
        Locate all text drawing commands, in the order they are provided in the
        content stream, and extract the text.

        This works well for some PDF files, but poorly for others, depending on
        the generator used. This will be refined in the future.

        Do not rely on the order of text coming out of this function, as it
        will change if this function is made more sophisticated.

        Arabic and Hebrew are extracted in the correct order.
        If required a custom RTL range of characters can be defined;
        see function set_custom_rtl.

        Additionally you can provide visitor methods to get informed on all
        operations and all text objects.
        For example in some PDF files this can be useful to parse tables.

        Args:
            orientations: list of orientations extract_text will look for
                default = (0, 90, 180, 270)
                note: currently only 0 (up),90 (turned left), 180 (upside down),
                270 (turned right)
                Silently ignored in "layout" mode.
            space_width: force default space width
                if not extracted from font (default: 200)
                Silently ignored in "layout" mode.
            visitor_operand_before: function to be called before processing an operation.
                It has four arguments: operator, operand-arguments,
                current transformation matrix and text matrix.
                Ignored with a warning in "layout" mode.
            visitor_operand_after: function to be called after processing an operation.
                It has four arguments: operator, operand-arguments,
                current transformation matrix and text matrix.
                Ignored with a warning in "layout" mode.
            visitor_text: function to be called when extracting some text at some position.
                It has five arguments: text, current transformation matrix,
                text matrix, font-dictionary and font-size.
                The font-dictionary may be None in case of unknown fonts.
                If not None it may e.g. contain key "/BaseFont" with value "/Arial,Bold".
                Ignored with a warning in "layout" mode.
            extraction_mode (Literal["plain", "layout"]): "plain" for legacy functionality,
                "layout" for experimental layout mode functionality.
                NOTE: orientations, space_width, and visitor_* parameters are NOT respected
                in "layout" mode.

        kwargs:
            layout_mode_space_vertically (bool): include blank lines inferred from
                y distance + font height. Defaults to True.
            layout_mode_scale_weight (float): multiplier for string length when calculating
                weighted average character width. Defaults to 1.25.
            layout_mode_strip_rotated (bool): layout mode does not support rotated text.
                Set to False to include rotated text anyway. If rotated text is discovered,
                layout will be degraded and a warning will result. Defaults to True.
            layout_mode_debug_path (Path | None): if supplied, must target a directory.
                creates the following files with debug information for layout mode
                functions if supplied:

                  - fonts.json: output of self._layout_mode_fonts
                  - tjs.json: individual text render ops with corresponding transform matrices
                  - bts.json: text render ops left justified and grouped by BT/ET operators
                  - bt_groups.json: BT/ET operations grouped by rendered y-coord (aka lines)
            layout_mode_font_height_weight (float): multiplier for font height when calculating
                blank lines. Defaults to 1.

        Returns:
            The extracted text

        """
        pass

    def extract_xform_text(
        self,
        xform: EncodedStreamObject,
        orientations: tuple[int, ...] = (0, 90, 270, 360),
        space_width: float = 200.0,
        visitor_operand_before: Optional[Callable[[Any, Any, Any, Any], None]] = None,
        visitor_operand_after: Optional[Callable[[Any, Any, Any, Any], None]] = None,
        visitor_text: Optional[Callable[[Any, Any, Any, Any, Any], None]] = None,
    ) -> str:
        """
        Extract text from an XObject.

        Args:
            xform:
            orientations:
            space_width:  force default space width (if not extracted from font (default 200)
            visitor_operand_before:
            visitor_operand_after:
            visitor_text:

        Returns:
            The extracted text

        """
        pass

    def _get_fonts(self) -> tuple[set[str], set[str]]:
        """
        Get the names of embedded fonts and unembedded fonts.

        Returns:
            A tuple (set of embedded fonts, set of unembedded fonts)

        """
        pass

    mediabox = _create_rectangle_accessor(PG.MEDIABOX, ())
    """A :class:`RectangleObject<pypdf.generic.RectangleObject>`, expressed in
    default user space units, defining the boundaries of the physical medium on
    which the page is intended to be displayed or printed."""

    cropbox = _create_rectangle_accessor("/CropBox", (PG.MEDIABOX,))
    """
    A :class:`RectangleObject<pypdf.generic.RectangleObject>`, expressed in
    default user space units, defining the visible region of default user
    space.

    When the page is displayed or printed, its contents are to be clipped
    (cropped) to this rectangle and then imposed on the output medium in some
    implementation-defined manner. Default value: same as
    :attr:`mediabox<mediabox>`.
    """

    bleedbox = _create_rectangle_accessor("/BleedBox", ("/CropBox", PG.MEDIABOX))
    """A :class:`RectangleObject<pypdf.generic.RectangleObject>`, expressed in
    default user space units, defining the region to which the contents of the
    page should be clipped when output in a production environment."""

    trimbox = _create_rectangle_accessor("/TrimBox", ("/CropBox", PG.MEDIABOX))
    """A :class:`RectangleObject<pypdf.generic.RectangleObject>`, expressed in
    default user space units, defining the intended dimensions of the finished
    page after trimming."""

    artbox = _create_rectangle_accessor("/ArtBox", ("/CropBox", PG.MEDIABOX))
    """A :class:`RectangleObject<pypdf.generic.RectangleObject>`, expressed in
    default user space units, defining the extent of the page's meaningful
    content as intended by the page's creator."""

    @property
    def annotations(self) -> Optional[ArrayObject]:
        pass

    @annotations.setter
    def annotations(self, value: Optional[ArrayObject]) -> None:
        """
        Set the annotations array of the page.

        Typically you do not want to set this value, but append to it.
        If you append to it, remember to add the object first to the writer
        and only add the indirect object.
        """
        pass


class _VirtualList(Sequence[PageObject]):
    def __init__(
        self,
        length_function: Callable[[], int],
        get_function: Callable[[int], PageObject],
    ) -> None:
        self.length_function = length_function
        self.get_function = get_function
        self.current = -1

    def __len__(self) -> int:
        return self.length_function()

    @overload
    def __getitem__(self, index: int) -> PageObject:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[PageObject]:
        ...

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[PageObject, Sequence[PageObject]]:
        if isinstance(index, slice):
            indices = range(*index.indices(len(self)))
            cls = type(self)
            return cls(indices.__len__, lambda idx: self[indices[idx]])
        if not isinstance(index, int):
            raise TypeError("Sequence indices must be integers")
        len_self = len(self)
        if index < 0:
            # support negative indexes
            index += len_self
        if not (0 <= index < len_self):
            raise IndexError("Sequence index out of range")
        return self.get_function(index)

    def __delitem__(self, index: Union[int, slice]) -> None:
        if isinstance(index, slice):
            r = list(range(*index.indices(len(self))))
            # pages have to be deleted from last to first
            r.sort()
            r.reverse()
            for p in r:
                del self[p]  # recursive call
            return
        if not isinstance(index, int):
            raise TypeError("Index must be integers")
        len_self = len(self)
        if index < 0:
            # support negative indexes
            index += len_self
        if not (0 <= index < len_self):
            raise IndexError("Index out of range")
        ind = self[index].indirect_reference
        assert ind is not None
        parent: Optional[PdfObject] = cast(DictionaryObject, ind.get_object()).get(
            "/Parent", None
        )
        first = True
        while parent is not None:
            parent = cast(DictionaryObject, parent.get_object())
            try:
                i = cast(ArrayObject, parent["/Kids"]).index(ind)
                del cast(ArrayObject, parent["/Kids"])[i]
                first = False
                try:
                    assert ind is not None
                    del ind.pdf.flattened_pages[index]  # case of page in a Reader
                except Exception:  # pragma: no cover
                    pass
                if "/Count" in parent:
                    parent[NameObject("/Count")] = NumberObject(
                        cast(int, parent["/Count"]) - 1
                    )
                if len(cast(ArrayObject, parent["/Kids"])) == 0:
                    # No more objects in this part of this subtree
                    ind = parent.indirect_reference
                parent = parent.get("/Parent", None)
            except ValueError:  # from index
                if first:
                    raise PdfReadError(f"Page not found in page tree: {ind}")
                break

    def __iter__(self) -> Iterator[PageObject]:
        for i in range(len(self)):
            yield self[i]

    def __str__(self) -> str:
        p = [f"PageObject({i})" for i in range(self.length_function())]
        return f"[{', '.join(p)}]"


def _get_fonts_walk(
    obj: DictionaryObject,
    fnt: set[str],
    emb: set[str],
) -> tuple[set[str], set[str]]:
    """
    Get the set of all fonts and all embedded fonts.

    Args:
        obj: Page resources dictionary
        fnt: font
        emb: embedded fonts

    Returns:
        A tuple (fnt, emb)

    If there is a key called 'BaseFont', that is a font that is used in the document.
    If there is a key called 'FontName' and another key in the same dictionary object
    that is called 'FontFilex' (where x is null, 2, or 3), then that fontname is
    embedded.

    We create and add to two sets, fnt = fonts used and emb = fonts embedded.

    """
    pass

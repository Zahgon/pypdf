# Copyright (c) 2006, Mathieu Fenniak
# Copyright (c) 2007, Ashish Kulkarni <kulkarni.ashish@gmail.com>
# Copyright (c) 2024, Pubpub-ZZ
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

import struct
from abc import abstractmethod
from collections.abc import Generator, Iterable, Iterator, Mapping
from datetime import datetime
from typing import (
    Any,
    Optional,
    Union,
    cast,
)

from ._encryption import Encryption
from ._page import PageObject, _VirtualList
from ._page_labels import index2label as page_index2page_label
from ._utils import (
    deprecation_with_replacement,
    logger_warning,
    parse_iso8824_date,
)
from .constants import CatalogAttributes as CA
from .constants import CatalogDictionary as CD
from .constants import (
    CheckboxRadioButtonAttributes,
    GoToActionArguments,
    PagesAttributes,
    UserAccessPermissions,
)
from .constants import Core as CO
from .constants import DocumentInformationAttributes as DI
from .constants import FieldDictionaryAttributes as FA
from .constants import PageAttributes as PG
from .errors import PdfReadError, PyPdfError
from .filters import _decompress_with_limit
from .generic import (
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    Destination,
    DictionaryObject,
    EncodedStreamObject,
    Field,
    Fit,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    PdfObject,
    TextStringObject,
    TreeObject,
    ViewerPreferences,
    create_string_object,
    is_null_or_none,
)
from .generic._files import EmbeddedFile
from .types import OutlineType, PagemodeType
from .xmp import XmpInformation


def convert_to_int(d: bytes, size: int) -> Union[int, tuple[Any, ...]]:
    if size > 8:
        raise PdfReadError("Invalid size in convert_to_int")
    d = b"\x00\x00\x00\x00\x00\x00\x00\x00" + d
    d = d[-8:]
    return struct.unpack(">q", d)[0]


class DocumentInformation(DictionaryObject):
    """
    A class representing the basic document metadata provided in a PDF File.
    This class is accessible through
    :py:class:`PdfReader.metadata<pypdf.PdfReader.metadata>`.

    All text properties of the document metadata have
    *two* properties, e.g. author and author_raw. The non-raw property will
    always return a ``TextStringObject``, making it ideal for a case where the
    metadata is being displayed. The raw property can sometimes return a
    ``ByteStringObject``, if pypdf was unable to decode the string's text
    encoding; this requires additional safety in the caller and therefore is not
    as commonly accessed.
    """

    def __init__(self) -> None:
        DictionaryObject.__init__(self)

    def _get_text(self, key: str) -> Optional[str]:
        pass

    @property
    def title(self) -> Optional[str]:
        """
        Read-only property accessing the document's title.

        Returns a ``TextStringObject`` or ``None`` if the title is not
        specified.
        """
        pass

    @property
    def title_raw(self) -> Optional[str]:
        """The "raw" version of title; can return a ``ByteStringObject``."""
        pass

    @property
    def author(self) -> Optional[str]:
        """
        Read-only property accessing the document's author.

        Returns a ``TextStringObject`` or ``None`` if the author is not
        specified.
        """
        pass

    @property
    def author_raw(self) -> Optional[str]:
        """The "raw" version of author; can return a ``ByteStringObject``."""
        pass

    @property
    def subject(self) -> Optional[str]:
        """
        Read-only property accessing the document's subject.

        Returns a ``TextStringObject`` or ``None`` if the subject is not
        specified.
        """
        pass

    @property
    def subject_raw(self) -> Optional[str]:
        """The "raw" version of subject; can return a ``ByteStringObject``."""
        pass

    @property
    def creator(self) -> Optional[str]:
        """
        Read-only property accessing the document's creator.

        If the document was converted to PDF from another format, this is the
        name of the application (e.g. OpenOffice) that created the original
        document from which it was converted. Returns a ``TextStringObject`` or
        ``None`` if the creator is not specified.
        """
        pass

    @property
    def creator_raw(self) -> Optional[str]:
        """The "raw" version of creator; can return a ``ByteStringObject``."""
        pass

    @property
    def producer(self) -> Optional[str]:
        """
        Read-only property accessing the document's producer.

        If the document was converted to PDF from another format, this is the
        name of the application (for example, macOS Quartz) that converted it to
        PDF. Returns a ``TextStringObject`` or ``None`` if the producer is not
        specified.
        """
        pass

    @property
    def producer_raw(self) -> Optional[str]:
        """The "raw" version of producer; can return a ``ByteStringObject``."""
        pass

    @property
    def creation_date(self) -> Optional[datetime]:
        """Read-only property accessing the document's creation date."""
        pass

    @property
    def creation_date_raw(self) -> Optional[str]:
        """
        The "raw" version of creation date; can return a ``ByteStringObject``.

        Typically in the format ``D:YYYYMMDDhhmmss[+Z-]hh'mm`` where the suffix
        is the offset from UTC.
        """
        pass

    @property
    def modification_date(self) -> Optional[datetime]:
        """
        Read-only property accessing the document's modification date.

        The date and time the document was most recently modified.
        """
        pass

    @property
    def modification_date_raw(self) -> Optional[str]:
        """
        The "raw" version of modification date; can return a
        ``ByteStringObject``.

        Typically in the format ``D:YYYYMMDDhhmmss[+Z-]hh'mm`` where the suffix
        is the offset from UTC.
        """
        pass

    @property
    def keywords(self) -> Optional[str]:
        """
        Read-only property accessing the document's keywords.

        Returns a ``TextStringObject`` or ``None`` if keywords are not
        specified.
        """
        pass

    @property
    def keywords_raw(self) -> Optional[str]:
        """The "raw" version of keywords; can return a ``ByteStringObject``."""
        pass


class PdfDocCommon:
    """
    Common functions from PdfWriter and PdfReader objects.

    This root class is strongly abstracted.
    """

    strict: bool = False  # default

    flattened_pages: Optional[list[PageObject]] = None

    _encryption: Optional[Encryption] = None

    _readonly: bool = False

    @property
    @abstractmethod
    def root_object(self) -> DictionaryObject:
        ...  # pragma: no cover

    @property
    @abstractmethod
    def pdf_header(self) -> str:
        ...  # pragma: no cover

    @abstractmethod
    def get_object(
        self, indirect_reference: Union[int, IndirectObject]
    ) -> Optional[PdfObject]:
        ...  # pragma: no cover

    @abstractmethod
    def _replace_object(self, indirect: IndirectObject, obj: PdfObject) -> PdfObject:
        ...  # pragma: no cover

    @property
    @abstractmethod
    def _info(self) -> Optional[DictionaryObject]:
        ...  # pragma: no cover

    @property
    def metadata(self) -> Optional[DocumentInformation]:
        """
        Retrieve the PDF file's document information dictionary, if it exists.

        Note that some PDF files use metadata streams instead of document
        information dictionaries, and these metadata streams will not be
        accessed by this function.
        """
        pass

    @property
    def xmp_metadata(self) -> Optional[XmpInformation]:
        ...  # pragma: no cover

    @property
    def viewer_preferences(self) -> Optional[ViewerPreferences]:
        """Returns the existing ViewerPreferences as an overloaded dictionary."""
        pass

    def get_num_pages(self) -> int:
        """
        Calculate the number of pages in this PDF file.

        Returns:
            The number of pages of the parsed PDF file.

        Raises:
            PdfReadError: If restrictions prevent this action.

        """
        pass

    def get_page(self, page_number: int) -> PageObject:
        """
        Retrieve a page by number from this PDF file.
        Most of the time ``.pages[page_number]`` is preferred.

        Args:
            page_number: The page number to retrieve
                (pages begin at zero)

        Returns:
            A :class:`PageObject<pypdf._page.PageObject>` instance.

        """
        pass

    def _get_page_in_node(
        self,
        page_number: int,
    ) -> tuple[DictionaryObject, int]:
        """
        Retrieve the node and position within the /Kids containing the page.
        If page_number is greater than the number of pages, it returns the top node, -1.
        """
        top = cast(DictionaryObject, self.root_object["/Pages"])

        def recursive_call(
            node: DictionaryObject, mi: int
        ) -> tuple[Optional[PdfObject], int]:
            ma = cast(int, node.get("/Count", 1))  # default 1 for /Page types
            if node["/Type"] == "/Page":
                if page_number == mi:
                    return node, -1
                return None, mi + 1
            if (page_number - mi) >= ma:  # not in nodes below
                if node == top:
                    return top, -1
                return None, mi + ma
            for idx, kid in enumerate(cast(ArrayObject, node["/Kids"])):
                kid = cast(DictionaryObject, kid.get_object())
                n, i = recursive_call(kid, mi)
                if n is not None:  # page has just been found ...
                    if i < 0:  # ... just below!
                        return node, idx
                    # ... at lower levels
                    return n, i
                mi = i
            raise PyPdfError("Unexpectedly cannot find the node.")

        node, idx = recursive_call(top, 0)
        assert isinstance(node, DictionaryObject), "mypy"
        return node, idx

    @property
    def named_destinations(self) -> dict[str, Destination]:
        """A read-only dictionary which maps names to destinations."""
        pass

    def get_named_dest_root(self) -> ArrayObject:
        named_dest = ArrayObject()
        if CA.NAMES in self.root_object and isinstance(
            self.root_object[CA.NAMES], DictionaryObject
        ):
            names = cast(DictionaryObject, self.root_object[CA.NAMES])
            if CA.DESTS in names and isinstance(names[CA.DESTS], DictionaryObject):
                # §3.6.3 Name Dictionary (PDF spec 1.7)
                dests = cast(DictionaryObject, names[CA.DESTS])
                dests_ref = dests.indirect_reference
                if CA.NAMES in dests:
                    # §7.9.6, entries in a name tree node dictionary
                    named_dest = cast(ArrayObject, dests[CA.NAMES])
                else:
                    named_dest = ArrayObject()
                    dests[NameObject(CA.NAMES)] = named_dest
            elif hasattr(self, "_add_object"):
                dests = DictionaryObject()
                dests_ref = self._add_object(dests)
                names[NameObject(CA.DESTS)] = dests_ref
                dests[NameObject(CA.NAMES)] = named_dest

        elif hasattr(self, "_add_object"):
            names = DictionaryObject()
            names_ref = self._add_object(names)
            self.root_object[NameObject(CA.NAMES)] = names_ref
            dests = DictionaryObject()
            dests_ref = self._add_object(dests)
            names[NameObject(CA.DESTS)] = dests_ref
            dests[NameObject(CA.NAMES)] = named_dest

        return named_dest

    ## common
    def _get_named_destinations(
        self,
        tree: Union[TreeObject, None] = None,
        retval: Optional[dict[str, Destination]] = None,
    ) -> dict[str, Destination]:
        """
        Retrieve the named destinations present in the document.

        Args:
            tree: The current tree.
            retval: The previously retrieved destinations for nested calls.

        Returns:
            A dictionary which maps names to destinations.

        """
        pass

    # A select group of relevant field attributes. For the complete list,
    # see §12.3.2 of the PDF 1.7 or PDF 2.0 specification.

    def get_fields(
        self,
        tree: Optional[TreeObject] = None,
        retval: Optional[dict[Any, Any]] = None,
        fileobj: Optional[Any] = None,
        stack: Optional[list[PdfObject]] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Extract field data if this PDF contains interactive form fields.

        The *tree*, *retval*, *stack* parameters are for recursive use.

        Args:
            tree: Current object to parse.
            retval: In-progress list of fields.
            fileobj: A file object (usually a text file) to write
                a report to on all interactive form fields found.
            stack: List of already parsed objects.

        Returns:
            A dictionary where each key is a field name, and each
            value is a :class:`Field<pypdf.generic.Field>` object. By
            default, the mapping name is used for keys.
            ``None`` if form data could not be located.

        """
        pass

    def _get_qualified_field_name(self, parent: DictionaryObject) -> str:
        pass

    def _build_field(
        self,
        field: Union[TreeObject, DictionaryObject],
        retval: dict[Any, Any],
        fileobj: Any,
        field_attributes: Any,
        stack: list[PdfObject],
    ) -> None:
        pass

    def _check_kids(
        self,
        tree: Union[TreeObject, DictionaryObject],
        retval: Any,
        fileobj: Any,
        stack: list[PdfObject],
    ) -> None:
        pass

    def _write_field(self, fileobj: Any, field: Any, field_attributes: Any) -> None:
        pass

    def get_form_text_fields(self, full_qualified_name: bool = False) -> dict[str, Any]:
        """
        Retrieve form fields from the document with textual data.

        Args:
            full_qualified_name: to get full name

        Returns:
            A dictionary. The key is the name of the form field,
            the value is the content of the field.

            If the document contains multiple form fields with the same name, the
            second and following will get the suffix .2, .3, ...

        """
        pass

    def get_pages_showing_field(
        self, field: Union[Field, PdfObject, IndirectObject]
    ) -> list[PageObject]:
        """
        Provides list of pages where the field is called.

        Args:
            field: Field Object, PdfObject or IndirectObject referencing a Field

        Returns:
            List of pages:
                - Empty list:
                    The field has no widgets attached
                    (either hidden field or ancestor field).
                - Single page list:
                    Page where the widget is present
                    (most common).
                - Multi-page list:
                    Field with multiple kids widgets
                    (example: radio buttons, field repeated on multiple pages).

        """
        pass

    @property
    def open_destination(
        self,
    ) -> Union[None, Destination, TextStringObject, ByteStringObject]:
        """
        Property to access the opening destination (``/OpenAction`` entry in
        the PDF catalog). It returns ``None`` if the entry does not exist
        or is not set.

        Raises:
            Exception: If a destination is invalid.

        """
        pass

    @open_destination.setter
    def open_destination(self, dest: Union[None, str, Destination, PageObject]) -> None:
        raise NotImplementedError("No setter for open_destination")

    @property
    def outline(self) -> OutlineType:
        """
        Read-only property for the outline present in the document
        (i.e., a collection of 'outline items' which are also known as
        'bookmarks').
        """
        pass

    def _get_outline(
        self,
        node: Optional[DictionaryObject] = None,
        outline: Optional[Any] = None,
        visited: Optional[set[int]] = None,
    ) -> OutlineType:
        pass

    @property
    def threads(self) -> Optional[ArrayObject]:
        """
        Read-only property for the list of threads.

        See §12.4.3 from the PDF 1.7 or 2.0 specification.

        It is an array of dictionaries with "/F" (the first bead in the thread)
        and "/I" (a thread information dictionary containing information about
        the thread, such as its title, author, and creation date) properties or
        None if there are no articles.

        Since PDF 2.0 it can also contain an indirect reference to a metadata
        stream containing information about the thread, such as its title,
        author, and creation date.
        """
        pass

    @abstractmethod
    def _get_page_number_by_indirect(
        self, indirect_reference: Union[None, int, NullObject, IndirectObject]
    ) -> Optional[int]:
        ...  # pragma: no cover

    def get_page_number(self, page: PageObject) -> Optional[int]:
        """
        Retrieve page number of a given PageObject.

        Args:
            page: The page to get page number. Should be
                an instance of :class:`PageObject<pypdf._page.PageObject>`

        Returns:
            The page number or None if page is not found

        """
        pass

    def get_destination_page_number(self, destination: Destination) -> Optional[int]:
        """
        Retrieve page number of a given Destination object.

        Args:
            destination: The destination to get page number.

        Returns:
            The page number or None if page is not found

        """
        pass

    def _build_destination(
        self,
        title: Union[str, bytes],
        array: Optional[
            list[
                Union[NumberObject, IndirectObject, None, NullObject, DictionaryObject]
            ]
        ],
    ) -> Destination:
        page, typ = None, None
        # handle outline items with missing or invalid destination
        if (
            isinstance(array, (NullObject, str))
            or (isinstance(array, ArrayObject) and len(array) == 0)
            or array is None
        ):
            page = NullObject()
            return Destination(title, page, Fit.fit())
        page, typ, *array = array  # type: ignore
        try:
            return Destination(title, page, Fit(fit_type=typ, fit_args=array))  # type: ignore
        except PdfReadError:
            logger_warning(f"Unknown destination: {title!r} {array}", __name__)
            if self.strict:
                raise
            # create a link to first Page
            tmp = self.pages[0].indirect_reference
            indirect_reference = NullObject() if tmp is None else tmp
            return Destination(title, indirect_reference, Fit.fit())

    def _build_outline_item(self, node: DictionaryObject) -> Optional[Destination]:
        dest, title, outline_item = None, None, None

        # title required for valid outline
        # §12.3.3, entries in an outline item dictionary
        try:
            title = cast("str", node["/Title"])
        except KeyError:
            if self.strict:
                raise PdfReadError(f"Outline Entry Missing /Title attribute: {node!r}")
            title = ""

        if "/A" in node:
            # Action, PDF 1.7 and PDF 2.0 §12.6 (only type GoTo supported)
            action = cast(DictionaryObject, node["/A"])
            action_type = cast(NameObject, action[GoToActionArguments.S])
            if action_type == "/GoTo":
                if GoToActionArguments.D in action:
                    dest = action[GoToActionArguments.D]
                elif self.strict:
                    raise PdfReadError(f"Outline Action Missing /D attribute: {node!r}")
        elif "/Dest" in node:
            # Destination, PDF 1.7 and PDF 2.0 §12.3.2
            dest = node["/Dest"]
            # if array was referenced in another object, will be a dict w/ key "/D"
            if isinstance(dest, DictionaryObject) and "/D" in dest:
                dest = dest["/D"]

        if isinstance(dest, ArrayObject):
            outline_item = self._build_destination(title, dest)
        elif isinstance(dest, str):
            # named destination, addresses NameObject Issue #193
            # TODO: Keep named destination instead of replacing it?
            try:
                outline_item = self._build_destination(
                    title, self._named_destinations[dest].dest_array
                )
            except KeyError:
                # named destination not found in Name Dict
                outline_item = self._build_destination(title, None)
        elif dest is None:
            # outline item not required to have destination or action
            # PDFv1.7 Table 153
            outline_item = self._build_destination(title, dest)
        else:
            if self.strict:
                raise PdfReadError(f"Unexpected destination {dest!r}")
            logger_warning(
                f"Removed unexpected destination {dest!r} from destination",
                __name__,
            )
            outline_item = self._build_destination(title, None)

        # if outline item created, add color, format, and child count if present
        if outline_item:
            if "/C" in node:
                # Color of outline item font in (R, G, B) with values ranging 0.0-1.0
                outline_item[NameObject("/C")] = ArrayObject(FloatObject(c) for c in node["/C"])  # type: ignore
            if "/F" in node:
                # specifies style characteristics bold and/or italic
                # with 1=italic, 2=bold, 3=both
                outline_item[NameObject("/F")] = node["/F"]
            if "/Count" in node:
                # absolute value = num. visible children
                # with positive = open/unfolded, negative = closed/folded
                outline_item[NameObject("/Count")] = node["/Count"]
            #  if count is 0 we will consider it as open (to have available is_open)
            outline_item[NameObject("/%is_open%")] = BooleanObject(
                node.get("/Count", 0) >= 0
            )
        outline_item.node = node
        try:
            outline_item.indirect_reference = node.indirect_reference
        except AttributeError:
            pass
        return outline_item

    @property
    def pages(self) -> list[PageObject]:
        """
        Property that emulates a list of :class:`PageObject<pypdf._page.PageObject>`.
        This property allows to get a page or a range of pages.

        Note:
            For PdfWriter only: Provides the capability to remove a page/range of
            page from the list (using the del operator). Remember: Only the page
            entry is removed, as the objects beneath can be used elsewhere. A
            solution to completely remove them - if they are not used anywhere - is
            to write to a buffer/temporary file and then load it into a new
            PdfWriter.

        """
        pass

    @property
    def page_labels(self) -> list[str]:
        """
        A list of labels for the pages in this document.

        This property is read-only. The labels are in the order that the pages
        appear in the document.
        """
        pass

    @property
    def page_layout(self) -> Optional[str]:
        """
        Get the page layout currently being used.

        .. list-table:: Valid ``layout`` values
           :widths: 50 200

           * - /NoLayout
             - Layout explicitly not specified
           * - /SinglePage
             - Show one page at a time
           * - /OneColumn
             - Show one column at a time
           * - /TwoColumnLeft
             - Show pages in two columns, odd-numbered pages on the left
           * - /TwoColumnRight
             - Show pages in two columns, odd-numbered pages on the right
           * - /TwoPageLeft
             - Show two pages at a time, odd-numbered pages on the left
           * - /TwoPageRight
             - Show two pages at a time, odd-numbered pages on the right
        """
        pass

    @property
    def page_mode(self) -> Optional[PagemodeType]:
        """
        Get the page mode currently being used.

        .. list-table:: Valid ``mode`` values
           :widths: 50 200

           * - /UseNone
             - Do not show outline or thumbnails panels
           * - /UseOutlines
             - Show outline (aka bookmarks) panel
           * - /UseThumbs
             - Show page thumbnails panel
           * - /FullScreen
             - Fullscreen view
           * - /UseOC
             - Show Optional Content Group (OCG) panel
           * - /UseAttachments
             - Show attachments panel
        """
        pass

    def _flatten(
        self,
        list_only: bool = False,
        pages: Union[None, DictionaryObject, PageObject] = None,
        inherit: Optional[dict[str, Any]] = None,
        indirect_reference: Optional[IndirectObject] = None,
    ) -> None:
        """
        Process the document pages to ease searching.

        Attributes of a page may inherit from ancestor nodes
        in the page tree. Flattening means moving
        any inheritance data into descendant nodes,
        effectively removing the inheritance dependency.

        Note: It is distinct from another use of "flattening" applied to PDFs.
        Flattening a PDF also means combining all the contents into one single layer
        and making the file less editable.

        Args:
            list_only: Will only list the pages within _flatten_pages.
            pages:
            inherit:
            indirect_reference: Used recursively to flatten the /Pages object.

        """
        pass

    def remove_page(
        self,
        page: Union[int, PageObject, IndirectObject],
        clean: bool = False,
    ) -> None:
        """
        Remove page from pages list.

        Args:
            page:
                * :class:`int`: Page number to be removed.
                * :class:`~pypdf._page.PageObject`: page to be removed. If the page appears many times
                  only the first one will be removed.
                * :class:`~pypdf.generic.IndirectObject`: Reference to page to be removed.

            clean: replace PageObject with NullObject to prevent annotations
                or destinations to reference a detached page.

        """
        pass

    def _get_indirect_object(self, num: int, gen: int) -> Optional[PdfObject]:
        """
        Used to ease development.

        This is equivalent to generic.IndirectObject(num,gen,self).get_object()

        Args:
            num: The object number of the indirect object.
            gen: The generation number of the indirect object.

        Returns:
            A PdfObject

        """
        pass

    def decode_permissions(
        self, permissions_code: int
    ) -> dict[str, bool]:  # pragma: no cover
        """Take the permissions as an integer, return the allowed access."""
        pass

    @property
    def user_access_permissions(self) -> Optional[UserAccessPermissions]:
        """
        Get the user access permissions for encrypted documents.
        Returns None if not encrypted.

        .. warning::

            For AES-256 encrypted documents (R=5/R=6), the returned
            permissions are derived from the ``/P`` field, which is
            only trustworthy if the ``/Perms`` integrity check passed.
            Check :attr:`are_permissions_valid` to verify.
        """
        pass

    @property
    def are_permissions_valid(self) -> Optional[bool]:
        """
        Whether the ``/Perms`` integrity check passed for this document.

        For AES-256 encrypted documents (R=5/R=6), the ``/Perms`` field
        is an encrypted copy of the permissions that can be verified
        independently. Returns ``False`` if this check fails (the ``/P``
        permissions may have been tampered with).

        Returns ``None`` if the document is not encrypted or has not yet
        been decrypted via :meth:`decrypt()<pypdf.PdfReader.decrypt>`.
        Returns ``True`` for non-AES-256 encryption (no ``/Perms`` to check).
        """
        pass

    @property
    @abstractmethod
    def is_encrypted(self) -> bool:
        """
        Read-only boolean property showing whether this PDF file is encrypted.

        Note that this property, if true, will remain true even after the
        :meth:`decrypt()<pypdf.PdfReader.decrypt>` method is called.
        """
        ...  # pragma: no cover

    @property
    def xfa(self) -> Optional[dict[str, Any]]:
        pass

    @property
    def attachments(self) -> Mapping[str, list[bytes]]:
        """Mapping of attachment filenames to their content."""
        pass

    @property
    def attachment_list(self) -> Generator[EmbeddedFile, None, None]:
        """Iterable of attachment objects."""
        pass

    def _list_attachments(self) -> list[str]:
        """
        Retrieves the list of filenames of file attachments.

        Returns:
            list of filenames

        """
        pass

    def _get_attachment_list(self, name: str) -> list[bytes]:
        pass

    def _get_attachments(
        self, filename: Optional[str] = None
    ) -> dict[str, Union[bytes, list[bytes]]]:
        """
        Retrieves all or selected file attachments of the PDF as a dictionary of file names
        and the file data as a bytestring.

        Args:
            filename: If filename is None, then a dictionary of all attachments
                will be returned, where the key is the filename and the value
                is the content. Otherwise, a dictionary with just a single key
                - the filename - and its content will be returned.

        Returns:
            dictionary of filename -> Union[bytestring or List[ByteString]]
            If the filename exists multiple times a list of the different versions will be provided.

        """
        pass

    @abstractmethod
    def _repr_mimebundle_(
        self,
        include: Union[None, Iterable[str]] = None,
        exclude: Union[None, Iterable[str]] = None,
    ) -> dict[str, Any]:
        """
        Integration into Jupyter Notebooks.

        This method returns a dictionary that maps a mime-type to its
        representation.

        .. seealso::

            https://ipython.readthedocs.io/en/stable/config/integrating.html
        """
        ...  # pragma: no cover


class LazyDict(Mapping[Any, Any]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._raw_dict = dict(*args, **kwargs)

    def __getitem__(self, key: str) -> Any:
        func, arg = self._raw_dict.__getitem__(key)
        return func(arg)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._raw_dict)

    def __len__(self) -> int:
        return len(self._raw_dict)

    def __str__(self) -> str:
        return f"LazyDict(keys={list(self.keys())})"

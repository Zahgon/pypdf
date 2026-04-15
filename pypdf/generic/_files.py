from __future__ import annotations

import bisect
from functools import cached_property
from typing import TYPE_CHECKING, cast

from pypdf._utils import format_iso8824_date, parse_iso8824_date
from pypdf.constants import CatalogAttributes as CA
from pypdf.constants import FileSpecificationDictionaryEntries
from pypdf.constants import PageAttributes as PG
from pypdf.errors import PdfReadError, PyPdfError
from pypdf.generic import (
    ArrayObject,
    ByteStringObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NullObject,
    NumberObject,
    StreamObject,
    TextStringObject,
    is_null_or_none,
)

if TYPE_CHECKING:
    import datetime
    from collections.abc import Generator

    from pypdf._writer import PdfWriter


class EmbeddedFile:
    """
    Container holding the information on an embedded file.

    Attributes are evaluated lazily if possible.

    Further information on embedded files can be found in section 7.11 of the PDF 2.0 specification.
    """
    def __init__(self, name: str, pdf_object: DictionaryObject, parent: ArrayObject | None = None) -> None:
        """
        Args:
            name: The (primary) name as provided in the name tree.
            pdf_object: The corresponding PDF object to allow retrieving further data.
            parent: The parent list.
        """
        self._name = name
        self.pdf_object = pdf_object
        self._parent = parent

    @property
    def name(self) -> str:
        """The (primary) name of the embedded file as provided in the name tree."""
        pass

    @classmethod
    def _create_new(cls, writer: PdfWriter, name: str, content: str | bytes) -> EmbeddedFile:
        """
        Create a new embedded file and add it to the PdfWriter.

        Args:
            writer: The PdfWriter instance to add the embedded file to.
            name: The filename to display.
            content: The data in the file.

        Returns:
            EmbeddedFile instance for the newly created embedded file.
        """
        pass

    @classmethod
    def _get_names_array(cls, writer: PdfWriter) -> ArrayObject:
        """Get the names array for embedded files, possibly creating and flattening it."""
        pass

    @classmethod
    def _get_insertion_index(cls, names_array: ArrayObject, name: str) -> int:
        pass

    @property
    def alternative_name(self) -> str | None:
        """Retrieve the alternative name (file specification)."""
        pass

    @alternative_name.setter
    def alternative_name(self, value: TextStringObject | None) -> None:
        """Set the alternative name (file specification)."""
        pass

    @property
    def description(self) -> str | None:
        """Retrieve the description."""
        pass

    @description.setter
    def description(self, value: TextStringObject | None) -> None:
        """Set the description."""
        pass

    @property
    def associated_file_relationship(self) -> str:
        """Retrieve the relationship of the referring document to this embedded file."""
        pass

    @associated_file_relationship.setter
    def associated_file_relationship(self, value: NameObject) -> None:
        """Set the relationship of the referring document to this embedded file."""
        pass

    @property
    def _embedded_file(self) -> StreamObject:
        """Retrieve the actual embedded file stream."""
        pass

    @property
    def _params(self) -> DictionaryObject:
        """Retrieve the file-specific parameters."""
        pass

    @cached_property
    def _ensure_params(self) -> DictionaryObject:
        """Ensure the /Params dictionary exists and return it."""
        pass

    @property
    def subtype(self) -> str | None:
        """Retrieve the subtype. This is a MIME media type, prefixed by a slash."""
        pass

    @subtype.setter
    def subtype(self, value: NameObject | None) -> None:
        """Set the subtype. This should be a MIME media type, prefixed by a slash."""
        pass

    @property
    def content(self) -> bytes:
        """Retrieve the actual file content."""
        pass

    @content.setter
    def content(self, value: str | bytes) -> None:
        """Set the file content."""
        pass

    @property
    def size(self) -> int | None:
        """Retrieve the size of the uncompressed file in bytes."""
        pass

    @size.setter
    def size(self, value: NumberObject | None) -> None:
        """Set the size of the uncompressed file in bytes."""
        pass

    @property
    def creation_date(self) -> datetime.datetime | None:
        """Retrieve the file creation datetime."""
        pass

    @creation_date.setter
    def creation_date(self, value: datetime.datetime | None) -> None:
        """Set the file creation datetime."""
        pass

    @property
    def modification_date(self) -> datetime.datetime | None:
        """Retrieve the datetime of the last file modification."""
        pass

    @modification_date.setter
    def modification_date(self, value: datetime.datetime | None) -> None:
        """Set the datetime of the last file modification."""
        pass

    @property
    def checksum(self) -> bytes | None:
        """Retrieve the MD5 checksum of the (uncompressed) file."""
        pass

    @checksum.setter
    def checksum(self, value: ByteStringObject | None) -> None:
        """Set the MD5 checksum of the (uncompressed) file."""
        pass

    def delete(self) -> None:
        """Delete the file from the document."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"

    @classmethod
    def _load_from_names(cls, names: ArrayObject) -> Generator[EmbeddedFile]:
        """
        Convert the given name tree into class instances.

        Args:
            names: The name tree to load the data from.

        Returns:
            Iterable of class instances for the files found.
        """
        pass

    @classmethod
    def _load(cls, catalog: DictionaryObject) -> Generator[EmbeddedFile]:
        """
        Load the embedded files for the given document catalog.

        This method and its signature are considered internal API and thus not exposed publicly for now.

        Args:
            catalog: The document catalog to load from.

        Returns:
            Iterable of class instances for the files found.
        """
        pass

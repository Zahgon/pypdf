"""
Anything related to Extensible Metadata Platform (XMP) metadata.

https://en.wikipedia.org/wiki/Extensible_Metadata_Platform
"""

import datetime
import decimal
import re
from collections.abc import Iterator
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
)
from xml.dom.expatbuilder import ExpatBuilderNS
from xml.dom.minidom import Document
from xml.dom.minidom import Element as XmlElement
from xml.parsers.expat import ExpatError, XMLParserType

from ._protocols import XmpInformationProtocol
from ._utils import StreamType, deprecate_with_replacement, deprecation_no_replacement
from .errors import PdfReadError, XmpDocumentError
from .generic import ContentStream, PdfObject

RDF_NAMESPACE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
XMP_NAMESPACE = "http://ns.adobe.com/xap/1.0/"
PDF_NAMESPACE = "http://ns.adobe.com/pdf/1.3/"
XMPMM_NAMESPACE = "http://ns.adobe.com/xap/1.0/mm/"

# What is the PDFX namespace, you might ask?
# It's documented here: https://github.com/adobe/xmp-docs/raw/master/XMPSpecifications/XMPSpecificationPart3.pdf
# This namespace is used to place "custom metadata"
# properties, which are arbitrary metadata properties with no semantic or
# documented meaning.
#
# Elements in the namespace are key/value-style storage,
# where the element name is the key and the content is the value. The keys
# are transformed into valid XML identifiers by substituting an invalid
# identifier character with \u2182 followed by the unicode hex ID of the
# original character. A key like "my car" is therefore "my\u21820020car".
#
# \u2182 is the unicode character \u{ROMAN NUMERAL TEN THOUSAND}
#
# The pdfx namespace should be avoided.
# A custom data schema and sensical XML elements could be used instead, as is
# suggested by Adobe's own documentation on XMP under "Extensibility of
# Schemas".
PDFX_NAMESPACE = "http://ns.adobe.com/pdfx/1.3/"

# PDF/A
PDFAID_NAMESPACE = "http://www.aiim.org/pdfa/ns/id/"

# Internal mapping of namespace URI → prefix
_NAMESPACE_PREFIX_MAP = {
    DC_NAMESPACE: "dc",
    XMP_NAMESPACE: "xmp",
    PDF_NAMESPACE: "pdf",
    XMPMM_NAMESPACE: "xmpMM",
    PDFAID_NAMESPACE: "pdfaid",
    PDFX_NAMESPACE: "pdfx",
}

iso8601 = re.compile(
    """
        (?P<year>[0-9]{4})
        (-
            (?P<month>[0-9]{2})
            (-
                (?P<day>[0-9]+)
                (T
                    (?P<hour>[0-9]{2}):
                    (?P<minute>[0-9]{2})
                    (:(?P<second>[0-9]{2}(.[0-9]+)?))?
                    (?P<tzd>Z|[-+][0-9]{2}:[0-9]{2})
                )?
            )?
        )?
        """,
    re.VERBOSE,
)


K = TypeVar("K")

# Minimal XMP template
_MINIMAL_XMP = f"""<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="pypdf">
    <rdf:RDF xmlns:rdf="{RDF_NAMESPACE}">
        <rdf:Description rdf:about=""
            xmlns:dc="{DC_NAMESPACE}"
            xmlns:xmp="{XMP_NAMESPACE}"
            xmlns:pdf="{PDF_NAMESPACE}"
            xmlns:xmpMM="{XMPMM_NAMESPACE}"
            xmlns:pdfaid="{PDFAID_NAMESPACE}"
            xmlns:pdfx="{PDFX_NAMESPACE}">
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>
<?xpacket end="r"?>"""


def _identity(value: K) -> K:
    pass


def _converter_date(value: str) -> datetime.datetime:
    pass


def _format_datetime_utc(value: datetime.datetime) -> str:
    """Format a datetime as UTC with trailing 'Z'.

    - If the input is timezone-aware, convert to UTC first.
    - If naive, assume UTC.
    """
    pass


def _generic_get(
        element: XmlElement, self: "XmpInformation", list_type: str, converter: Callable[[Any], Any] = _identity
) -> Optional[list[str]]:
    pass


class _XmpBuilder(ExpatBuilderNS):
    """
    Custom XML parser denying all entity declarations.

    This is a stripped down and typed version inspired by what *defusedxml* does.

    Why do we need this? The default limits of *libexpat* used by Python only block exponential entity expansion,
    but not cases like quadratic entity expansion which can still cause quite some memory usage.
    """

    def custom_entity_declaration_handler(
            self,
            entity_name: str,
            is_parameter_entity: bool,
            value: Optional[str],
            base: Optional[str],
            system_id: str,
            public_id: Optional[str],
            notation_name: Optional[str],
    ) -> None:
        raise ExpatError(f"Forbidden entities: {entity_name!r}")

    def install(self, parser: XMLParserType) -> None:
        pass


class XmpInformation(XmpInformationProtocol, PdfObject):
    """
    An object that represents Extensible Metadata Platform (XMP) metadata.
    Usually accessed by :py:attr:`xmp_metadata()<pypdf.PdfReader.xmp_metadata>`.

    Raises:
      PdfReadError: if XML is invalid

    """

    def __init__(self, stream: ContentStream) -> None:
        self.stream = stream
        try:
            data = self.stream.get_data()
            doc_root: Document = _XmpBuilder().parseString(data)
        except (AttributeError, ExpatError) as e:
            raise PdfReadError(f"XML in XmpInformation was invalid: {e}")
        self.rdf_root: XmlElement = doc_root.getElementsByTagNameNS(
            RDF_NAMESPACE, "RDF"
        )[0]
        self.cache: dict[Any, Any] = {}

    @classmethod
    def create(cls) -> "XmpInformation":
        """
        Create a new XmpInformation object with minimal structure.

        Returns:
            A new XmpInformation instance with empty metadata fields.
        """
        pass

    def write_to_stream(
        self, stream: StreamType, encryption_key: Union[None, str, bytes] = None
    ) -> None:
        deprecate_with_replacement(
            "XmpInformation.write_to_stream",
            "PdfWriter.xmp_metadata",
            "6.0.0"
        )
        if encryption_key is not None:  # deprecated
            deprecation_no_replacement(
                "the encryption_key parameter of write_to_stream", "5.0.0"
            )
        self.stream.write_to_stream(stream)

    def get_element(self, about_uri: str, namespace: str, name: str) -> Iterator[Any]:
        pass

    def get_nodes_in_namespace(self, about_uri: str, namespace: str) -> Iterator[Any]:
        pass

    def _get_text(self, element: XmlElement) -> str:
        pass

    def _get_single_value(
        self,
        namespace: str,
        name: str,
        converter: Callable[[str], Any] = _identity,
    ) -> Optional[Any]:
        pass

    def _getter_bag(self, namespace: str, name: str) -> Optional[list[str]]:
        pass

    def _get_seq_values(
        self,
        namespace: str,
        name: str,
        converter: Callable[[Any], Any] = _identity,
    ) -> Optional[list[Any]]:
        pass

    def _get_langalt_values(self, namespace: str, name: str) -> Optional[dict[Any, Any]]:
        pass

    @property
    def dc_contributor(self) -> Optional[list[str]]:
        """Contributors to the resource (other than the authors)."""
        pass

    @dc_contributor.setter
    def dc_contributor(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def dc_coverage(self) -> Optional[str]:
        """Text describing the extent or scope of the resource."""
        pass

    @dc_coverage.setter
    def dc_coverage(self, value: Optional[str]) -> None:
        pass

    @property
    def dc_creator(self) -> Optional[list[str]]:
        """A sorted array of names of the authors of the resource, listed in order of precedence."""
        pass

    @dc_creator.setter
    def dc_creator(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def dc_date(self) -> Optional[list[datetime.datetime]]:
        """A sorted array of dates of significance to the resource. The dates and times are in UTC."""
        pass

    @dc_date.setter
    def dc_date(self, values: Optional[list[Union[str, datetime.datetime]]]) -> None:
        pass

    @property
    def dc_description(self) -> Optional[dict[str, str]]:
        """A language-keyed dictionary of textual descriptions of the content of the resource."""
        pass

    @dc_description.setter
    def dc_description(self, values: Optional[dict[str, str]]) -> None:
        pass

    @property
    def dc_format(self) -> Optional[str]:
        """The mime-type of the resource."""
        pass

    @dc_format.setter
    def dc_format(self, value: Optional[str]) -> None:
        pass

    @property
    def dc_identifier(self) -> Optional[str]:
        """Unique identifier of the resource."""
        pass

    @dc_identifier.setter
    def dc_identifier(self, value: Optional[str]) -> None:
        pass

    @property
    def dc_language(self) -> Optional[list[str]]:
        """An unordered array specifying the languages used in the resource."""
        pass

    @dc_language.setter
    def dc_language(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def dc_publisher(self) -> Optional[list[str]]:
        """An unordered array of publisher names."""
        pass

    @dc_publisher.setter
    def dc_publisher(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def dc_relation(self) -> Optional[list[str]]:
        """An unordered array of text descriptions of relationships to other documents."""
        pass

    @dc_relation.setter
    def dc_relation(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def dc_rights(self) -> Optional[dict[str, str]]:
        """A language-keyed dictionary of textual descriptions of the rights the user has to this resource."""
        pass

    @dc_rights.setter
    def dc_rights(self, values: Optional[dict[str, str]]) -> None:
        pass

    @property
    def dc_source(self) -> Optional[str]:
        """Unique identifier of the work from which this resource was derived."""
        pass

    @dc_source.setter
    def dc_source(self, value: Optional[str]) -> None:
        pass

    @property
    def dc_subject(self) -> Optional[list[str]]:
        """An unordered array of descriptive phrases or keywords that specify the topic of the content."""
        pass

    @dc_subject.setter
    def dc_subject(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def dc_title(self) -> Optional[dict[str, str]]:
        """A language-keyed dictionary of the title of the resource."""
        pass

    @dc_title.setter
    def dc_title(self, values: Optional[dict[str, str]]) -> None:
        pass

    @property
    def dc_type(self) -> Optional[list[str]]:
        """An unordered array of textual descriptions of the document type."""
        pass

    @dc_type.setter
    def dc_type(self, values: Optional[list[str]]) -> None:
        pass

    @property
    def pdf_keywords(self) -> Optional[str]:
        """An unformatted text string representing document keywords."""
        pass

    @pdf_keywords.setter
    def pdf_keywords(self, value: Optional[str]) -> None:
        pass

    @property
    def pdf_pdfversion(self) -> Optional[str]:
        """The PDF file version, for example 1.0 or 1.3."""
        pass

    @pdf_pdfversion.setter
    def pdf_pdfversion(self, value: Optional[str]) -> None:
        pass

    @property
    def pdf_producer(self) -> Optional[str]:
        """The name of the tool that saved the document as a PDF."""
        pass

    @pdf_producer.setter
    def pdf_producer(self, value: Optional[str]) -> None:
        pass

    @property
    def xmp_create_date(self) -> Optional[datetime.datetime]:
        """The date and time the resource was originally created. Returned as a UTC datetime object."""
        pass

    @xmp_create_date.setter
    def xmp_create_date(self, value: Optional[datetime.datetime]) -> None:
        pass

    @property
    def xmp_modify_date(self) -> Optional[datetime.datetime]:
        """The date and time the resource was last modified. Returned as a UTC datetime object."""
        pass

    @xmp_modify_date.setter
    def xmp_modify_date(self, value: Optional[datetime.datetime]) -> None:
        pass

    @property
    def xmp_metadata_date(self) -> Optional[datetime.datetime]:
        """The date and time that any metadata for this resource was last changed. Returned as a UTC datetime object."""
        pass

    @xmp_metadata_date.setter
    def xmp_metadata_date(self, value: Optional[datetime.datetime]) -> None:
        pass

    @property
    def xmp_creator_tool(self) -> Optional[str]:
        """The name of the first known tool used to create the resource."""
        pass

    @xmp_creator_tool.setter
    def xmp_creator_tool(self, value: Optional[str]) -> None:
        pass

    @property
    def xmpmm_document_id(self) -> Optional[str]:
        """The common identifier for all versions and renditions of this resource."""
        pass

    @xmpmm_document_id.setter
    def xmpmm_document_id(self, value: Optional[str]) -> None:
        pass

    @property
    def xmpmm_instance_id(self) -> Optional[str]:
        """An identifier for a specific incarnation of a document, updated each time a file is saved."""
        pass

    @xmpmm_instance_id.setter
    def xmpmm_instance_id(self, value: Optional[str]) -> None:
        pass

    @property
    def pdfaid_part(self) -> Optional[str]:
        """The part of the PDF/A standard that the document conforms to (e.g., 1, 2, 3)."""
        pass

    @pdfaid_part.setter
    def pdfaid_part(self, value: Optional[str]) -> None:
        pass

    @property
    def pdfaid_conformance(self) -> Optional[str]:
        """The conformance level within the PDF/A standard (e.g., 'A', 'B', 'U')."""
        pass

    @pdfaid_conformance.setter
    def pdfaid_conformance(self, value: Optional[str]) -> None:
        pass

    @property
    def custom_properties(self) -> dict[Any, Any]:
        """
        Retrieve custom metadata properties defined in the undocumented pdfx
        metadata schema.

        Returns:
            A dictionary of key/value items for custom metadata properties.

        """
        pass

    def _get_or_create_description(self, about_uri: str = "") -> XmlElement:
        """Get or create an rdf:Description element with the given about URI."""
        pass

    def _clear_cache_entry(self, namespace: str, name: str) -> None:
        """Remove a cached value for a given namespace/name if present."""
        pass

    def _set_single_value(self, namespace: str, name: str, value: Optional[str]) -> None:
        """Set or remove a single metadata value."""
        pass

    def _set_bag_values(self, namespace: str, name: str, values: Optional[list[str]]) -> None:
        """Set or remove bag values (unordered array)."""
        pass

    def _set_seq_values(self, namespace: str, name: str, values: Optional[list[str]]) -> None:
        """Set or remove sequence values (ordered array)."""
        pass

    def _set_langalt_values(self, namespace: str, name: str, values: Optional[dict[str, str]]) -> None:
        """Set or remove language alternative values."""
        pass

    def _get_namespace_prefix(self, namespace: str) -> str:
        """Get the appropriate namespace prefix for a given namespace URI."""
        pass

    def _update_stream(self) -> None:
        """Update the stream with the current XML content."""
        pass

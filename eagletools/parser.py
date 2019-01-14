from typing import Callable, Dict, NamedTuple, Optional, TYPE_CHECKING, TextIO, Tuple, TypeVar, Union
from xml.etree.ElementTree import ElementTree, Element

if TYPE_CHECKING:
    from xml.etree.ElementTree import parse as parse_xml_et
else:
    from defusedxml.ElementTree import parse as parse_xml_et


T = TypeVar('T')


class LibraryRef(NamedTuple):
    name: str
    urn: str

    def __str__(self) -> str:
        if self.urn:
            return f'{self.name} ({self.urn})'
        return self.name


def _parse_bool(value: str) -> bool:
    if value == 'no':
        return False
    if value == 'yes':
        return True
    raise ValueError(value)


def _parse_library_map(element: Element, query: str) \
        -> Dict[LibraryRef, 'Library']:
    result = {}
    for e in element.iterfind(query):
        lib = Library.from_et(e)
        result[lib.ref] = lib
    return result


def _parse_map(element: Element, query: str, parser: Callable[[Element], T]) \
        -> Dict[str, T]:
    return {e.attrib['name']: parser(e) for e in element.iterfind(query)}


def _text_at(element: Element, query: str, none_ok: bool=True) \
        -> Optional[str]:
    found = element.find(query)
    if found is None:
        if none_ok:
            return None
        raise ValueError('Element not found for query {!r}'.format(query))
    return found.text


class Board:
    @classmethod
    def from_et(cls, element: Element) -> 'Board':
        raise NotImplementedError()


class Technology:
    def __init__(self, name: str, attributes: Dict[str, str]) -> None:
        self.name = name
        self.attributes = attributes

    @classmethod
    def from_et(cls, element: Element) -> 'Technology':
        name = element.attrib['name']
        attributes = _parse_map(element, './attribute',
                                lambda e: e.attrib['value'])
        return cls(name, attributes)


class Variant:
    def __init__(self, name: str, package: Optional[str],
                 technologies: Dict[str, Technology]) -> None:
        self.name = name
        self.package = package
        self.technologies = technologies

    @classmethod
    def from_et(cls, element: Element) -> 'Variant':
        name = element.attrib['name']
        package = element.attrib.get('package')
        techs = _parse_map(element, './technologies/technology',
                           Technology.from_et)
        return cls(name, package, techs)


class Device:
    def __init__(self, name: str, prefix: str, uservalue: bool,
                 description: Optional[str], gates: Dict[str, Element],
                 variants: Dict[str, Variant]) -> None:
        self.name = name
        self.prefix = prefix
        self.uservalue = uservalue
        self.description = description
        self.gates = gates
        self.variants = variants

    @classmethod
    def from_et(cls, element: Element) -> 'Device':
        name = element.attrib['name']
        prefix = element.attrib.get('prefix', '')
        uservalue = _parse_bool(element.attrib.get('uservalue', 'no'))
        description = _text_at(element, './description')
        gates = _parse_map(element, './gates/gate', lambda e: e)
        variants = {}
        for var_elt in element.iterfind('./devices/device'):
            var_name = var_elt.attrib.get('name', '')
            variants[var_name] = Variant.from_et(var_elt)
        return cls(name, prefix, uservalue, description, gates, variants)


class Library:
    def __init__(self, name: Optional[str], urn: str,
                 description: Optional[str],
                 packages: Dict[str, Element],
                 symbols: Dict[str, Element],
                 devices: Dict[str, Device]) -> None:
        self.name = name
        self.urn = urn
        self.description = description
        self.packages = packages
        self.symbols = symbols
        self.devices = devices

    @classmethod
    def from_et(cls, element: Element) -> 'Library':
        # Per DTD, name is only present within board/schematic files
        name = element.attrib.get('name')
        urn = element.attrib.get('urn', '')
        description = _text_at(element, './description')
        packages = _parse_map(element, './packages/package', lambda e: e)
        symbols = _parse_map(element, './symbols/symbol', lambda e: e)
        devices = _parse_map(element, './devicesets/deviceset',
                             Device.from_et)
        return cls(name, urn, description, packages, symbols, devices)

    @property
    def ref(self) -> LibraryRef:
        if self.name is None:
            raise AttributeError("Can't get ref of Library with no name")
        return LibraryRef(self.name, self.urn)


class Part:
    def __init__(self, name: str, library: str, library_urn: str, device: str,
                 variant: str, technology: str, value: Optional[str],
                 attributes: Dict[str, str]) -> None:
        self.name = name
        self.library = library
        self.library_urn = library_urn
        self.device = device
        self.variant = variant
        self.technology = technology
        self.value = value
        self.attributes = attributes

    @classmethod
    def from_et(cls, element: Element) -> 'Part':
        name = element.attrib['name']
        library = element.attrib['library']
        library_urn = element.attrib.get('library_urn', '')
        device = element.attrib['deviceset']
        variant = element.attrib['device']
        technology = element.attrib.get('technology', '')
        value = element.attrib.get('value')
        attributes = _parse_map(element, './attribute',
                                lambda e: e.attrib['value'])
        return cls(name, library, library_urn, device, variant, technology,
                   value, attributes)

    @property
    def library_ref(self) -> LibraryRef:
        return LibraryRef(self.library, self.library_urn)


class Schematic:
    def __init__(self, description: Optional[str],
                 libraries: Dict[LibraryRef, Library],
                 parts: Dict[str, Part]) -> None:
        self.description = description
        self.libraries = libraries
        self.parts = parts

    @classmethod
    def from_et(cls, element: Element) -> 'Schematic':
        description = _text_at(element, './description')
        libraries = _parse_library_map(element, './libraries/library')
        parts = _parse_map(element, './parts/part', Part.from_et)
        return cls(description, libraries, parts)


def load_file(source: TextIO) -> Tuple[str, ElementTree, Element]:
    et = parse_xml_et(source)
    if et.getroot().tag != 'eagle':
        raise ValueError('Not an EAGLE file')
    board = et.find('./drawing/board')
    if board:
        return 'board', et, board
    library = et.find('./drawing/library')
    if library:
        return 'library', et, library
    schematic = et.find('./drawing/schematic')
    if schematic:
        return 'schematic', et, schematic
    raise ValueError('Corrupt or unhandled EAGLE file')


def parse_file(source: TextIO) -> Union[Board, Library, Schematic]:
    type_, et, element = load_file(source)
    if type_ == 'board':
        return Board.from_et(element)
    if type_ == 'library':
        return Library.from_et(element)
    if type_ == 'schematic':
        return Schematic.from_et(element)
    assert False, "load_file returned unknown type"

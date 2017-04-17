from typing import Any, Callable, Dict, Iterable, TYPE_CHECKING, TextIO, TypeVar, Union
from xml.etree.ElementTree import ElementTree, Element

if TYPE_CHECKING:
    from xml.etree.ElementTree import parse as parse_xml_et
else:
    from defusedxml.ElementTree import parse as parse_xml_et


T = TypeVar('T')


def _parse_bool(value: str, none_value: bool=None) -> bool:
    if value == 'no':
        return False
    if value == 'yes':
        return True
    if value is None and none_value is not None:
        return none_value
    raise ValueError(value)


def _parse_map(element: Element, query: str, parser: Callable[[Element], T]) \
        -> Dict[str, T]:
    return {e.attrib['name']: parser(e) for e in element.iterfind(query)}


def _text_at(element: Element, query: str, none_ok: bool=True) -> str:
    found = element.find(query)
    if found is None:
        if none_ok:
            return None
        raise ValueError('Element not found for query {!r}'.format(query))
    return found.text


class Board:
    @classmethod
    def from_et(cls, doc: ElementTree, element: Element) -> 'Board':
        raise NotImplementedError()


class Variant:
    def __init__(self, name: str, package: str,
                 technologies: Dict[str, Element]) -> None:
        self.name = name
        self.package = package
        self.technologies = technologies

    @classmethod
    def from_et(cls, element: Element) -> 'Variant':
        name = element.attrib.get('name')
        package = element.attrib.get('package')
        techs = _parse_map(element, './technologies/technology', lambda e: e)
        return cls(name, package, techs)


class Device:
    def __init__(self, name: str, prefix: str, uservalue: bool,
                 description: str, gates: Dict[str, Element],
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
        prefix = element.attrib.get('prefix')
        uservalue = _parse_bool(element.attrib.get('uservalue'), False)
        description = _text_at(element, './description')
        gates = _parse_map(element, './gates/gate', lambda e: e)
        variants = {}
        for var_elt in element.iterfind('./devices/device'):
            var_name = var_elt.attrib.get('name', '')
            variants[var_name] = Variant.from_et(var_elt)
        return cls(name, prefix, uservalue, description, gates, variants)


class Library:
    def __init__(self, name: str, description: str,
                 packages: Dict[str, Element],
                 symbols: Dict[str, Element],
                 devices: Dict[str, Device]) -> None:
        self.name = name
        self.description = description
        self.packages = packages
        self.symbols = symbols
        self.devices = devices

    @classmethod
    def from_et(cls, doc: ElementTree, element: Element) -> 'Library':
        name = element.attrib.get('name')
        description = _text_at(element, './description')
        packages = _parse_map(element, './packages/package', lambda e: e)
        symbols = _parse_map(element, './symbols/symbol', lambda e: e)
        devices = _parse_map(element, './devicesets/deviceset',
                             Device.from_et)
        return cls(name, description, packages, symbols, devices)


class Schematic:
    @classmethod
    def from_et(cls, doc: ElementTree, element: Element) -> 'Schematic':
        raise NotImplementedError()


def parse_file(source: TextIO) -> Union[Board, Library, Schematic]:
    et = parse_xml_et(source)
    if et.getroot().tag != 'eagle':
        raise ValueError('Not an EAGLE file')
    board = et.find('./drawing/board')
    if board:
        return Board.from_et(et, board)
    library = et.find('./drawing/library')
    if library:
        return Library.from_et(et, library)
    schematic = et.find('./drawing/schematic')
    if schematic:
        return Schematic.from_et(et, schematic)
    raise ValueError('Corrupt or unhandled EAGLE file')

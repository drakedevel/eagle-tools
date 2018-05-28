import click
import os
import re
from tabulate import tabulate
from typing import TextIO, Tuple
from xml.etree.ElementTree import Element, ElementTree, SubElement

from hwpy.value import Value

from .parser import Library, Part, Schematic, load_file, parse_file, _text_at


def _part_sort_key(value: Tuple[str, Part]) -> Tuple[str, int]:
    match = re.fullmatch(r'([A-Z]+)([0-9]+)', value[0])
    if match:
        return match.group(1), int(match.group(2))
    return value[0], 0


def _format_dev(dev: str, var: str=None, tech: str=None) -> str:
    result = dev
    if var is not None:
        if '?' in result:
            result = result.replace('?', var)
        else:
            result = result + var
    if tech is not None:
        if '*' in result:
            result = result.replace('*', tech)
        else:
            result = result + tech
    return result


def _summary(desc: str) -> str:
    lines = [l.strip() for l in desc.split('\n')]
    for line in lines:
        if not line:
            continue
        if line != desc:
            return line + ' ...'
        return line
    return ''


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--output', '-o', type=click.Path(exists=True, file_okay=False),
              default='.', help="Output directory (default current)")
@click.argument('in_f', type=click.File('r'))
def extract(output: str, in_f: TextIO) -> None:
    """Extract libraries from a board or schematic"""
    # Load and validate input file
    type_, et, element = load_file(in_f)
    if type_ not in ('board', 'schematic'):
        raise ValueError("This command requires board or schematic files")
    version = et.getroot().attrib['version']

    # Extract each library
    for lib_elt in element.iterfind('./libraries/library'):
        root = Element('eagle', attrib={'version': version})
        drawing = SubElement(root, 'drawing')
        library = SubElement(drawing, 'library')
        library.extend(lib_elt)

        et = ElementTree(root)
        et.write(os.path.join(output, '{}.lbr'.format(lib_elt.attrib['name'])),
                 encoding='utf-8')


@cli.command(name='list')
@click.argument('in_f', type=click.File('r'))
def cmd_list(in_f: TextIO) -> None:
    """List the contents of a library"""
    parsed = parse_file(in_f)
    if not isinstance(parsed, Library):
        raise NotImplementedError("Only libraries are supported at this time")

    if parsed.name:
        print("Name: {}".format(parsed.name))
    if parsed.description:
        print("Description: {}".format(_summary(parsed.description)))
    print("Packages:")
    for name, pkg in sorted(parsed.packages.items()):
        print("  {}".format(name))
        descr = _text_at(pkg, './description')
        if descr:
            print("    Description: {}".format(_summary(descr)))
    print("Symbols:")
    for name, sym in sorted(parsed.symbols.items()):
        print("  {}".format(name))
        descr = _text_at(sym, './description')
        if descr:
            print("    Description: {}".format(_summary(descr)))
    print("Devices:")
    for dev_name, dev in sorted(parsed.devices.items()):
        print("  {}".format(dev_name))
        if dev.description:
            print("    Description: {}".format(_summary(dev.description)))
        if dev.variants:
            print("    Variants:")
            for var_name, var in sorted(dev.variants.items()):
                print("      {} pkg={}".format(_format_dev(dev_name, var_name),
                                               var.package))
                if var.technologies.keys() != {''}:
                    for tech_name in sorted(var.technologies.keys()):
                        formatted = _format_dev(dev_name, var_name, tech_name)
                        print("        {}".format(formatted))


@cli.command()
@click.option('--format', type=click.Choice(['table', 'machine']),
              default='table', help="Data output format.")
@click.argument('sch_f', type=click.File('r'))
def parts(format: str, sch_f: TextIO) -> None:
    """List used parts/libraries in a schematic"""
    parsed = parse_file(sch_f)
    if not isinstance(parsed, Schematic):
        raise ValueError("This command requires a schematic file")

    data = []
    for name, part in sorted(parsed.parts.items(), key=_part_sort_key):
        tech = parsed.libraries[part.library].devices[part.device].variants[part.variant].technologies[part.technology]
        attrs = tech.attributes.copy()
        attrs.update(part.attributes)
        value = part.value
        if value:
            try:
                value = Value.parse(value).to_str(True)
            except ValueError:
                pass

        data.append((name, part.library, _format_dev(part.device, part.variant,
                                                     part.technology),
                     value or '', attrs.get('MPN', '')))
    if format == 'table':
        print(tabulate(data, headers=['Part', 'Library', 'Device', 'Value', 'MPN']))
    elif format == 'machine':
        for line in data:
            print(' '.join(line))
    else:
        raise ValueError(format)

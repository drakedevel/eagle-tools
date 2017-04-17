import click
from tabulate import tabulate
from typing import TextIO

from .parser import Library, Schematic, parse_file, _text_at


@click.group()
def cli() -> None:
    pass


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


@cli.command()
@click.argument('in_f', type=click.File('r'))
def list(in_f: TextIO) -> None:
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
    for name, part in sorted(parsed.parts.items()):
        data.append((name, part.library, _format_dev(part.device, part.variant,
                                                     part.technology)))
    if format == 'table':
        print(tabulate(data, headers=['Part', 'Library', 'Device']))
    elif format == 'machine':
        for line in data:
            print(' '.join(line))
    else:
        raise ValueError(format)

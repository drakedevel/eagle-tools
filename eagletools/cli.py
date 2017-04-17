import click
from typing import TextIO

from .parser import Library, parse_file, _text_at


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
    """List the contents of a file"""
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

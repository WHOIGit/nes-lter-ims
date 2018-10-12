from jinja2 import Environment, PackageLoader, select_autoescape
from lxml import etree as et

def get_j2_environment(module='neslter.metadata.eml', dir='templates', autoescape='xml'):
    j2_env = Environment(
        loader=PackageLoader(module, dir),
        autoescape=select_autoescape([autoescape])
    )
    j2_env.trim_blocks = True
    return j2_env

def pretty_print_xml(xml, encoding='utf-8'):
    parser = et.XMLParser(remove_blank_text=True)
    tree = et.fromstring(xml, parser) # checks for well-formedness
    return et.tostring(tree, pretty_print=True).decode(encoding)
from jinja2 import Environment, PackageLoader, select_autoescape

def get_j2_environment(module='neslter.metadata.eml', dir='templates', autoescape='xml'):
    j2_env = Environment(
        loader=PackageLoader(module, dir),
        autoescape=select_autoescape([autoescape])
    )
    j2_env.trim_blocks = True
    return j2_env
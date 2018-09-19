import os

from neslter.metadata.eml.units import EmlUnit
from neslter.metadata.eml.attributes import EmlAttribute

attrs = [
    EmlAttribute('distance', unit=EmlUnit('meter')),
    EmlAttribute('concentration', unit=EmlUnit('microMolePerLiter')),
    EmlAttribute('notes', xsd_type='string', definition='any relevant comments'),
    EmlAttribute('latitude', precision=4),
    EmlAttribute('timestamp', xsd_type='date'),
]

TEST_OUTPUT_DIR = './test-output'

try:
    os.makedirs(TEST_OUTPUT_DIR)
except FileExistsError:
    pass

output_path = os.path.join(TEST_OUTPUT_DIR, 'attributes.xml')

with open(output_path,'w') as fout:
    print('<attributeList>', file=fout)
    for attr in attrs:
        print(attr.to_eml(), file=fout)
    print('</attributeList>', file=fout)

from lxml import etree as et

parser = et.XMLParser(remove_blank_text=True)
tree = et.parse(output_path, parser) # checks for well-formedness
with open(output_path,'w') as pretty_out:
    print(et.tostring(tree, pretty_print=True).decode('utf-8'), file=pretty_out)
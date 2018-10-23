import os

from neslter.metadata.eml.units import EmlUnit
from neslter.metadata.eml.attributes import EmlAttribute
from neslter.metadata.eml.utils import pretty_print_xml

attrs = [
    EmlAttribute.real('distance', unit='meter'),
    EmlAttribute.real('concentration', unit='microMolePerLiter'),
    EmlAttribute.string('notes', definition='any relevant comments'),
    EmlAttribute.latitude(precision=4),
    EmlAttribute.date('timestamp'),
]

TEST_OUTPUT_DIR = './test-output'

try:
    os.makedirs(TEST_OUTPUT_DIR)
except FileExistsError:
    pass

alist_xml = '<attributeList>'

for attr in attrs:
    alist_xml += attr.to_eml()

alist_xml += '</attributeList>'

from lxml import etree as et

output_path = os.path.join(TEST_OUTPUT_DIR, 'attributes.xml')

with open(output_path,'w') as pretty_out:
    print(pretty_print_xml(alist_xml), file=pretty_out)

import sys
import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worldsfair.settings")
import django
django.setup()
from plates.models import *


with open('retrained_labels.txt') as infile:
    lines = infile.readlines()

lines = [(l.strip(), re.sub('\d', '', l).strip().title()) for l in lines]

for label, title in lines:
    plate = Plate(label=label, title=title)
    plate.save()

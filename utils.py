import sys
import os
import re
from shutil import copyfile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worldsfair.settings")
import django
django.setup()
from plates.models import *


def import_plates():
    with open('retrained_labels.txt') as infile:
        lines = infile.readlines()

    lines = [(l.strip(), re.sub('\d', '', l).strip().title()) for l in lines]

    for label, title in lines:
        img = 'plates/' + label.replace(' ', '_') + '.png'
        plate = Plate(label=label, title=title)
        plate.save()


def update_images():
    plates = Plate.objects.all()
    for plate in plates:
        plate.image = 'plates/' + plate.label.replace(' ', '_') + '.png'
        plate.save()


def export_bad_images():
    listings = Listing.objects.filter(title__icontains='license') | Listing.objects.filter(title__icontains='spoon')
    for l in listings:
        print(l.title)
        images = l.images()
        for i in images:
            img = i.image
            if 'listing_images/' not in img:
                img = 'listing_images/' + img
            print(img)
            dst = '../worldsfair_training/tf_files/newplates/NOT_PLATES/' + os.path.basename(img)
            copyfile(img, dst)


export_bad_images()
# import_plates()
# update_images()

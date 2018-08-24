from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.safestring import mark_safe

class Plate(models.Model):
    title = models.CharField(max_length=255)
    label = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=255, default='default.jpg')
    lightIntensity = models.FloatField(default=0.8)
    description = models.TextField()


    def images(self):
         return PlateImage.objects.filter(plate=self)

    def listings(self):
         return Listing.objects.filter(plate=self)

    def __str__(self):
        return self.title


class PlateImage(models.Model):
    image = models.CharField(max_length=255)
    plate = models.ForeignKey(Plate, on_delete=models.CASCADE)


class Listing(models.Model):
    LISTINGSOURCES = (('ebay', 'ebay'), ('etsy', 'etsy'))

    title = models.CharField(max_length=255)
    image = models.CharField(max_length=255, default='default.jpg', blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_listed = models.DateTimeField(blank=True, null=True)
    price = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255, blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    listing_source = models.CharField(max_length=255, choices=LISTINGSOURCES)
    listing_url = models.CharField(max_length=255, blank=True, null=True)
    original_id = models.CharField(max_length=255, unique=True, default=0)
    original_listing = JSONField()
    confirmed = models.BooleanField(default=False)
    duplicate = models.BooleanField(default=False)
    not_a_plate = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)

    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, blank=True, null=True)

    def image_url(self):
        if self.image is None:
            return ''
        return self.image.replace('listing_images/', '')

    def images(self):
         return ListingImage.objects.filter(listing=self)

    def image_tag(self):
        return mark_safe('<img src="/static/%s" width="150"/>' % (self.image_url()))

    image_tag.short_description = 'Image'

    def __str__(self):
        return self.title


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    image = models.CharField(max_length=255, null=True, blank=True)

from django.db import models
from django.contrib.postgres.fields import JSONField

class Plate(models.Model):
    title = models.CharField(max_length=255)
    image = models.CharField(max_length=255, default='default.jpg')
    description = models.TextField()


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
    listing_source = models.CharField(max_length=255, choices=LISTINGSOURCES)
    listing_url = models.CharField(max_length=255, blank=True, null=True)
    original_id = models.CharField(max_length=255, unique=True, default=0)
    original_listing = JSONField()
    confirmed = models.BooleanField(default=False)

    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, blank=True, null=True)

    def image_url(self):
        if self.image is None:
            return ''
        return self.image.replace('listing_images/', '')


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    image = models.CharField(max_length=255, null=True, blank=True)

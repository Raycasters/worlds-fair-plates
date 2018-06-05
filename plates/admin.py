from django.contrib import admin
from django.utils.html import format_html

from .models import Plate, Listing, PlateImage, ListingImage

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'location', 'show_listing_url', 'plate', 'confidence', 'confirmed')

    def show_listing_url(self, obj):
        return format_html('<a href="{url}">{desc}</a>', url=obj.listing_url, desc=obj.original_id)

    show_listing_url.short_description = "Link"

admin.site.register(Listing, ListingAdmin)
admin.site.register(Plate)
admin.site.register(PlateImage)
admin.site.register(ListingImage)

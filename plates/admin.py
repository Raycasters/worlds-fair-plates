from django.contrib import admin
from django.utils.html import format_html

from .models import Plate, Listing, PlateImage, ListingImage

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'location', 'show_listing_url', 'plate', 'confidence', 'confirmed')

    fields = ['title', 'price', 'date_added', 'date_listed', 'location', 'listing_source', 'listing_url', 'plate', 'image_tag', 'confidence', 'confirmed']
    readonly_fields = ['date_added', 'date_listed', 'confidence', 'image_tag']

    def show_listing_url(self, obj):
        return format_html('<a href="{url}">{desc}</a>', url=obj.listing_url, desc=obj.original_id)

    show_listing_url.short_description = "Link"

admin.site.register(Listing, ListingAdmin)
admin.site.register(Plate)
admin.site.register(PlateImage)
admin.site.register(ListingImage)

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Listing, Plate


def index(request):
    return render(request, 'plates/index.html', {})


def manage(request):
    return render(request, 'plates/manage.html', {})


def plate_list(request):
    all_plates = Plate.objects.all()
    all_plates = all_plates.values('id', 'title', 'image', 'description')

    if request.GET.get('listings'):
        for p in all_plates:
            listings = Listing.objects.all().filter(plate_id=p['id'])
            listings = listings.filter(confidence__gt=0.5)
            listings = listings.filter(confirmed=True).order_by('-confidence')
            if request.GET.get('listing_limit'):
                limit = int(request.GET.get('listing_limit'))
                listings = listings[0:limit]
            listings = listings.values('id', 'plate_id', 'title', 'image', 'location', 'lat', 'lng', 'listing_url')
            p['listings'] = list(listings)

    all_plates = sorted(list(all_plates), key=lambda k: len(k.get('listings', [])), reverse=True)

    return JsonResponse(all_plates, safe=False)


def plate_details(request, pk):
    plate = get_object_or_404(Plate, pk=pk)
    output = {
        'id': plate.id, 'title': plate.title, 'description': plate.description, 'image': plate.image
    }
    listings = Listing.objects.all().filter(plate_id=output['id'])
    listings = listings.filter(confidence__gt=0.5)
    listings = listings.filter(confirmed=True).order_by('-confidence')
    if request.GET.get('listing_limit'):
        limit = int(request.GET.get('listing_limit'))
        listings = listings[0:limit]
    listings = listings.values('id', 'title', 'image', 'location', 'lat', 'lng', 'listing_url')
    output['listings'] = list(listings)

    return JsonResponse(output, safe=False)


def listings(request):
    all_listings = Listing.objects.all().exclude(image='default.jpg')

    query = request.GET

    if query.get('plate_id'):
        all_listings = all_listings.filter(plate_id=query.get('plate_id'))

    if query.get('confirmed'):
        all_listings = all_listings.filter(confirmed=True)
        all_listings = all_listings.filter(confidence__gt=0.5)

    if query.get('limit'):
        all_listings = all_listings[0:int(query.get('limit'))]

    if query.get('notplates'):
        all_listings = all_listings.filter(not_a_plate=True)

    all_listings = all_listings.order_by('-confidence')

    all_listings = all_listings.values('id', 'title', 'plate_id', 'listing_source', 'listing_url', 'price', 'date_listed', 'image', 'lat', 'lng')

    return JsonResponse(list(all_listings), safe=False)

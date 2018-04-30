from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Listing


def index(request):
    all_listings = Listing.objects.all().exclude(image='default.jpg')
    paginator = Paginator(all_listings, 100)
    page = request.GET.get('page')
    listings = paginator.get_page(page)

    context = {'listings': listings}

    return render(request, 'plates/index.html', context)

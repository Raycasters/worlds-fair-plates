import sys
import os
import pytz
import json
import datetime
import requests
from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from ebaysdk.exception import ConnectionError
from pprint import pprint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worldsfair.settings")
import django
django.setup()
from plates.models import *

with open('credentials.json', 'r') as infile:
    creds = json.load(infile)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def download_file(url, local_filename=None):
    if local_filename is None:
        local_filename = url.split('/')[-1]

    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return local_filename


def get_ebay_page(query, page=1, entries=200, search_type='findItemsAdvanced'):
    try:
        api = Finding(appid=creds['ebay']['appID'], config_file=None)
        response = api.execute(search_type, {
            'keywords': query,
            'outputSelector': ['PictureURL', 'PictureURLSuperSize'],
            'paginationInput': {
                'entriesPerPage': str(entries),
                'pageNumber': str(page)
            },
        })

        return response.dict()

    except ConnectionError as e:
        print(e)
        return e.response.dict()


def search_ebay(query, search_type='findItemsAdvanced'):
    response = get_ebay_page(query, search_type=search_type)
    total_pages = int(response['paginationOutput']['totalPages'])
    out = response

    print('total pages: ', total_pages)

    page = 2

    while page <= total_pages:
        print('Getting page',  page)
        response = get_ebay_page(query, page, search_type=search_type)
        out['searchResult']['item'] += response['searchResult']['item']
        page += 1


    return out


def search_etsy(query):
    out = []

    url = 'https://openapi.etsy.com/v2/listings/active'

    params = {
        'api_key': creds['etsy']['key'],
        'page': 1,
        'keywords': query
    }

    results = requests.get(url, params=params).json()
    out += results['results']
    page = results['pagination']['next_page']

    while page is not None:
        params['page'] = page
        results = requests.get(url, params=params).json()
        out += results['results']
        page = results['pagination']['next_page']

    return out


def parse_and_save_ebay(listings):
    for listing in listings:
        record = Listing(
            title=listing['title'],
            # date_listed=datetime.datetime.fromtimestamp(listing['creation_tsz'], pytz.UTC),
            date_listed=listing['listingInfo']['startTime'],
            price=float(listing['sellingStatus']['currentPrice']['value']),
            location=listing['location'],
            listing_source='ebay',
            listing_url=listing['viewItemURL'],
            original_id='ebay_' + str(listing['itemId']),
            confirmed=False,
            original_listing=listing
        )
        try:
            record.save()
        except Exception as e:
            print(e)
            continue


def parse_and_save_etsy(listings):
    for listing in listings:
        record = Listing(
            title=listing['title'],
            date_listed=datetime.datetime.fromtimestamp(listing['creation_tsz'], pytz.UTC),
            price=float(listing['price']),
            location='unknown',
            listing_source='etsy',
            listing_url=listing['url'],
            original_id='etsy_' + str(listing['listing_id']),
            confirmed=False,
            original_listing=listing
        )
        try:
            record.save()
        except Exception as e:
            print(e)
            continue


def download_images():
    ebay_ids = []
    etsy_ids = []

    listings = Listing.objects.filter(image='default.jpg')

    for listing in listings:
        service, oid = listing.original_id.split('_')
        if service == 'ebay':
            ebay_ids.append(oid)
        elif service == 'etsy':
            etsy_ids.append(oid)


    for etsy_id in etsy_ids:
        request_url = 'https://openapi.etsy.com/v2/listings/{}/images/?api_key={}'.format(etsy_id, creds['etsy']['key'])
        response = requests.get(request_url).json().get('results', [])
        oid = 'etsy_' + etsy_id
        listing = Listing.objects.get(original_id=oid)
        # print(listing.listing_image_set)
        listing_images = []
        for i, r in enumerate(response):
            basename = '{}_{}.jpg'.format(oid, str(i).zfill(3))
            outname = 'listing_images/' + basename
            print(outname)
            url = r['url_fullxfull']
            download_file(url, outname)
            listing.listingimage_set.create(image=basename)
            listing_images.append(basename)

        # listing.listingimage_set = listing_images
        listing.image = listing_images[0]
        listing.save()


    ebay_api = Shopping(appid=creds['ebay']['appID'], config_file=None)
    for _ebay_ids in chunks(ebay_ids, 20):
        response = ebay_api.execute('GetMultipleItems', {'ItemID': _ebay_ids}).dict()
        for item in response['Item']:
            oid = 'ebay_' + item['ItemID']
            listing = Listing.objects.get(original_id=oid)
            listing_images = []
            urls = item['PictureURL']
            for i, url in enumerate(urls):
                basename = '{}_{}.jpg'.format(oid, str(i).zfill(3))
                outname = 'listing_images/' + basename
                print(url, outname)
                download_file(url, outname)
                listing_images.append(basename)
                listing.listingimage_set.create(image=basename)

            listing.image = listing_images[0]
            listing.save()


if __name__ == '__main__':

    keywords = ["1964 world's fair plate new york"]

    for keyword in keywords:
        results = search_ebay(keyword, 'findItemsAdvanced')['searchResult']['item']
        results += search_ebay(keyword, 'findCompletedItems')['searchResult']['item']
        parse_and_save_ebay(results)
        results = search_etsy(keyword)
        parse_and_save_etsy(results)

    download_images()

    # results = search_ebay(keywords[0], 'findItemsAdvanced')
    # with open('ebay3.json', 'w') as outfile:
    #     json.dump(results, outfile, indent=2)
    #
    # results = search_ebay("World's fair plate", 'findCompletedItems')
    # with open('ebay2.json', 'w') as outfile:
    #     json.dump(results, outfile, indent=2)
    #
    # results = search_etsy("World's fair plate")
    # with open('etsy.json', 'w') as outfile:
    #     json.dump(results, outfile, indent=2)

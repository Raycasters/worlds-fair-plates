import sys
import os
import pytz
import json
import datetime
import time
import requests
import numpy as np
import tensorflow as tf
from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from ebaysdk.exception import ConnectionError
from pprint import pprint
import geocoder
from PIL import Image

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


def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()

    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)

    return graph


def read_tensor_from_image_file(file_name, input_height=299, input_width=299, input_mean=0, input_std=255):

    input_name = "file_reader"
    output_name = "normalized"
    file_reader = tf.read_file(file_name, input_name)
    if file_name.endswith(".png"):
        image_reader = tf.image.decode_png(file_reader, channels=3, name='png_reader')
    elif file_name.endswith(".gif"):
        image_reader = tf.squeeze(tf.image.decode_gif(file_reader, name='gif_reader'))
    elif file_name.endswith(".bmp"):
        image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
    else:
        image_reader = tf.image.decode_jpeg(file_reader, channels = 3, name='jpeg_reader')
    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0);
    resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)

    return result


def load_labels(label_file):
    label = []
    proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
    for l in proto_as_ascii_lines:
        label.append(l.rstrip())
    return label


def test_label(filenames):
    model_file = "retrained_graph.pb"
    label_file = "retrained_labels.txt"
    input_height = 224
    input_width = 224
    input_mean = 128
    input_std = 128
    input_layer = "input"
    output_layer = "final_result"

    labels = load_labels(label_file)
    graph = load_graph(model_file)

    with tf.Session(graph=graph) as sess:
        for file_name in filenames:
            print(file_name)

            t = read_tensor_from_image_file(file_name, input_height=input_height, input_width=input_width, input_mean=input_mean, input_std=input_std)

            input_name = "import/" + input_layer
            output_name = "import/" + output_layer
            input_operation = graph.get_operation_by_name(input_name);
            output_operation = graph.get_operation_by_name(output_name);

            results = sess.run(output_operation.outputs[0], {input_operation.outputs[0]: t})

            results = np.squeeze(results)
            top_k = results.argsort()[-5:][::-1]
            label=labels[top_k[0]]
            confidence = results[top_k[0]]

            print("{} (score={:0.5f})".format(label, confidence))
            for i in top_k:
                print("{} (score={:0.5f})".format(labels[i], results[i]))

            print('--')



def label_images():
    model_file = "retrained_graph.pb"
    label_file = "retrained_labels.txt"
    input_height = 224
    input_width = 224
    input_mean = 128
    input_std = 128
    input_layer = "input"
    output_layer = "final_result"

    labels = load_labels(label_file)
    graph = load_graph(model_file)

    listings = Listing.objects.exclude(image='default.jpg').exclude(image=None).exclude(confirmed=True).exclude(not_a_plate=True).filter(plate=None)

    with tf.Session(graph=graph) as sess:
        for l in listings:
            file_name = 'listing_images/' + l.image
            print(file_name)
            if not os.path.exists(file_name):
                continue

            t = read_tensor_from_image_file(file_name, input_height=input_height, input_width=input_width, input_mean=input_mean, input_std=input_std)

            input_name = "import/" + input_layer
            output_name = "import/" + output_layer
            input_operation = graph.get_operation_by_name(input_name);
            output_operation = graph.get_operation_by_name(output_name);

            results = sess.run(output_operation.outputs[0], {input_operation.outputs[0]: t})

            results = np.squeeze(results)
            top_k = results.argsort()[-5:][::-1]
            label=labels[top_k[0]]
            confidence = results[top_k[0]]

            print("{} (score={:0.5f})".format(label, confidence))
            print('--')

            if label == 'not plates':
                l.not_a_plate = True
                l.confidence = confidence
            else:
                plate = Plate.objects.get(label=label)
                print(plate.title)
                l.plate = plate
                l.confirmed = True
                l.confidence = confidence
                l.save()
            # print(top_k)
            # for i in top_k:
            #     print(template.format(labels[i], results[i]))


def geocode_listings():
    listings = Listing.objects.filter(lat=None).exclude(location='unknown').exclude(plate=None)
    for l in listings:
        try:
            print(l.location)
            g = geocoder.osm(l.location)
            lat, lng = g.latlng
            l.lat = lat
            l.lng = lng
            l.save()
        except Exception as e:
            print(e)


def thumb(img, outname=None, w=200, h=200):
    if outname is None:
        outname = img + '.thumb.jpg'

    if os.path.exists(outname):
        return outname

    image = Image.open(img)
    width, height = image.size

    # Crop as little as possible to square, keeping the center.
    if width > height:
        delta = width - height
        left = int(delta / 2)
        upper = 0
        right = height + left
        lower = height
    else:
        delta = height - width
        left = 0
        upper = int(delta / 2)
        right = width
        lower = width + upper
    image = image.crop((left, upper, right, lower))
    image.thumbnail((w, h))
    image.save(img + '.thumb.jpg')
    return outname


def make_thumbnails():
    listings = Listing.objects.exclude(image='default.jpg')
    for l in listings:
        try:
            thumb('listing_images/' + l.image)
        except Exception as e:
            continue


if __name__ == '__main__':

    # test_label(sys.argv[1:])

    keywords = ["1964 world's fair plate new york", "1964 fair plate -license"]

    for keyword in keywords:
        results = search_ebay(keyword, 'findItemsAdvanced')['searchResult']['item']
        results += search_ebay(keyword, 'findCompletedItems')['searchResult']['item']
        parse_and_save_ebay(results)
        results = search_etsy(keyword)
        parse_and_save_etsy(results)

    print('downloading images')
    download_images()

    print('labeling')
    label_images()

    print('making thumbs')
    make_thumbnails()

    print('geocoding results')
    geocode_listings()

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

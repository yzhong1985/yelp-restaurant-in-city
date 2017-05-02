# -*- coding: utf-8 -*-
"""
Yelp Fusion API code sample.

This program demonstrates the capability of the Yelp Fusion API
by using the Search API to query for businesses by a search term and location,
and the Business API to query additional information about the top result
from the search query.

Please refer to http://www.yelp.com/developers/v3/documentation for the API
documentation.

This program requires the Python requests library, which you can install via:
`pip install -r requirements.txt`.

Sample usage of the program:
`python sample.py --term="bars" --location="San Francisco, CA"`
"""
from __future__ import print_function

import argparse
import json
import pprint
import requests
import sys
import urllib
import csv


# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


# OAuth credential placeholders that must be filled in by users.
# You can find them on
# https://www.yelp.com/developers/v3/manage_app
CLIENT_ID = None
CLIENT_SECRET = None


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'

# Defaults for our simple example.
DEFAULT_TERM = 'delis'
DEFAULT_LOCATION = 'Montclair, CA'
DEFAULT_STATE = 'CA'
DEFAULT_OUTPUT_PATH = 'D:/Projects/yelp-data/{0}.csv'
SEARCH_LIMIT = 50

def obtain_bearer_token(host, path):
    """Given a bearer token, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        str: OAuth bearer token, obtained using client_id and client_secret.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    #assert CLIENT_ID, "Please supply your client_id."
    #assert CLIENT_SECRET, "Please supply your client_secret."
    data = urlencode({
        'client_id': 'XxYjwsOcO48HlQG24BJmdQ',
        'client_secret': '6X1o2Cywg7CESqJYJYzD7a6aEGzRnCAS7G5GvWm18spR11f24oMN7BWVbl9X9BTC',
        'grant_type': GRANT_TYPE,
    })
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    response = requests.request('POST', url, data=data, headers=headers)
    bearer_token = response.json()['access_token']
    return bearer_token

def request(host, path, bearer_token, url_params=None):
    """Given a bearer token, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        bearer_token (str): OAuth bearer token, obtained using client_id and client_secret.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % bearer_token,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()

def search(bearer_token, term, location):
    """Query the Search API by a search term and location.

    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.

    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)

def get_business(bearer_token, business_id):
    """Query the Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, bearer_token)

def query_api(term, location):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)

    response = search(bearer_token, term, location)

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return

    business_id = businesses[0]['id']

    print(u'{0} businesses found, querying business info ' \
        'for the top result "{1}" ...'.format(
            len(businesses), business_id))
    response = get_business(bearer_token, business_id)

    print(u'Result for business "{0}" found:'.format(business_id))
    pprint.pprint(response, indent=2)


def restaurant_query(term, cities):
    """Queries the API by the input values from the user.
        Modified to search for multiple cities
    Args:
        term (str): The search term to query.
        cities (str): The location of the business to query.
    """
    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
    output_path = DEFAULT_OUTPUT_PATH
    # output csv: open a file for writing. Note: use utf-8 encoding to deal with special chars
    rest_data = open(output_path.format(term), 'w', 1, 'utf-8', None, newline='')
    csv_writer = csv.writer(rest_data)
    # write header
    header = ['id', 'name', 'display_phone', 'longitude', 'latitude', 'image_url', 'country', 'address1', 'state',
              'display_address', 'address2', 'address3', 'city', 'zip_code', 'url', 'rating', 'review_count', 'price',
              'tags']
    csv_writer.writerow(header)

    for city in cities:
        city_to_search = city + ', ' + DEFAULT_STATE
        response = search(bearer_token, term, city_to_search)
        businesses = response.get('businesses')

        if not businesses:
            print(u'No businesses for {0} in {1} found.'.format(term, city))
            continue

        print(u'{0} businesses found in {1}, now processing search result'.format(len(businesses), city_to_search))

        for bus in businesses:
            tags = ''
            cats = bus['categories']
            # make tags from yelp api categories alias' values
            for cat in cats:
                tags += cat['alias'] + ','

            tags = tags[:-1]
            # check for two conditions:
            # 1. the business is actually in the selected city.
            # 2. the tags include the given word.
            # if any of the two conditions is not meet, it will not be added to the list
            if bus['location']['city'].strip() != city:
                continue
            if term not in tags:
                continue

            price = ''
            if 'price' in bus:
                price = bus['price']

            row_data = [bus['id'], bus['name'], bus['display_phone'], bus['coordinates']['longitude'], bus['coordinates']['latitude'], bus['image_url'], bus['location']['country'], bus['location']['address1'], bus['location']['state'], bus['location']['display_address'], bus['location']['address2'], bus['location']['address3'], bus['location']['city'], bus['location']['zip_code'], bus['url'], bus['rating'], bus['review_count'], price, tags]
            csv_writer.writerow(row_data)

    # close the file
    rest_data.close()

def restaurant_query(category, terms, cities):
    """Queries the API by the input values from the user.
        Modified to search for multiple cities and output as one single file
    Args:
        category (str): Used for output path
        terms (str): The search term to query.
        cities (str): The location of the business to query.
    """
    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
    output_path = DEFAULT_OUTPUT_PATH
    # output csv: open a file for writing. Note: use utf-8 encoding to deal with special chars
    rest_data = open(output_path.format(category), 'w', 1, 'utf-8', None, newline='')
    csv_writer = csv.writer(rest_data)
    # write header
    header = ['id', 'name', 'display_phone', 'longitude', 'latitude', 'image_url', 'country', 'address1', 'state',
              'display_address', 'address2', 'address3', 'city', 'zip_code', 'url', 'rating', 'review_count', 'price',
              'tags']
    csv_writer.writerow(header)

    for term in terms:

        for city in cities:
            city_to_search = city + ', ' + DEFAULT_STATE
            response = search(bearer_token, term, city_to_search)
            businesses = response.get('businesses')

            if not businesses:
                print(u'No businesses for {0} in {1} found.'.format(term, city))
                continue

            print(u'{0} businesses found in {1}, now processing search result'.format(len(businesses), city_to_search))

            for bus in businesses:
                tags = ''
                cats = bus['categories']
                # make tags from yelp api categories alias' values
                for cat in cats:
                    tags += cat['alias'] + ','

                tags = tags[:-1]
                # check for two conditions:
                # 1. the business is actually in the selected city.
                # 2. the tags include the given word.
                # if any of the two conditions is not meet, it will not be added to the list
                if bus['location']['city'].strip() != city:
                    continue
                if term not in tags:
                    continue

                price = ''
                if 'price' in bus:
                    price = bus['price']

                row_data = [bus['id'], bus['name'], bus['display_phone'], bus['coordinates']['longitude'], bus['coordinates']['latitude'], bus['image_url'], bus['location']['country'], bus['location']['address1'], bus['location']['state'], bus['location']['display_address'], bus['location']['address2'], bus['location']['address3'], bus['location']['city'], bus['location']['zip_code'], bus['url'], bus['rating'], bus['review_count'], price, tags]
                csv_writer.writerow(row_data)

    # close the file
    rest_data.close()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
                        type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-l', '--location', dest='location',
                        default=DEFAULT_LOCATION, type=str,
                        help='Search location (default: %(default)s)')

    input_values = parser.parse_args()

    try:
        # asian type restaurants tags
        # Asian food
        terms = ['chinese', 'asianfusion', 'halal', 'japanese', 'korean', 'mideastern', \
                 'mongolian', 'ramen', 'sushi', 'taiwanese', 'thai', 'vietnamese', 'filipino']
        # American food
        # terms = ['american', 'bars', 'burgers', 'coffee', 'hawaiian', 'pizza']
        # European food
        # terms = ['belgian', 'irish', 'french', 'greek', 'italian', 'mediterranean', 'portuguese', 'modern_european', \
        #         'russian', 'scottish', 'german']
        # Mexican food
        # terms = ['mexican']
        # Others
        # terms = ['vegan', 'delis']
        cities = ['Claremont', 'Ontario', 'Rancho Cucamonga', 'Upland', 'Montclair']
        # for term in terms:
        #    restaurant_query(term, cities)
        restaurant_query('asian', terms, cities)


    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )


if __name__ == '__main__':
    main()

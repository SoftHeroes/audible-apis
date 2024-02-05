import time
import json
import boto3
import audible
import requests
from math import ceil
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from core.marketplaces import Marketplace
from botocore.exceptions import ClientError
from urllib.parse import urlencode, urlunparse, urlparse


s3 = boto3.client('s3',
                  region_name=settings.REGION_NAME)

LOCALE_CODE = 'us'


class CatalogCategories(APIView):

    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''

        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE

        categories_file_path = locale_code+'/' + \
            settings.CATEGORIES_FILE_DIRECTORY+'/'+settings.CATEGORIES_FILE_NAME

        if (not is_file_exists(categories_file_path) or (time.time() - get_file_last_modified(categories_file_path).timestamp()) > settings.CATEGORIES_REFRESH_TIME_IN_SEC):

            auth = getAuthenticator(request.META.get(
                'HTTP_PRIVATE_KEY'), request.META.get('HTTP_ADP_TOKEN'), locale_code)

            with audible.Client(auth=auth) as client:
                api_result = client.get(
                    "1.0/catalog/categories",
                    response_groups="category_metadata"
                )
            data = {'categories': api_result["categories"]}
            update_file_content(categories_file_path,
                                json.dumps(data, ensure_ascii=False))
        else:
            data = json.loads(read_file_content(categories_file_path))

        return JsonResponse(data, safe=False)


class CatalogProducts(APIView):

    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''

        limit = int(request.query_params.get('limit')) if (
            'limit' in request.query_params) else 10
        page = int(request.query_params.get('page')) if (
            'page' in request.query_params) else 1
        exclude_category_ids = request.query_params.get('exclude_category_ids').split(
            ',') if ('exclude_category_ids' in request.query_params) else []
        category_id = request.query_params.get('category_id') if (
            'category_id' in request.query_params) else None

        # Supported Option [products,search]
        resource_type = request.query_params.get('resource_type') if (
            'resource_type' in request.query_params) else 'products'

        # Supported Option [-ReleaseDate, ContentLevel, -Title, AmazonEnglish, AvgRating, BestSellers, -RuntimeLength, ReleaseDate, ProductSiteLaunchDate, -ContentLevel, Title, Relevance, RuntimeLength]
        products_sort_by = request.query_params.get('products_sort_by') if (
            'products_sort_by' in request.query_params) else 'ReleaseDate'

        #  Supported Option [ 20956260011 - Plus Catalog ,21487975011 - free title ] US only
        audible_programs = request.query_params.get('audible_programs') if (
            'audible_programs' in request.query_params) else 'ReleaseDate'

        if (limit > 50 or limit < 1):
            response_data = {
                'error': {
                    'code': 'Request_BadRequest',
                    'message': 'limit must be between 1 to 50'
                }
            }
            return JsonResponse(response_data, status=400)

        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE

        # auth = getAuthenticator(request.META.get(
        #     'HTTP_PRIVATE_KEY'), request.META.get('HTTP_ADP_TOKEN'), locale_code)

        categories_file_path = locale_code+'/' + \
            settings.CATEGORIES_FILE_DIRECTORY+'/'+settings.CATEGORIES_FILE_NAME

        category_ids = get_ids_from_json(
            json.loads(read_file_content(categories_file_path)))

        category_ids = remove_elements(category_ids, exclude_category_ids)

        marketplace = Marketplace.from_country_code(locale_code)

        # Supported Option [contributors, media, price, product_attrs, product_desc, product_extended_attrs, product_plan_details, product_plans, rating, review_attrs, reviews, sample, series, sku]
        response_groups = "contributors, media, price, product_attrs, product_desc, product_extended_attrs,category_ladders,category_ladders"

        if category_id:
            api_result = get_audible_data(
                limit=limit, page=page, response_groups=response_groups, products_sort_by=products_sort_by, category_id=category_id, tld=marketplace.domain, resource_type=resource_type, audible_programs=audible_programs)
        elif True if (len(exclude_category_ids) == 0) else False:
            api_result = get_audible_data(
                limit=limit, page=page, response_groups=response_groups, products_sort_by=products_sort_by, tld=marketplace.domain, resource_type=resource_type, audible_programs=audible_programs)
        else:
            api_result = get_audible_data(
                limit=limit, page=page, response_groups=response_groups, products_sort_by=products_sort_by, disjunctive_category_ids=convert_to_csv(category_ids), tld=marketplace.domain, resource_type=resource_type, audible_programs=audible_programs)

        data = []
        for product in api_result["products"]:
            data.append(
                {
                    'id': product['asin'],
                    "issue_date": product['issue_date'] if 'issue_date' in product else None,
                    "title": product['title'] if 'title' in product else None,
                    "publisher_name": product['publisher_name'] if 'publisher_name' in product else None,
                    "description": product['publisher_summary'] if 'publisher_summary' in product else None,
                    "runtime_length_min": product['runtime_length_min'] if 'runtime_length_min' in product else None,
                    "language": product['language'] if 'language' in product else None,
                    "authors": product['authors'] if 'authors' in product else None,
                    "categories": product['category_ladders'] if 'category_ladders' in product else None,
                    "product_image": product['product_images']['500'] if 'product_images' in product else None,
                    "web_url": "https://www.audible."+marketplace.domain+"/pd/"+product['asin'],
                    "mobile_url": "https://www.audible."+marketplace.domain+"/pd/"+product['asin'],
                }
            )

        if 'total_results' in api_result:
            total_results = int(api_result["total_results"])
        elif 'result_count' in api_result and 'total' in api_result['result_count']:
            total_results = int(api_result['result_count']['total'])
        else:
            total_results = len(data)

        total_pages = ceil(total_results/limit)

        return JsonResponse({'products': data, 'total_results': total_results, 'total_pages': total_pages, 'limit': limit, "page": page}, safe=False)


class GetAllProducts(APIView):
    def get(self, request):

        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE

        products_file_path = locale_code+'/' + \
            settings.PRODUCTS_FILE_DIRECTORY+'/'+settings.PRODUCTS_FILE_NAME

        data = json.loads(read_file_content(products_file_path))

        # Get the exclude_category_ids from the query parameters
        exclude_category_ids = request.GET.get(
            'exclude_category_ids', '').split(',')

        # Filter out products with matching category IDs
        filtered_products = [product for product in data['products'] if not any(
            category['ladder'][0]['id'] in exclude_category_ids for category in product['categories'])]

        # Prepare the response
        response_data = {
            'products': filtered_products,
            'total_results': len(filtered_products),
        }

        return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False}, safe=False)


class ProductDetail(APIView):

    def get(self, request, asin, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''

        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE
        auth = getAuthenticator(request.META.get(
            'HTTP_PRIVATE_KEY'), request.META.get('HTTP_ADP_TOKEN'), locale_code)
        with audible.Client(auth=auth) as client:
            api_result = client.get(
                "/1.0/catalog/products/"+asin,
                response_groups="contributors, media, price, product_attrs, product_desc, product_extended_attrs, product_plan_details, product_plans, rating, sample, sku, series, reviews, relationships, review_attrs, category_ladders, claim_code_url,provided_review,listening_status"
            )

        return JsonResponse(api_result, safe=False)


class StatsAggregates(APIView):

    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''
        param = {}

        if ('daily_listening_interval_duration' in request.query_params):
            param['daily_listening_interval_duration'] = request.query_params.get(
                'daily_listening_interval_duration')
        if ('daily_listening_interval_start_date' in request.query_params):
            param['daily_listening_interval_start_date'] = request.query_params.get(
                'daily_listening_interval_start_date')
        if ('monthly_listening_interval_duration' in request.query_params):
            param['monthly_listening_interval_duration'] = request.query_params.get(
                'monthly_listening_interval_duration')
        if ('monthly_listening_interval_start_date' in request.query_params):
            param['monthly_listening_interval_start_date'] = request.query_params.get(
                'monthly_listening_interval_start_date')

        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE
        auth = getAuthenticator(request.META.get(
            'HTTP_PRIVATE_KEY'), request.META.get('HTTP_ADP_TOKEN'), locale_code)
        with audible.Client(auth=auth) as client:
            api_result = client.get(
                "/1.0/stats/aggregates",
                store='Audible',
                response_groups='total_listening_stats',
                **param
            )

        data = {'aggregated_total_listening_stats': {
            'aggregated_sum': api_result["aggregated_total_listening_stats"]['aggregated_sum'], 'unit': 'Milliseconds'}}
        return JsonResponse(data, safe=False)


class AccountInfo(APIView):

    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''
        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE
        auth = getAuthenticator(request.META.get(
            'HTTP_PRIVATE_KEY'), request.META.get('HTTP_ADP_TOKEN'), locale_code)
        with audible.Client(auth=auth) as client:
            api_result = client.get(
                "/1.0/account/information",
                source=['AmazonEducation', 'AyceRomance', 'Channels', 'AudibleInstitutionsAdmin',
                        'TasteOfAudible', 'Sleep', 'Credit', 'AYCE', 'AudibleInstitutions'],
                response_groups='delinquency_status, customer_benefits, subscription_details_payment_instrument, plan_summary, subscription_details, directed_ids'
            )

        return JsonResponse(api_result, safe=False)


class StatsProducts(APIView):

    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''
        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE
        auth = getAuthenticator(request.META.get(
            'HTTP_PRIVATE_KEY'), request.META.get('HTTP_ADP_TOKEN'), locale_code)
        with audible.Client(auth=auth) as client:
            api_result = client.get(
                "/1.0/stats/status/finished"
            )

        data = []
        for product in api_result["mark_as_finished_status_list"]:

            with audible.Client(auth=auth) as client:
                product_api_result = client.get(
                    "/1.0/catalog/products/"+product['asin'],
                    response_groups="listening_status,product_attrs"
                )

            listening_status = {
                'is_finished': product_api_result['product']['listening_status']['is_finished'],
                'percent_complete': product_api_result['product']['listening_status']['percent_complete'],
                'time_remaining_seconds': product_api_result['product']['listening_status']['time_remaining_seconds'],
                'time_spend_seconds': (product_api_result['product']['runtime_length_min'] * 60) - product_api_result['product']['listening_status']['time_remaining_seconds'],
                'total_runtime_seconds': product_api_result['product']['runtime_length_min'] * 60,
            }

            data.append(
                {
                    "asin": product.get('asin'),
                    "event_timestamp": product['event_timestamp'],
                    "is_marked_as_finished": product['is_marked_as_finished'],
                    "update_date": product['update_date'],
                    "listening_status": listening_status
                }
            )

        return JsonResponse(data, safe=False)


class AddProduct(APIView):

    def get(self, request, asin, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''
        locale_code = request.META.get('HTTP_LOCALE_CODE') if (
            'HTTP_LOCALE_CODE' in request.META) else LOCALE_CODE

        marketplace = Marketplace.from_country_code(locale_code)

        # Supported Option [contributors, media, price, product_attrs, product_desc, product_extended_attrs, product_plan_details, product_plans, rating, review_attrs, reviews, sample, series, sku]
        response_groups = "contributors, media, price, product_attrs, product_desc, product_extended_attrs,category_ladders,category_ladders"

        # Supported Option [-ReleaseDate, ContentLevel, -Title, AmazonEnglish, AvgRating, BestSellers, -RuntimeLength, ReleaseDate, ProductSiteLaunchDate, -ContentLevel, Title, Relevance, RuntimeLength]
        products_sort_by = 'ReleaseDate'

        api_result = get_audible_data(
            response_groups=response_groups, tld=marketplace.domain, product_id=asin, resource_type='products')

        product = api_result['product']
        data = []
        data.append(
            {
                'id': product['asin'],
                "issue_date": product['issue_date'] if 'issue_date' in product else None,
                "title": product['title'] if 'title' in product else None,
                "publisher_name": product['publisher_name'] if 'publisher_name' in product else None,
                "description": product['publisher_summary'] if 'publisher_summary' in product else None,
                "runtime_length_min": product['runtime_length_min'] if 'runtime_length_min' in product else None,
                "language": product['language'] if 'language' in product else None,
                "authors": product['authors'] if 'authors' in product else None,
                "categories": product['category_ladders'] if 'category_ladders' in product else None,
                "product_image": product['product_images']['500'] if 'product_images' in product else None,
                "web_url": "https://www.audible."+marketplace.domain+"/pd/"+product['asin'],
                "mobile_url": "https://www.audible."+marketplace.domain+"/pd/"+product['asin'],
            }
        )

        products_file_path = locale_code+'/' + \
            settings.PRODUCTS_FILE_DIRECTORY+'/'+settings.PRODUCTS_FILE_NAME

        save_to_s3(data[0], products_file_path)

        response_data = {
            'message': {
                'code': 'Request_Successfully',
                'message': 'Product added successfully in S3.'
            }
        }
        return JsonResponse(response_data, status=200)


def getAuthenticator(device_private_key, adp_token, locale_code=LOCALE_CODE):
    auth_dict = {
        'device_private_key': device_private_key.replace("\\n", "\n"),
        'adp_token': adp_token,
        "locale_code": locale_code
    }

    return audible.Authenticator.from_dict(auth_dict)


def write_dict_to_json(dictionary, file_path):
    with open(file_path, 'w') as file:
        json.dump(dictionary, file)


def read_json_to_dict(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


def extract_ids(data_dict):
    ids = []
    categories = data_dict['categories']
    for category in categories:
        children = category['children']
        for child in children:
            ids.append(child['id'])
    return ids


def remove_elements(arr1, arr2):
    arr1 = list(filter(lambda x: x not in arr2, arr1))
    return arr1


def convert_to_csv(arr):
    return ','.join(str(x) for x in arr)


def get_ids_from_json(json_data):
    ids = []

    def process_category(category):
        ids.append(category['id'])
        # if 'children' in category:
        #     for child in category['children']:
        #         process_category(child)

    for category in json_data['categories']:
        process_category(category)

    return ids


def read_file_content(file_path):
    return s3.get_object(Bucket=settings.BUCKET_NAME, Key=file_path)['Body'].read().decode('utf-8')


def is_file_exists(object_key):
    """
    Check if a file exists in an S3 bucket.
    """
    try:
        s3.head_object(Bucket=settings.BUCKET_NAME, Key=object_key)
        return True
    except s3.exceptions.NoSuchKey:
        return False
    except Exception as e:
        return False


def update_file_content(file_key, new_content):

    try:
        s3.put_object(Bucket=settings.BUCKET_NAME,
                      Key=file_key, Body=new_content)
    except Exception as e:
        raise e


def get_file_last_modified(object_key):
    """
    Get the last modified time of an S3 object.
    """
    try:
        response = s3.head_object(
            Bucket=settings.BUCKET_NAME, Key=object_key)
        return response['LastModified']
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_audible_data(limit=10, page=1, response_groups='', products_sort_by=None, category_id=None, disjunctive_category_ids=None, tld='com', product_id=None, resource_type='products', audible_programs=None):
    base_url = f"https://api.audible.{tld}"

    if (product_id):
        endpoint = "1.0/catalog/"+resource_type+"/"+product_id
    else:
        endpoint = "1.0/catalog/"+resource_type

    query_params = {
        "num_results": limit,
        "page": page,
        "response_groups": response_groups,
    }

    products_sort_by_key = 'sort' if resource_type == 'search' else 'products_sort_by'

    if (products_sort_by):
        query_params[products_sort_by_key] = products_sort_by

    if (category_id):
        query_params['category_id'] = category_id

    if (disjunctive_category_ids):
        query_params['disjunctive_category_ids'] = disjunctive_category_ids

    if (audible_programs):
        query_params['audible_programs'] = audible_programs

    encoded_params = urlencode(query_params)
    parsed_base_url = urlparse(base_url)
    full_url = urlunparse(parsed_base_url._replace(
        path=endpoint, query=encoded_params))

    response = requests.get(full_url)

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        return None


def save_to_s3(data, products_file_path):
    new_data = data

    # Check if the JSON file already exists
    if check_exist_or_create_file(products_file_path):
        # Read the existing JSON data

        try:
            existing_data = json_string_to_dict(
                read_file_content(products_file_path))

            # Check if the 'products' key exists in the existing data
            if 'products' in existing_data and isinstance(existing_data['products'], list):
                # Check if the 'id' of the new products already exists in the existing data
                existing_ids = []
                for product in existing_data['products']:
                    existing_ids = set(product['id'])
                # existing_ids = set(product['id'] for product in existing_data['products'])

                if not data['id'] in existing_ids:

                    # Adding new Product
                    existing_data['products'].extend([data])
                    # Save the new data to the JSON file
                    update_file_content(products_file_path,
                                        json.dumps(existing_data, ensure_ascii=False))

        except json.JSONDecodeError as e:
            raise e


def check_exist_or_create_file(file_key):
    try:
        s3.head_object(Bucket=settings.BUCKET_NAME, Key=file_key)

        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                s3.put_object(Bucket=settings.BUCKET_NAME, Key=file_key)
                return True
            except Exception as e:
                raise e
        else:
            raise e


def json_string_to_dict(json_string):
    try:
        json_dict = json.loads(json_string)
        return json_dict
    except json.JSONDecodeError as e:
        raise e

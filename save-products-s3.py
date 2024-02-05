import os
import time
import json
import boto3
import argparse
import requests
import traceback
from datetime import datetime
from botocore.exceptions import ClientError

# Dev Param
limit = 50
page_to_loop = 10
debugging = False
log_folder = "log"
exit_on_error = False

# file details params
products_file_path = None
products_file_name = 'products.json'
products_file_directory = 'products'

categories_file_path = None
categories_file_directory = 'categories'
categories_file_name = 'categories.json'

# aws s3 params
region_name = None
bucket_name = None

# audible param
base_url = None
locale_code = None
resource_type = None
audible_programs = None
products_sort_by = None

# Add a global variable for the last run timestamp
last_run_timestamp = None

# s3 client object
s3 = None


def get_last_run_timestamp():
    try:
        last_run_object = s3.get_object(
            Bucket=bucket_name, Key=f'{locale_code}/last_run.json')
        last_run_data = json.loads(last_run_object['Body'].read().decode('utf-8'))
        return last_run_data.get('timestamp')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return None
        else:
            raise e

def set_last_run_timestamp(timestamp):
    data = {'timestamp': timestamp}
    s3.put_object(
        Bucket=bucket_name, Key=f'{locale_code}/last_run.json', Body=json.dumps(data))

def check_and_set_lock():
    global last_run_timestamp

    current_timestamp = int(time.time())
    last_run_timestamp = get_last_run_timestamp()

    if last_run_timestamp is None or current_timestamp - last_run_timestamp >= ( 60 * 60 * 60 * 24 ):
        # The last run was more than an hour ago or no last run timestamp exists
        # This script can run
        set_last_run_timestamp(current_timestamp)
        return True
    else:
        # Another instance is running or has recently finished
        return False

def parse_arguments():
    try:
        parser = argparse.ArgumentParser(
            description='This Script call Audible product API in Batch and store in S3.')

        parser.add_argument('--region_name', required=True,
                            help='AWS Region Name where S3 bucket present')

        parser.add_argument('--bucket_name',
                            required=True, help='AWS S3 Bucket Name.')

        # Optional Arguments
        parser.add_argument('--locale_code', default='us', choices=[
                            'us', 'ca', 'uk', 'au', 'fr', 'de', 'jp', 'it', 'in', 'es'],
                            help='Audible Market Place Locale Code for calling API\'s (default is US).')

        parser.add_argument('--base_url',
                            default='http://127.0.0.1:8000/', help='Audible Disprz Base Url.')

        parser.add_argument(
            '--debugging', choices=['Yes', 'No'], help='This param used to print debugging purpose.')

        parser.add_argument(
            '--exit_on_error', choices=['Yes', 'No'], help='This param used to stop code running when any exceptions occurs.')

        parser.add_argument('--resource_type', choices=[
                            'products', 'product', 'search'], default='products', help='Audible resource url Url.')

        parser.add_argument('--audible_programs', default=None,
                            help='Audible Filter options.')

        parser.add_argument('--products_sort_by', default=None,
                            help='Audible sort options.')

        args = parser.parse_args()

        global debugging, exit_on_error
        global locale_code
        global base_url, region_name, bucket_name
        global products_file_path, categories_file_path, resource_type, audible_programs, products_sort_by

        debugging = True if args.debugging == 'Yes' else False
        exit_on_error = True if args.exit_on_error == 'Yes' else False

        base_url = args.base_url
        locale_code = args.locale_code

        region_name = args.region_name
        bucket_name = args.bucket_name
        resource_type = args.resource_type
        audible_programs = args.audible_programs
        products_sort_by = args.products_sort_by

        # Setting up paths
        products_file_path = locale_code + '/' + \
            products_file_directory + '/' + products_file_name
        categories_file_path = locale_code + '/' + \
            categories_file_directory + '/' + categories_file_name

    except argparse.ArgumentError as e:
        print_log("Error in arguments:")
        raise e


def print_params():
    print('products_file_path:', products_file_path, "\n")
    print('products_file_name:', products_file_name, "\n")
    print('products_file_directory:', products_file_directory, "\n")
    print('categories_file_path:', categories_file_path, "\n")
    print('categories_file_directory:', categories_file_directory, "\n")
    print('categories_file_name:', categories_file_name, "\n")
    print('region_name:', region_name, "\n")
    print('bucket_name:', bucket_name, "\n")
    print('locale_code:', locale_code, "\n")


def set_s3_client():
    global s3
    s3 = boto3.client('s3',
                      region_name=region_name)


def get_ids_from_json(json_data):
    ids = []

    def process_category(category):
        ids.append(category['id'])
        if 'children' in category:
            for child in category['children']:
                process_category(child)

    for category in json_data['categories']:
        process_category(category)

    return ids


def read_file_content(file_path):
    return s3.get_object(Bucket=bucket_name, Key=file_path)['Body'].read().decode('utf-8')


def json_string_to_dict(json_string):
    try:
        json_dict = json.loads(json_string)
        return json_dict
    except json.JSONDecodeError as e:
        print_log("Error: Invalid JSON string.")
        raise e


def check_exist_or_create_file(file_key):
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        print_log("File already exists.")

        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                s3.put_object(Bucket=bucket_name, Key=file_key)
                print_log("File created successfully.")
                return True
            except Exception as e:
                print_log("Error creating file:")
                raise e
        else:
            raise e


def update_file_content(file_key, new_content):
    try:
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=new_content)
        print_log("File content updated successfully!")
    except Exception as e:
        print_log("Error updating file content:")
        raise e


# Function to save data to a JSON file
def save_to_s3(data):
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
                existing_ids = set(product['id']
                                   for product in existing_data['products'])
                new_products = [
                    product for product in data['products'] if product['id'] not in existing_ids]

                # Adding new products
                existing_data['products'].extend(new_products)

                new_data = existing_data

        except json.JSONDecodeError as e:
            # Handle the case where the file contains invalid JSON data
            print_log(
                f"Warning: The JSON file '{products_file_path}' contains invalid data. Appending new data without filtering.")
            pass

    # Save the new data to the JSON file
    time.sleep(3)  # Delay in seconds
    update_file_content(products_file_path,
                        json.dumps(new_data, ensure_ascii=False))


# Function to make the API call and fetch data
def fetch_data(page_num, category_id):

    url = f"{base_url}/api/catalog/products"
    params = {
        'limit': limit,
        'page': page_num,
        'category_id': category_id,
        'resource_type': resource_type,
        'audible_programs': audible_programs,
        'products_sort_by': products_sort_by,
    }

    headers = {
        'LOCALE-CODE': locale_code
    }

    response = requests.get(url, params=params, headers=headers)
    return response.json()


def main():
    start_time = time.time()
    print_log("Script started.")

    parse_arguments()
    set_s3_client()

    # Check if the script can run
    if not check_and_set_lock():
        print_log("Another instance is running or has recently finished. Exiting.")
        return

    # print_params()

    category_ids = get_ids_from_json(json_string_to_dict(
        read_file_content(categories_file_path)))

    for category_id in category_ids:
        # Loop through pages 1 to page_to_loop
        for page_num in range(1, page_to_loop):
            try:
                data = fetch_data(page_num, category_id)
                save_to_s3(data)  # Save data to S3 Bucket

                print_log(
                    f"Page {page_num} data saved for category id {category_id}")
            except Exception as e:
                exception_message = f"An exception occurred: Page {page_num} data not saved for category id {category_id}\n"
                exception_message += str(e)  # Include the exception message

                # Include traceback information
                traceback_info = traceback.format_exc()
                exception_message += f"\nTraceback:\n{traceback_info}"

                # Print the detailed exception message
                print_log(exception_message)

                if exit_on_error:
                    exit()

            # Add a delay between API calls
            time.sleep(3)  # Delay in seconds

        # Add a delay after processing each category
        print_log("Waiting for 1 minute...")
        time.sleep(60)  # Delay in seconds

        end_time = time.time()
        elapsed_time = end_time - start_time
        print_log(f"Script finished. Time taken: {elapsed_time:.2f} seconds.")


def print_log(message):
    current_datetime = datetime.utcnow()

    log_message = f"[{current_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')} UTC] {message}"

    if debugging:
        print(log_message)

    log_folder = "log"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_file_path = os.path.join(
        log_folder, f"log_{current_datetime.strftime('%Y-%m-%d')}.txt")
    with open(log_file_path, "a") as log_file:
        log_file.write(log_message + "\n")


if __name__ == "__main__":
    main()

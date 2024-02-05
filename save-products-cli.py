import json
import subprocess
import os
import time

def run_cmd(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        raise ValueError(result.stderr)

def remove_duplicates(products):
    unique_products = {}
    for product in products:
        asin = product["asin"]
        if asin not in unique_products:
            unique_products[asin] = product
    return list(unique_products.values())

def save_to_json(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def insert_into_json(data, filename):
    if not data:
        return

    existing_asins = set()
    existing_data = []
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r") as file:
            existing_data = json.load(file)
            existing_asins = set(product["asin"] for product in existing_data)

    new_data = [product for product in data if product["asin"] not in existing_asins]

    if new_data:
        existing_data.extend(new_data)
        save_to_json(existing_data, filename)

num_pages = 10
num_results_per_page = 50

output_file = "all_products.json"

for page in range(1, num_pages + 1):
    cmd = f'C:\\Users\\USER\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\Scripts\\audible.exe api catalog/products -p page={page} -p category_id=21881872031 -p num_results={num_results_per_page} -p response_groups=contributors,media,category_ladders,price,product_attrs,product_desc,product_extended_attrs,product_plans,rating,review_attrs,reviews,sample,sku'
    cmd_output = run_cmd(cmd)
    response_data = json.loads(cmd_output)
    products_on_page = response_data["products"]
    filtered_products = remove_duplicates(products_on_page)

    insert_into_json(filtered_products, output_file)
    print(f"Page {page}/{num_pages} data saved to {output_file}")

    # Add a delay of 6 seconds after each set of 50 API calls
    if page % 50 == 0 and page != num_pages:
        print("Waiting for 6 seconds...")
        time.sleep(6 * 60)

print("All pages data saved.")

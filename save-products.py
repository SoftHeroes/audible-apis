import requests
import csv
import json
import time
import os

# CATEGORIES_FILE_NAME = 'categories.json'
CATEGORIES_FILE_NAME = 'categories-us.json'
LOCALE_CODE = 'us'


# Function to make the API call and fetch data
def fetch_data(page_num,category_id):
    # url = f'https://audible-integration.disprz.com/api/catalog/products'
    url = f'http://127.0.0.1:8000/api/catalog/products'
    params = {
        'limit': 50,
        'page': page_num,
        'category_id': category_id
    }
    
    # US
    headers = {
        'ADP-TOKEN': '{enc:/5reUCW0JQpR7VXG0vozMvEJGFyEicBAe8naREaQbRKip2atzgqB1hvCW9Id2biMs631NyjWvXoU0kxwHKHZ8+VHKl6O00FX7iqMzkR+FtB1/kfd9ZSUZf1lkbNbqmt968pk6/l4UNNTLStscqxINQE5B3cxLjJfwibFVnRLqGY2In0Lm9XguZizTLyb2lzBDDbeQCKyl4ygRfmIKeyV2gdMBO0/4hF2rJcTDvkMsaW8b1zCvy//m9lKzr30MshOD0/S6+dlZyiDrYM51L/iclgY3bC9y7oMFJMkkFdtMJcTjNObKhkwdj/PO+JzO3XmnOzm3keudqbVsCjAppp1Q5iacnXZ3Ewpxp0RbbqK9codOoZJuzly2bxeOHaPVdvg5L/8K3v2z+tRqyYEXvPgE2VDyuuL3FQJkqw5jdJRsBYfEqyNHl0ae5kfceuwy2ya4ojiugX36+oUxOCdTMLm9knmlp2zBB0N+qcdyAl7DWL8lv4rfLb8Alo6sPfPMq3oOQ+h5d17d8PyjAT+LXPSPZSwldyhcd5wf9NjRkUFB5ybe6znhOfGyZzt8BFaQ9KhPLegwdUbLm1WE0XUoK1eQqe54b0cc5jbZHuarZ0FDB8JtHSbOAk2FzM9OoPDO46Dk40G/01xbFTJM7UDwT+waDRJq4AD6OLLFDd91OAYruLQsd6M8WUipbss5JEHRAKt6IhNV1lNA9eOjf/wk8Y/RwkfuG1e/C/j2CeXgXa25jYJn/ZFlY8CInLd9zrkRjcWAoGuEp7tgDzRef4Duji/G/0Kspa4KeVaqPoq/TkHyUbqSKXAEM3COSGhsT+23BQ06eTcUPD3zn9jyhgThNHEj1D5K9GPIdbbTrhrQMuEAMH8oL8CmLiI9igfD7RiKCbjWn51Dha5QCawzb7xj9BvkPB5mTh5cJe919EkZBfeXTPhKLCIAVSOL3MZkBENmOZYgCxJ2Fo/migzSYQfXwxAi+WONNpFTcRCTOHB0sjg2A+am8JOo3bQwAPA6sM+xg48tGl8BfMP1UvxY0T/rzkmuEojndairVng1jjiVMkrmFY=}{key:n96lM2bDvhMikrPQhjQ7x+CJL6oMWnzAMd1tXuRqDicMayD0qqTuT2+p2nKFTY3/kHhhtCBfaXbSn84y7BEwtNljIA7SndSPj7rsZuyT55ri4lxCQWmXhT0EPyYNygRn00thIHzwnYuCYHbCI+csKVMXzdw1yN9DPiJXBcTFZrtIVPPz1N3IC+UearvWyqKk3CYG2gRXhFb40QgphC5oxkHHuNR0R3FOlrq5a+6MSJ5Z/OXtVowimum7wSiwp+peU5i7txnq21fn1oPLC87C47ab/ZUw3y0oDtmKLRmfOvdQ+5TRjv2ztLV+EYw2j0axztYzMq/Q8gUHHD7AIX6LOg==}{iv:z8/WQ5KAfU47OQO0+0vH1A==}{name:QURQVG9rZW5FbmNyeXB0aW9uS2V5}{serial:Mg==}',
        'PRIVATE-KEY': "-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEA0QViNJSitOZ3QvWVM+mJdV2B/3/aNRtw3kEQBIkua+4LAWT9\\nyKfXK2juP8c3/pfRkPV/S2jndk8wxZSq4AmYXCPKOh/BdscFCksZRxd/CjXTuJLd\\nNIj1Egf0K4Ot1xrehGYL+hxuzF53JEm63XCDb2fjQdzW2wpphJwWRqq/3G/L/e08\\nloWz0HMXbqme0+Hl6Zc/6Ay3E9LdoAclcb26Qmt0jitO7UCG52HYv1nmmC5YU2zW\\nxE36Je59qZh5uvOXn/BtxN5mbYCPhBEHEPmFij+ZVK0uiex7iemQKU7Q/1h3eX9v\\nW+eawtVF41GFuz1WCgjBKG/IlbXwJg7NUmLSWQIDAQABAoIBAQCaSDUCxquKh4qE\\nPC1TUhAKN2kbJE32YTjgdHnUP0WqmNw6vUat82VZP2yMWwozu/AN5Yd+LAKdSzqe\\nvGucTrjNWgWM/Z+ZgrFvtZsE5Iz7BlwuowjwHB94nbJW5C1O1yBj7cbtaEtIQnoC\\nqQFrLf92HeKa3N0idP8JyQSQSLyxgeYkUX1tKihwQmZi2a9VKXeoz5c7M2V1l4sG\\n/M2iyCoTEgs+pYK4wJk1lLPvknL41SX+UwbPcwYsq4xNnrNlabI9JBF8dNB12mdu\\nI6Ng6Y6uzfYOmZuZURg22Ku2qVRjYntfKaszmZV4RxBVOBHJKy/2hoDPDSyt9YD8\\n+YorOz75AoGBAOzscDwHFjLFlx0hMJcvfGYDIqx2rzkScS6TmaQULMUvvk0YgmA4\\nLijftkjeNM3mu2bDJLjullbM0OFte9umnBrlEJjtV7LZdBTn5qkUpUc9yMkLfHqs\\nP/P1dBetAjTNEKQo2PAbZCwSlPBdYnXDC5Y8JgogYW+K2A/U/jw4H6SHAoGBAOHZ\\nzoibKkD2pk1GsBvqwYkTQyMOPal65Lk04acsqGAoRzHkWG6wprHIIjlaKZ+lPqn0\\nJhfJ6rV1k/qTgAz4MU0g32TmkJJZ2i0RO03tME/orEJeuGQWgeYg/b0+eLAR20fO\\nfbFsyyUulNszOg6DTtFq+Utp6DQr87IioQj5omofAoGAcIydgJapP/NHpynmKFwB\\nj4B7z0wOT2FobQTnHuAKqJ3WnE9BWC44F2i28oTEtu+eJOIdJtEIkDF6JSzaguzy\\nCYC50rwlRiwxDeFgXQAWx/Ic2Qzg1HHRa7Y1sS2Z97VW63UQIXgRrTIimNDz/hdr\\nALKQK41YXCGsJFE9eSP8PC8CgYAlmBjd+l4dNDFYeaTE8N3IUHGDe1JeTLuX7KqH\\nJlLctrerIWRrAHKu8y5nN4/oKBx3M9HHce/kxq6cLkNJZWLngMpOxGZaRiSgDdc+\\nUHYTRxqtbZDp8CktQl6aSrTSMha7LC8WApMKHGfg2PUYB1luWI0otXdWf95vz33Y\\nvZ0AZwKBgQCLQpJEaB9jxQmdo2fr75QYerRK4brUYV3u8LLviYrAYDb1urWuHQ0X\\n0uoCj5Q/zJcKRivj37cKsMdq8OlgqY4G/epGuHXY/z16Txk/rH6OeJuaesCTmrZd\\nQQf0AonkSilwsq/k4/0NiXdeMI8/tXLWchWPalQROWjxFIZHxXqNoA==\\n-----END RSA PRIVATE KEY-----\\n",
        'LOCALE-CODE': 'us'
    }
    
    # IN
    # headers = {
    #     'ADP-TOKEN': '{enc:a7C5d/7bLw7KgI/aqs5IlPiwn0fjn7MNL98OdjLf2kS4VCWRbAV2NHJA9LwyLU4O0WZ/n2Dm5K6f/HzVvSi/si4fAdAIpk+NicoYr8X3JgKEoeVFUBh+nizsOtY2lLvWu+sAR2CK0qBeyN5j1t0TVCU8lK3ri1cNmKjVbMlhQIhNEuSyqn+u9gJ/yRLG9bZtW2MN3Fvvb9px4M3FteMmxYaSkuQLaonk28PWYl3365w9W19H33M+0B54g18N/vkxXOUrgP2OJxmP+XzRHF+2sirsKE3EwkCQU2uA8x9n45pDcZbnMRiFL0gBeWCsEOtYOjBAOSWRQrqcRUVFGG7NvpPdRxfBJlnMAULwYz3sjb47QCYjyra0LkCK6ee2iYJn6bZlvigd1V1XrNdlahFTKbWCQrkDTcvooPofILoFg4ZdxhG+TZZfv1kLcc0vhDpKIU5R2FAZuSVyINROUBjZAoFaZxYkUtUkSRuFrWeCIlLm/BTEm+e0muXrgLksAmAl89kFs6ucUgQu17f1iDeLkScCrt2eNOzUVZJgPEzfAQMIPk0ajsu4t6ACntpFi1k//hF6FvTPZBQoaXohDjy+dhXHWWFwQBXrg0wBVvW1qsdhf86T5ZrzjL/7lHG9hCa1je+SxzO4V3lsQSBkKlj30Kvh7tzBCuw0OSDN4btpIcoHLBHJo8dKsrR65DlVIHXCz1T6Kq8quUlc0Q3s5uRO6E57I0v1+BIYzuxuuPPxWfHnUELqHYXPbx1dVtjXa/l0JBjGVzM+kuu2B/HFdcGo5l8xhgB52xtlS6ABRwrbLncUPeZLv5MDEHSS1jedBwpte4Q0yeQZxJVjgvg6U9NK7pUjmabzALltAOYsmmHaprr7h5AXueq9n7QLyOrZLDgN+Q9Yc7YfctIq0CVxg0DoPCq9vcJsJMxr/pC7GUzURbGu6RRp1NMwyKdug6kNgDgu+i35gKV9cxtIGpRQyVA7S+VNUJaKOqa7HpT18p6xEzjqsv6fzmBRW8IrDDi+UNyVZ1x/TuOw0YkBiIHzweDfmfMw+bkZV9j5CdP9eSs6tI4=}{key:M4vUhJw7AW4pk2usBrXEOYTKue44WED9/4QmWRTq9u1VZCMlLnOVr8oq9x5P/eb0+xPM6Htv5rb4TIp3qjcuBQHVWJ9vN7Q9SNFtZLzamTGZ3r+VcnirmGkqyuhkUF7KIwiDdAUCrP0zLbcW3EFmZC0pb2GM1DWsuLxSeg+shfs51cBAZt+btH7rk/U+CWRdCo07GClPT4BchgodV3zqBIrlNJMTPRYH02iq6r7Kd+oEy+sLVuDkfpzgjK2ZFZ1ta8xOaOC8D84/K3CdCNFE0e/4FYPKW/sdGO+9R5z5lAyU79cRyfPWJM7y5dQqeOp/HytiU0DKevap5mli92d+EQ==}{iv:NCdtpqZA0/Myep+qaIhIuQ==}{name:QURQVG9rZW5FbmNyeXB0aW9uS2V5}{serial:Mg==}',
    #     'PRIVATE-KEY': "-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEApyZ+b3bxpmZZLhOKyhb/uyUjCv4ZlbmVWbFDy/eSIPkDjiZm\\nO4Sg4YDsuDgPpzdAwCBtWuJBLdmFtkrQEp4wR7KIyvWGGCbZf6e0ynoIsqiSZ5/q\\nXV8T5/sAQywT3odcUZTVn4RPeoCL0NLoozhnRLD32JYKm1M+s6EZE6Ag/2cA45eb\\nfg8v531XuXECou3XiWxbnAVF7vKW8clrRAb6Hg5BiL0u3sJPp20oQf5vzc1p3c8U\\nfmWDxV9uTyFzb6mJuu9BTEpiP37mjFAY3G5mdM2JicviSogCmG3Dw65326zlviOf\\ncq90fovEQB6aVNJxd9V+vgfo3iDNScGFO0WKxwIDAQABAoIBAFz4SDLvUZFgNBIw\\nxG2LRUpuaYNfuhNRWgS9WBxG43x7hMK4EPzh1CoZb5E3fV1gmh9C6hA28FH0Py8Z\\nhYoVen0mjHd3ANLGKQub2C8WmWfl4yjIBa9Rhtzs+0Rha9vGJk8qHXfQO/TDMwE/\\nji3a3XWTiQdqzRN/xcxbunr0AeaMGefmK65Og9aivEYQZxarNnFRGfKDvtLDl9W9\\nvr2AZZa66dAt21XJpesXx6TErm9/gUtGIhshTNVPjqMAxjNEp4zpd7sqzEdl+MKq\\n4nrVpHlZ1GAyLY9bX2oLgfphdzUOU8St/rJMKqeT8OLPbRPXM/pboyqwjXiDiYbt\\nwt65soECgYEA1rv6vR+L3753p5T7YcVcrhnJ3uOXXufuj3l6FEgBoqmkgUyM6eGu\\n7aE9dOXKmEXG/DfFA1vdneM5B0hBxc2kISQ41v1PQ1Q3sgm7qkXo40nIPHGug03I\\nwvtHoWNmrXG2wDToEQzwduKptWFqpLAol/jLCkOIqcjm2PkyxmBP8XECgYEAx0WW\\nC5fx84/R5QFlcH9/7w7HEVtD5Vo03MoLuDcaldpFK/H49dQcbjX1XOsExAjP5Y19\\nvTAac+zLRfHksr7LjEEU8H+P16KIZ6kfyXsTNkKLn6twHfGzUXExZh6/DppaUON6\\noGb2RL0ufhDYMtw6GhimL1QRzMUoaSizTu81o7cCgYEAjXOIyTpVpo7OPVs7eP1M\\nfvdH7oZXuVHo6SQpUeDZCvDbB72IeayL0cdMN4wDt+kHGjAWnI7QXuhGMdDcWtOK\\n0bYNpzl4FC8O/T3CHHku30JEH+T3A1Gi9SYX2m0jPw/QRa7UTB8M7BOFnZDNci0E\\noI9oGJvCE63eu4D0fI8HOlECgYEAv/P+F2jkfrQ5ghmYN4f6GrPneoapnpMIfO57\\n35XlHBjHrQ9HvLX4NQnxMvKJArViXkOvrcBamvSs0tGydaRoutAudYTLcPJ15zT5\\nE8JkvU3Y5ZPlSlL7YyZgaXiQnmZ9PZIDG+RSseBymqlrOYL+zQiVfN3Ez7XTuYil\\nQRIYX30CgYAMZFNW+iDiEZod5TyA6465QTXmzqFr1ESlDxrqCIOGxPf2UEn0Ib7z\\ngNAGyaXD68MgkxCIAetEsyLjpm6kcbcFetmcKMHBcDRtVDvSV4rmVJdFv3K8hC3P\\nywC5vssWm72y4m9bHatrMHXfBf9tooDiSNNH1/t8OTh2vaPVXk0A7w==\\n-----END RSA PRIVATE KEY-----\\n",
    #     'LOCALE-CODE': 'in'
    # }
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()


# Function to save data to a CSV file
def save_to_csv(data):
    with open('products.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['id','title', 'description', 'publisher_name', 'runtime_length_min', 'language', 'authors', 'categories', 'product_image', 'web_url', 'mobile_url'])
        for product in data['products']:
            id = product['id']
            title = product['title']
            description = product['description']
            publisher_name = product['publisher_name']
            runtime_length_min = product['runtime_length_min']
            language = product['language']
            authors = ', '.join(author['name'] for author in product['authors'])
            categories = ', '.join(category['ladder'][-1]['name'] for category in product['categories'])
            product_image = product['product_image']
            web_url = product['web_url']
            mobile_url = product['mobile_url']

            writer.writerow([id,title, description, publisher_name, runtime_length_min, language, authors, categories, product_image, web_url, mobile_url])

# Function to save data to a JSON file
def save_to_json(data):
    file_name = 'products.json'
    new_data = data

    # Check if the JSON file already exists
    if os.path.exists(file_name):
        # Read the existing JSON data
        with open(file_name, mode='r', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
                # Check if the 'products' key exists in the existing data
                if 'products' in existing_data and isinstance(existing_data['products'], list):
                    # Check if the 'id' of the new products already exists in the existing data
                    existing_ids = set(product['id'] for product in existing_data['products'])
                    new_products = [product for product in data['products'] if product['id'] not in existing_ids]
                    existing_data['products'].extend(new_products)
                    new_data = existing_data
            except json.JSONDecodeError:
                # Handle the case where the file contains invalid JSON data
                print(f"Warning: The JSON file '{file_name}' contains invalid data. Appending new data without filtering.")
                pass

    # Save the new data to the JSON file
    time.sleep(3)  # Delay in seconds
    with open(file_name, mode='w', encoding='utf-8') as file:
        json.dump(new_data, file, ensure_ascii=False)

# Main loop to call API and save data to JSON
def main():
    
    category_ids = get_ids_from_json(read_json_to_dict(CATEGORIES_FILE_NAME))
    
    for category_id in category_ids:
        for page_num in range(1, 15 ):  # Loop through pages 1 to 1300
            try:
              data = fetch_data(page_num,category_id)
              save_to_json(data)
              print(f"Page {page_num} data saved. for category id {category_id}")
            except:
              print(f"An exception occurred: Page {page_num} data saved. for category id {category_id}")

            # Add a delay of 6 minutes after every 50 API calls
            if page_num % 50 == 0 and page_num < 1168:
                print("Waiting for 6 minutes...")
                time.sleep(6 * 60)  # Delay in seconds
        print("Waiting for 1 minutes...")
        time.sleep(1 * 60)  # Delay in seconds


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

def read_json_to_dict(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


if __name__ == "__main__":
    main()

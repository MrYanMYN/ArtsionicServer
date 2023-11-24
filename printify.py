import os
import requests
import json
import base64

def check_shops_id(API_KEY_PRINTIFY):
    printify_headers = {
        'Authorization': f'Bearer {API_KEY_PRINTIFY}',
        'Content-Type': 'application/json'
    }

    response = requests.get(
        'https://api.printify.com/v1/shops.json',
        headers=printify_headers
    )

    return response.json()


def publish_product(shop_id , product_id, API_KEY_PRINTIFY):
    # Set up Printify API headers
    printify_headers = {
        'Authorization': f'Bearer {API_KEY_PRINTIFY}',
        'Content-Type': 'application/json'
    }

    payload = {
    "title": True,
    "description": True,
    "images": True,
    "variants": True,
    "tags": True,
    "keyFeatures": True,
    "shipping_template": True
    }

    # Upload the image to Printify
    response = requests.post(
        f'https://api.printify.com/v1/shops/{shop_id}/products/{product_id}/publish.json',
        headers=printify_headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(f'{response.status_code} Failed to publish {response.json()}')

    published_product = response.json()
    return published_product



def upload_image_to_printify(image_path, API_KEY_PRINTIFY):
    # Read image data
    with open(image_path, 'rb') as img_file:
        image_data = img_file.read()

    # Encode image data to Base64
    base64_image_data = base64.b64encode(image_data).decode('utf-8')

    # Set up Printify API headers
    printify_headers = {
        'Authorization': f'Bearer {API_KEY_PRINTIFY}',
        'Content-Type': 'application/json'
    }

    imageName = os.path.basename(image_path)
    # Upload the image to Printify
    response = requests.post(
        'https://api.printify.com/v1/uploads/images.json',
        headers=printify_headers,
        json={'file_name': imageName, "contents": base64_image_data}
    )

    if response.status_code != 200:
        raise Exception(f'Failed to upload image: {response.json()}')

    uploaded_image = response.json()
    return uploaded_image['id']

def create_product_printify(image_id, metadata, shop_id, API_KEY_PRINTIFY):
    # Set up Printify API headers
    printify_headers = {
        'Authorization': f'Bearer {API_KEY_PRINTIFY}',
        'Content-Type': 'application/json'
    }

    product_data_01 = {
        "title": metadata['name'],
        "description": metadata['description'] + "\n\n" + metadata['hashtags'],
        "blueprint_id": 725,
        "print_provider_id": 39,
        "variants": [
            {
                "id": 73871,
                "price": 14990,
                "is_enabled": True
            },
            {
                "id": 73873,
                "price": 14990,
                "is_enabled": True
            },
            {
                "id": 73875,
                "price": 14990,
                "is_enabled": False
            },
            {
                "id": 73877,
                "price": 14990,
                "is_enabled": False
            }
        ],
        "print_areas": [
            {
                "variant_ids": [73871, 73873, 73875, 73877],
                "placeholders": [
                    {
                        "position": "front",
                        "images": [
                            {
                                "id": image_id,
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1,
                                "angle": 0
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Upload the image to Printify
    response = requests.post(
        f'https://api.printify.com/v1/shops/{shop_id}/products.json',
        headers=printify_headers,
        json=product_data_01
    )

    if response.status_code != 200:
        raise Exception(f'{response.status_code} Failed to create product: {response.json()}')

    uploaded_product = response.json()
    return uploaded_product
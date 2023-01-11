# inspo: https://python.plainenglish.io/how-to-scrape-images-using-beautifulsoup4-in-python-e7a4ddb904b8

import requests
from bs4 import BeautifulSoup
import os
import urllib.request
import json
import random

with open('input_dir.json', 'r') as f:
    input_json = json.load(f)
    root_dir = input_json['input_dir']
    if not root_dir:
        root_dir = 'input/'


def input_filepath_exists():
    return os.path.exists('input/train/') and os.path.exists('input/valid/')


def build_filepath(class_name):
    train_path = f'input/train/{class_name}/'
    valid_path = f'input/valid/{class_name}/'
    # output_path = 'outputs/'
    for path in [train_path, valid_path]:
        if not os.path.exists(path):
            print(f'Building filepath {path}')
            os.makedirs(path)


def get_image_tags(url):
    user_agent = 'Mozilla/5.0 (Linux; Android 10; SM-A205U) ' \
                 'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/106.0.5249.126 Mobile Safari/537.36'
    # Google Image Search doesn't like the headers
    if 'google' in url:
        page = requests.get(url)
    else:
        page = requests.get(url, headers={'User-Agent': user_agent})

    soup = BeautifulSoup(page.content, 'html.parser')
    return soup.find_all('img')


def scrape_images(class_name, queries):
    build_filepath(class_name)

    train_counter, test_counter = 0, 0

    for query in queries:
        print(f'downloading {query} images')

        # scrape from Google images
        google_url = f"https://www.google.com/search?q={query}" \
                     f"&sxsrf=ALeKk03xBalIZi7BAzyIRw8R4_KrIEYONg:1620885765119" \
                     f"&source=lnms&tbm=isch&sa=X" \
                     f"&ved=2ahUKEwjv44CC_sXwAhUZyjgGHSgdAQ8Q_AUoAXoECAEQAw&cshid=1620885828054361"

        # scrape from shutterstock
        ss_url = f"https://www.shutterstock.com/search?searchterm={query}&sort=popular"

        # scrape from istock
        istock_url = f"https://www.istockphoto.com/search/2/image?phrase={query}&sort=best"

        image_tags = []
        for url in [
            google_url,
            ss_url,
            istock_url
        ]:
            image_tags += get_image_tags(url)

        random.shuffle(image_tags)
        test_train_boundary = int(len(image_tags) * 0.8)
        error_counter = 0

        for i, link in enumerate(image_tags):
            ignore = ['.gif', '.svg']
            # TODO: Better way to get the extension
            if link['src'][-4:] not in ignore:

                if i > 0:
                    try:
                        if i <= test_train_boundary:
                            urllib.request.urlretrieve(
                                link['src'],
                                f"input/train/{class_name}/{query.replace(' ', '_')}_{i:02d}.jpg"
                                )
                            train_counter += 1
                        else:
                            urllib.request.urlretrieve(
                                link['src'],
                                f"input/valid/{class_name}/{query.replace(' ', '_')}_{i:02d}.jpg"
                                )
                            test_counter += 1
                    except Exception as e:
                        print(f'Error sourcing {link["src"]}. Error message: {e}')
                        error_counter += 1

        print(f'Saved {len(image_tags) - error_counter} {query} images')

    print(f"Saved {train_counter} train images and {test_counter} test images in total")


def generate_dataset():
    # Read image queries from image_queries.json
    # Each query currently generates ~20 images

    with open('image_queries.json', 'r') as f:
        queries_json = json.load(f)

    for class_name, queries in queries_json.items():
        scrape_images(class_name, queries)

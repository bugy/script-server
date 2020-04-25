#!/usr/bin/python3
import sys
import tempfile
import time

import requests

# api_key = os.environ.get('KITTENS_API_KEY')
# if not api_key:
#     print('Please request api_key from http://requestkittens.com and put it into KITTENS_API_KEY env. variable')
#     sys.exit(-1)

for i in range(1, 6):
    # response = requests.get('http://requestkittens.com/cats?numOfResults=1', headers={'Authorization': api_key})
    # if (response.status_code != 200):
    #     print('Ooops, all kittens are hiding today :(')
    #     sys.exit(-2)
    #
    # response_json = response.json()
    #
    # image_url = response_json['_items'][0]['url']
    # image_id = response_json['_items'][0]['id']
    # file_name = str(uuid.uuid4()) + '.png'
    # file_path = os.path.join('/tmp', 'script-server', file_name)

    image_response = requests.get('https://cataas.com/cat/kitten?type=medium')
    if (image_response.status_code != 200):
        print('Ooops, all kittens are hiding today :(')
        sys.exit(-2)

    f = tempfile.NamedTemporaryFile()
    f.write(image_response.content)
    file_path = f.name
    open(file_path, 'wb').write(image_response.content)
    print(file_path)

    time.sleep(3)

    f.close()

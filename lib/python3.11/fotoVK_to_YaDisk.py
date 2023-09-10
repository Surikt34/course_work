import json
import os
from datetime import datetime
from pprint import pprint
from urllib.parse import urlencode
import requests

# APP_ID = '51741073'
# OAUTH_BASE_URL = 'https://oauth.vk.com/authorize'
# params = {
#     'client_id': APP_ID,
#     'redirect_uri': 'https://oauth.vk.com/blank.html',
#     'display': 'page',
#     'scope': 'status, photos',
#     'response_type': 'token'
# }
#
# oauth_url = f'{OAUTH_BASE_URL}?{urlencode(params)}'
# print(oauth_url)

token = 'vk1.a.CHkvbnXnWVLMLfpmBqBSGR_DC1lrI09HPnNTk1ILQdXe0ajJBNinq1MJy2cDw0_8txs9VB63F-y3fkkrkKkOW3qBO-Pqtr9Lp95tSeFGlZ44Sj0_A_eqs1H4Cva-6awzSDd-1UNHCrrxpvKE-5slZ1GLh8RF6_0lTbK3yB7EXrjLRstqL_BHNI-E07FIgpnsema4IxN0R8AMDDzOUlOs5g'
class VKAPIClient:
    API_BASE_URL = 'https://api.vk.com/method'
    def _build_url(self, api_method):
        return f'{self.API_BASE_URL}/{api_method}'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
    def get_profile_fotos(self):
        params = {
            'access_token': self.token,
            'v': '5.131'
        }
        params.update({'owner_id': self.user_id, 'album_id': 'profile', 'extended': '1'})
        response = requests.get(self._build_url('photos.get'), params=params)
        return response.json()

if __name__ == '__main__':
    vk_client = VKAPIClient(token, 33034989)
    photos = vk_client.get_profile_fotos()
    # pprint(photos)

    max_resolution_urls = []

for item in photos["response"]["items"]:
    if "sizes" in item and isinstance(item["sizes"], list) and len(item["sizes"]) > 0:
        max_size = max(item["sizes"], key=lambda x: x.get("height", 0) * x.get("width", 0))
        date_object = datetime.fromtimestamp(item["date"])
        formatted_date = date_object.strftime('%d.%m.%Y')
        max_resolution_urls.append({
            "url": max_size.get("url", None),
            "resolution": max_size.get("height", 0) * max_size.get("width", 0),
            "likes": item["likes"]["count"],
            "date": formatted_date
        })

sorted_urls = sorted(max_resolution_urls, key=lambda x: (x["resolution"], x["likes"], x["date"]), reverse=True)
top_5_urls = sorted_urls[:5]
result_list = []
for entry in top_5_urls:
    name = f"{entry['likes']}likes_{entry['date']}.jpg"
    result_list.append([name, entry['url']])

file_to_upload = []
for file_name, url in result_list:
    response = requests.get(url)
    file_to_upload.append(file_name)
    with open(file_name, 'wb') as file:
        file.write(response.content)

base_url = 'https://cloud-api.yandex.net'
params = {'path': 'FotoVK'}
headers = {'Authorization': '***'}
response = requests.put(f'{base_url}/v1/disk/resources', params=params, headers=headers)

if 200 <= response.status_code < 300:
    for file_name in file_to_upload:
        params = {'path': f'FotoVK/{file_name}'}
        response = requests.get(f'{base_url}/v1/disk/resources/upload', params=params, headers=headers)
        path_to_upload = response.json().get('href', '')
        print(path_to_upload)

        with open(file_name, 'rb') as file:
            response = requests.put(path_to_upload, files={'file': file})
            print(response.status_code)

    info_files = []
    for file_name in file_to_upload:
        file_size = os.path.getsize(file_name)
        info_files.append({
            'file_name': file_name,
            'size': file_size
        })
    with open('info_photos.json', 'w') as json_file:
        json.dump(info_files, json_file, ensure_ascii=False, indent=4)
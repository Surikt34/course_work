import json
import os
from datetime import datetime
import requests

class VKAPIClient:
    API_BASE_URL = 'https://api.vk.com/method'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    def _build_url(self, api_method):
        return f'{self.API_BASE_URL}/{api_method}'

    def get_profile_photos(self):
        params = {
            'access_token': self.token,
            'v': '5.131',
            'owner_id': self.user_id,
            'album_id': 'profile',
            'extended': '1'
        }
        response = requests.get(self._build_url('photos.get'), params=params)
        return response.json()


class YandexDiskClient:
    BASE_URL = 'https://cloud-api.yandex.net'

    def __init__(self, token):
        self.token = token

    def create_folder(self, path):
        params = {'path': path}
        headers = {'Authorization': f'OAuth {self.token}'}
        return requests.put(f'{self.BASE_URL}/v1/disk/resources', params=params, headers=headers)

    def get_upload_link(self, path):
        params = {'path': path}
        headers = {'Authorization': f'OAuth {self.token}'}
        response = requests.get(f'{self.BASE_URL}/v1/disk/resources/upload', params=params, headers=headers)
        return response.json().get('href', '')

    def upload_file(self, path, file_data):
        upload_link = self.get_upload_link(path)
        with open(file_data['file'].name, 'rb') as file:
            return requests.put(upload_link, data=file)


if __name__ == '__main__':
    VK_TOKEN = 'vk_token'
    YANDEX_TOKEN = 'ya_token'

    vk_client = VKAPIClient(token=VK_TOKEN, user_id=33034989)
    photos = vk_client.get_profile_photos()

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

    yandex_client = YandexDiskClient(token=YANDEX_TOKEN)
    response = yandex_client.create_folder('FotoVK')
    if not (200 <= response.status_code < 300):
        print(f"Error while creating folder: {response.status_code} - {response.text}")

    for file_name in file_to_upload:
        response = yandex_client.upload_file(f'FotoVK/{file_name}', {'file': open(file_name, 'rb')})
        print(f"Upload status for {file_name}: {response.status_code}")

    info_files = []
    for file_name in file_to_upload:
        file_size = os.path.getsize(file_name)
        info_files.append({
            'file_name': file_name,
            'size': file_size
        })

    with open('info_photos.json', 'w') as json_file:
        json.dump(info_files, json_file, ensure_ascii=False, indent=4)

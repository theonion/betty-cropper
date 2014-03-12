from django.core.files.storage import Storage

from betty.conf.app import settings

import requests


class BettyCropperStorage(Storage):

    def __init__(self, base_url=settings.BETTY_IMAGE_URL):
        if base_url[-1] == "/":
            base_url = base_url[:-1]
        self.base_url = base_url

    def delete(self, name):
        raise NotImplementedError

    def exists(self, name):

        detail_url = "{base_url}/api/{id}".format(base_url=self.base_url, id=name)
        r = requests.get(detail_url, headers={"X-Betty-Api-Key": settings.BETTY_PUBLIC_TOKEN})
        print(r.content)
        return r.status_code == 200

    def listdir(self, path):
        raise NotImplementedError

    def size(self, name):
        raise NotImplementedError

    def get_available_name(self, name):
        return name

    def _save(self, name, content):
        # data = {"image": lenna, "name": "LENNA DOT PNG", "credit": "Playboy"}
        # res = self.client.post('/images/api/new', data)
        endpoint = "{base_url}/api/new".format(base_url=self.base_url)

        data = {"name": name}
        files = {"image": content}

        r = requests.post(endpoint, data=data, files=files, headers={"X-Betty-Api-Key": settings.BETTY_PUBLIC_TOKEN})
        if r.status_code != 200:
            print(r.content)
            raise IOError("Save failed")

        return str(r.json()["id"])

    def url(self, name, ratio="original", width=600, format="jpg"):

        # TODO: id string bullshit

        return "{base_url}/{id_string}/{ratio}/{width}.{format}".format(
            base_url=self.base_url,
            id_string=name,
            ratio=ratio,
            width=width,
            format=format)

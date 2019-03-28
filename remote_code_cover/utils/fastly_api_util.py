import requests
import sys

if sys.version_info[0] < 3:
    from urllib import urlencode
else:
    from urllib.parse import urlencode


class FastlyApiClient:
    api_host = 'https://api.fastly.com'
    auth_token = None
    service_id = None

    def __init__(self, auth_token, service_id):
        if len(auth_token) != 32:
            raise Exception('Fastly auth token should be 32 characters. Are you sure you have the correct token?')

        self.auth_token = auth_token
        self.service_id = service_id

    def path(self, version=None, suffix=''):
        """
        :param int version:
        :param string suffix:
        :return string:
        """
        path = '/service/{}'.format(self.service_id)
        if version:
            path += '/version/{}'.format(version)
        path += suffix
        return path

    def do_request(self, http_method, uri, params=None, data=None):
        """
        Does an API request with the supplied http method (string),
        params (dict), uri (string), data (url_encoded string)
        Returns a requests response object.
        """
        headers = {
            'Fastly-Key': self.auth_token,
            'Accept': 'application/json',
            'cache-control': 'no-cache'
        }
        url = self.api_host + uri
        params = params if params else {}
        response = requests.request(http_method, url, headers=headers, params=params, data=data)
        return response

    def get(self, uri, params=None, data=None):
        return self.do_request('GET', uri, params, data)

    def post(self, uri, params=None, data=None):
        return self.do_request('POST', uri, params, data)

    def put(self, uri, params=None, data=None):
        return self.do_request('PUT', uri, params, data)

    def delete(self, uri, params=None, data=None):
        return self.do_request('DELETE', uri, params, data)

    def activate_version(self, version):
        response = self.put(self.path(version, '/activate'))
        body = response.json()
        if response.status_code == 404:
            raise Exception('Cannot find version to activate {} for service {}'.format(version, self.service_id))
        elif response.status_code != 200:
            msg = 'Failed activating version with status code {}. Message: {}'.format(response.status_code, body['msg'])
            raise Exception(msg)
        return True

    def get_active_version(self):
        response = self.get(self.path(suffix='/version'))
        body = response.json()
        active_version = None
        for version_obj in body:
            if version_obj['active']:
                active_version = version_obj['number']
        return active_version

    def clone_version(self, version):
        """
        Clones the current active Fastly configuration version
        Returns the version number (int)
        """
        response = self.put(self.path(version, '/clone'))
        return response.json()['number']

    def create_syslog(self, version, syslog_vcl):
        """
        Create syslog configuration on the Fastly configuration version (int).
        Returns nothing.
        """
        response = self.post(self.path(version, 'logging/syslog'), params=syslog_vcl)
        if response.status_code == 409:
            raise Exception('syslog already exists')
        elif response.status_code >= 400:
            raise Exception('failed to create syslog. Error: {}'.format(response.json()))
        return response.json()

    def delete_syslog(self, version, name):
        response = self.delete(self.path(version, '/logging/syslog/{}'.format(name)))
        if response.status_code == 404:
            return False
        if response.status_code >= 400:
            raise Exception('failed to delete syslog {}. Error: {}'.format(name, response.json()))
        return response.json()

    def get_all_custom_vcls(self, version):
        response = self.get(self.path(version, '/vcl'))
        return response.json()

    def create_custom_vcl(self, version, vcl):
        response = self.post(self.path(version, '/vcl'), data=urlencode(vcl))
        if response.status_code == 409:
            raise Exception('custom vcl {} already exists'.format(vcl['name']))
        elif response.status_code >= 400:
            raise Exception('failed to create custom vcl {}. Error: {}'.format(vcl['name'], response.json()))
        return response.json()

    def delete_custom_vcl(self, version, name):
        response = self.delete(self.path(version, '/vcl/{}'.format(name)))
        if response.status_code == 404:
            return False
        if response.status_code >= 400:
            raise Exception('failed to delete custom vcl {}. Error: {}'.format(name, response.json()))
        return response.json()

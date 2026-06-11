#!/usr/local/bin/python
import json
import httplib2
import configparser

config = configparser.ConfigParser()
config.read('config.py')
facebook = config['facebook']
print(facebook)

class apiToolFacebookGraph:
    def __init__(self):
        self.key = facebook.get('fb_access_token')


    def get_user_info(self, handle):
        print(handle)
        service_url = 'username,fan_count,talking_about_count'
        try:
            fb_json = self._get_json(handle, service_url)
            return fb_json
        except Exception as e:
            print('ERROR processing handle {0)'.format(handle))
            print(str(e))


    def _get_json(self, handle, service_url):
        # service_url: username, fan_count, talking_about_count

        apiUrl = 'https://graph.facebook.com/v2.10/{0}'.format(handle) + \
                '?fields={0}'.format(service_url) + \
                '&access_token=' + self.key

        h = httplib2.Http()
        resp, content = h.request(apiUrl, 'GET')
        result = json.loads(content)
        return result

import requests
import os


def _get_base_url():
    base_url_by_env = {
        'staging': 'https://api.staging.napari-hub.org',
        'prod': 'https://api.napari-hub.org'
    }
    prefix = os.getenv('PREFIX')
    if prefix in base_url_by_env:
        return base_url_by_env.get(prefix)
    elif not prefix:
        return 'http://localhost:12345'

    return f'https://api.dev.napari-hub.org/{prefix}'


base_url = _get_base_url()
headers = {'User-Agent': 'bdd-test'}


def verify_response_status_code(context, status_code):
    actual = context['response'].status_code
    assert int(status_code) == actual, f'status code of {actual} was not expected'


def call_api(context, endpoint):
    url = f'{base_url}{endpoint}'
    context['response'] = requests.get(url, headers=headers)


def valid_str(value):
    return value and value.strip()

import io
import json
import logging
import mimetypes
import os
import os.path
import time
from datetime import datetime
from io import StringIO
from typing import Union, IO, List, Dict, Any

import boto3
import pandas as pd
from botocore.client import Config
from botocore.exceptions import ClientError
from utils.utils import send_alert
from utils.time import print_perf_duration

# Environment variable set through ecs stack terraform module
bucket = os.environ.get('BUCKET')
bucket_path = os.environ.get('BUCKET_PATH', '')
endpoint_url = os.environ.get('BOTO_ENDPOINT_URL', None)

s3_client = boto3.client("s3", endpoint_url=endpoint_url, config=Config(max_pool_connections=50))


def get_cache(key: str) -> Union[Dict, List, None]:
    """
    Get the cached json file or manifest file for a given key if exists, None otherwise.

    :param key: key to the cache to get
    :return: file content for the key if exists, None otherwise
    """
    try:
        start = time.perf_counter()
        result = json.loads(s3_client.get_object(Bucket=bucket, Key=os.path.join(bucket_path, key))['Body'].read())
        print_perf_duration(start, f"get_cache({key})")
        return result
    except ClientError:
        print(f"Not cached: {key}")
        return None


def cache(content: Union[dict, list, IO[bytes]], key: str, mime: str = None):
    """
    Cache the given content to the key location.

    :param content: content to cache
    :param key: key path in s3
    :param mime: type of the file
    """
    extra_args = None
    mime = mime or mimetypes.guess_type(key)[0]
    if mime:
        extra_args = {'ContentType': mime}
    if bucket is None:
        send_alert(f"({datetime.now()}) Unable to find bucket for lambda "
                   f"configuration, skipping caching for napari hub."
                   f"Check terraform setup to add environment variable for "
                   f"napari hub lambda")
        return content
    if isinstance(content, io.IOBase):
        s3_client.upload_fileobj(Fileobj=content, Bucket=bucket,
                                 Key=os.path.join(bucket_path, key), ExtraArgs=extra_args)
    else:
        with io.BytesIO(json.dumps(content).encode('utf8')) as stream:
            s3_client.upload_fileobj(Fileobj=stream, Bucket=bucket,
                                     Key=os.path.join(bucket_path, key), ExtraArgs=extra_args)


def _get_complete_path(path):
    return os.path.join(bucket_path, path)


def write_data(data: str, path: str):
    s3_client.put_object(Body=data, Bucket=bucket, Key=_get_complete_path(path))


def _get_from_s3(path):
    return s3_client.get_object(Bucket=bucket, Key=_get_complete_path(path))['Body'].read().decode('utf-8')


def get_install_timeline_data(plugin):
    """
    Read activity dashboard install data from s3

    :param plugin: plugin name
    :return: dataframe that consists of plugin-specific data for activity_dashboard backend endpoints
    """
    plugin_installs_dataframe = pd.read_csv(StringIO(_get_from_s3("activity_dashboard_data/plugin_installs.csv")))
    plugin_df = plugin_installs_dataframe[plugin_installs_dataframe.PROJECT == plugin]
    plugin_df = plugin_df[['MONTH', 'NUM_DOWNLOADS_BY_MONTH']]
    plugin_df['MONTH'] = pd.to_datetime(plugin_df['MONTH'])
    return plugin_df


def _load_json_from_s3(path: str) -> Dict:
    """
    Load activity dashboard .json file from s3

    :param path: path to file in s3
    :return: dictionary that consists of path-specific data for activity_dashboard backend endpoints
    """
    try:
        return json.loads(_get_from_s3(path))
    except Exception as e:
        logging.error(e)
        return {}


def get_recent_activity_data() -> Dict:
    return _load_json_from_s3("activity_dashboard_data/recent_installs.json")


def get_latest_commit(plugin: str) -> Any:
    return _load_json_from_s3("activity_dashboard_data/latest_commits.json").get(plugin)


def get_commit_activity(plugin: str) -> List:
    return _load_json_from_s3("activity_dashboard_data/commit_activity.json").get(plugin, [])

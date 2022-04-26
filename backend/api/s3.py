import io
import json
import os
import os.path
from datetime import datetime
from typing import Union, IO, List, Dict
import mimetypes

import boto3
import yaml
from botocore.exceptions import ClientError
from botocore.client import Config

from utils.utils import send_alert

# Environment variable set through ecs stack terraform module
bucket = os.environ.get('BUCKET')
bucket_path = os.environ.get('BUCKET_PATH', '')
endpoint_url = os.environ.get('BOTO_ENDPOINT_URL', None)

s3_client = boto3.client("s3", endpoint_url=endpoint_url, config=Config(max_pool_connections=50))


def get_cache(key: str, format: str = 'json') -> Union[Dict, List, None]:
    """
    Get the cached json file or manifest file for a given key if exists, None otherwise.

    :param key: key to the cache to get
    :param format: Format of the file to obtain
    :return: file content for the key if exists, None otherwise
    """
    try:
        if format == 'json':
            return json.loads(s3_client.get_object(Bucket=bucket, Key=os.path.join(bucket_path, key))['Body'].read())
        elif format == 'yaml':
            return yaml.safe_load(s3_client.get_object(Bucket=bucket, Key=os.path.join(bucket_path, key))['Body'])
    except ClientError:
        print(f"Not cached: {key}")
        return None


def write_cache_manifest(content: dict, key: str):
    """
    Cache the given content to the key location in yaml format

    :param key: key path in s3
    :param content: content to cache
    """

    extra_args = None
    if bucket is None:
        send_alert(f"({datetime.now()}) Unable to find bucket for lambda "
                   f"configuration, skipping caching for napari hub."
                   f"Check terraform setup to add environment variable for "
                   f"napari hub lambda")
        return content
    with io.BytesIO(yaml.dump(content).encode('utf8')) as stream:
        s3_client.upload_fileobj(Fileobj=stream, Bucket=bucket,
                                 Key=os.path.join(bucket_path, key), ExtraArgs=extra_args)


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

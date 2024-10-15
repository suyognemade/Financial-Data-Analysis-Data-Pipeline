from airflow.hooks.base import BaseHook
from airflow.exceptions import AirflowNotFoundException
import requests
import json
from minio import Minio
from io import BytesIO

Bucket_Name = 'stock-market'

def _get_minio_client():
    minio = BaseHook.get_connection('minio')
    print(minio)
    client = Minio(
        endpoint = minio.extra_dejson['endpoint_url'].split('//')[1],
        access_key = minio.login,
        secret_key = minio.password,
        secure = False
    )
    return client

def _get_stock_prices(url, symbol):
    url = f"{url}{symbol}?metrics=high?&interval=1d&range=1y"
    api = BaseHook.get_connection('stock_api')
    response = requests.get(url, headers = api.extra_dejson['headers'])
    return json.dumps(response.json()['chart']['result'][0])

def _store_prices(stock):
    client = _get_minio_client()
    minio = BaseHook.get_connection('minio')
    print(minio)
    client = Minio(
        endpoint = minio.extra_dejson['endpoint_url'].split('//')[1],
        access_key = minio.login,
        secret_key = minio.password,
        secure = False
    )
    if not client.bucket_exists(Bucket_Name):
        client.make_bucket(Bucket_Name)
    stock = json.loads(stock)
    symbol = stock ['meta']['symbol']
    data = json.dumps(stock, ensure_ascii = False).encode('utf8')
    objw = client.put_object(
        bucket_name = Bucket_Name,
        object_name = f'{symbol}/prices.json',
        data = BytesIO(data),
        length = len(data)
    )
    return f'{objw.bucket_name}/{symbol}'

def _get_formatted_csv(path):
    client = _get_minio_client()
    prefix_name = f"{path.split('/')[1]}/formatted_prices/"
    objects = client.list_objects(Bucket_Name, prefix = prefix_name, recursive = True)
    for obj in objects:
        if obj.object_name.endswith('.csv'):
            return obj.object_name
    raise AirflowNotFoundException('The csv file does not exists')
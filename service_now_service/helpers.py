import logging
import os
import pysnow
import requests

from dataclasses import dataclass
from flask_jwt_extended import get_raw_jwt
from functools import reduce
from operator import and_
from pysnow import QueryBuilder
from pysnow.criterion import Criterion, Field, Order, Table as SN_Table
from typing import Any, Sequence, Union

from techlock.common.api import NotFoundException
from techlock.common.config import AuthInfo, ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class SN_Config:
    host: str
    user: str
    password: str


class Table(SN_Table):

    def __init__(
        self,
        name: str,
        sn_config: SN_Config,
    ):
        super(Table, self).__init__(name)
        self.host = sn_config.host
        self.auth = (sn_config.user, sn_config.password)

    def _get_url(self, sys_id: str = None, stats: bool = False):
        type_ = 'stats' if stats else 'table'

        if sys_id:
            return f'https://{self.host}/api/now/{type_}/{self.table_name}/{sys_id}'
        else:
            return f'https://{self.host}/api/now/{type_}/{self.table_name}'

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        query: Any = None,
        fields: Sequence[str] = None,
        display_value: Union[str, bool] = False,
        exclude_reference_link: bool = True,
        params: dict = None
    ):
        params = params.copy() if params else dict()

        if limit:
            params['sysparm_limit'] = limit
        if offset:
            params['sysparm_offset'] = offset
        if query:
            params['sysparm_query'] = str(query)
        if fields:
            params['sysparm_fields'] = ','.join(fields)
        if display_value is not None:
            params['sysparm_display_value'] = display_value
        if exclude_reference_link is not None:
            params['sysparm_exclude_reference_link'] = exclude_reference_link

        url = self._get_url()
        response = requests.get(url, auth=self.auth, params=params)

        if response.status_code != 200:
            logger.error('Failed to list Service Now object.', extra={
                'table_name': self.table_name,
                'status': response.status_code,
                'headers': response.headers,
                'error_response': response.json()
            })
            raise Exception('Failed to list Service Now object.')

        return response

    def post(self, data: dict, params: dict = None):
        url = self._get_url()
        response = requests.post(url, json=data, auth=self.auth, params=params)

        if response.status_code != 201:
            logger.error('Failed to post Service Now object.', extra={
                'table_name': self.table_name,
                'data': data,
                'status': response.status_code,
                'headers': response.headers,
                'error_response': response.json()
            })
            raise Exception('Failed to post Service Now object.')

        return response

    def get(self, sys_id: str, params: dict = None):
        url = self._get_url(sys_id=sys_id)
        response = requests.get(url, auth=self.auth, params=params)

        if response.status_code == 404:
            raise NotFoundException(f'No record found with id: {sys_id}')
        elif response.status_code != 200:
            logger.error('Failed to get Service Now object.', extra={
                'table_name': self.table_name,
                'sys_id': sys_id,
                'status': response.status_code,
                'headers': response.headers,
                'error_response': response.json()
            })
            raise Exception('Failed to get Service Now object.')

        return response

    def put(self, sys_id: str, data: dict, params: dict = None):
        url = self._get_url(sys_id=sys_id)
        response = requests.put(url, json=data, auth=self.auth, params=params)

        if response.status_code == 404:
            raise NotFoundException(f'No record found with id: {sys_id}')
        elif response.status_code != 200:
            logger.error('Failed to put Service Now object.', extra={
                'table_name': self.table_name,
                'sys_id': sys_id,
                'data': data,
                'status': response.status_code,
                'headers': response.headers,
                'error_response': response.json()
            })
            raise Exception('Failed to put Service Now object.')

        return response

    def delete(self, sys_id: str, params: dict = None):
        url = self._get_url(sys_id=sys_id)
        response = requests.delete(url, auth=self.auth)

        if response.status_code == 404:
            raise NotFoundException(f'No record found with id: {sys_id}')
        elif response.status_code != 204:
            logger.error('Failed to delete Service Now object.', extra={
                'table_name': self.table_name,
                'sys_id': sys_id,
                'status': response.status_code,
                'headers': response.headers,
                'error_response': response.json()
            })
            raise Exception('Failed to delete Service Now object.')

        return response

    def stats(
        self,
        query: Any = None,
        count: bool = False,
        display_value: bool = False,
        exclude_reference_link: bool = True,
        params: dict = None
    ):
        params = params.copy() if params else dict()

        if query:
            params['sysparm_query'] = str(query)
        if count is not None:
            params['sysparm_count'] = count
        if display_value is not None:
            params['sysparm_display_value'] = display_value
        if exclude_reference_link is not None:
            params['sysparm_exclude_reference_link'] = exclude_reference_link

        url = self._get_url(stats=True)
        response = requests.get(url, auth=self.auth, params=params)

        if response.status_code != 200:
            logger.error('Failed to list Service Now object.', extra={
                'table_name': self.table_name,
                'status': response.status_code,
                'headers': response.headers,
                'error_response': response.json()
            })
            raise Exception('Failed to list Service Now object.')

        return response


def get_sn_config(current_user: AuthInfo) -> SN_Config:
    sn_config = SN_Config(
        host=ConfigManager().get(current_user, 'api_host', raise_if_not_found=True),
        user=ConfigManager().get(current_user, 'api_user', raise_if_not_found=True),
        password=ConfigManager().get(current_user, 'api_password', raise_if_not_found=True),
    )

    return sn_config


def get_sn_client(current_user: AuthInfo):
    sn_config = get_sn_config(current_user)

    sn_client = pysnow.Client(user=sn_config.user, password=sn_config.password, host=sn_config.host)

    return sn_client


def sort_sn_result(query: Union[QueryBuilder, Criterion], sort_string: str):
    if isinstance(query, QueryBuilder):
        return sort_sn_result_qb(query, sort_string)
    elif isinstance(query, Criterion):
        return sort_sn_result_c(query, sort_string)
    else:
        raise Exception(f'Invalid query type: {type(query)}')


def sort_sn_result_c(query: Criterion, sort_string: str):
    sort_fields = sort_string.split(',')

    def get_order_field(sort_str):
        sort_direction = sort_str.split(':')[1]
        if sort_direction:
            column = sort_str.split(':')[0]
            if sort_direction == 'asc':
                return Field(column).order(Order.asc)
            elif sort_direction == 'desc':
                return Field(column).order(Order.desc)
        else:
            return Field(sort_str).order(Order.asc)

    order_fields = [get_order_field(sf) for sf in sort_fields]
    if order_fields:
        query &= reduce(and_, order_fields)

    return query


def sort_sn_result_qb(query: QueryBuilder, sort_string: str):
    sort_fields = sort_string.split(',')

    for (idx, field) in enumerate(sort_fields):
        sort_direction = field.split(':')[1]
        if sort_direction:
            column = field.split(':')[0]
            if sort_direction == 'asc':
                query.field(column).order_ascending()
            elif sort_direction == 'desc':
                query.field(column).order_descending()
        else:
            query.field(field).order_ascending()

        if idx != len(sort_fields) - 1:
            query.AND()

    return query


def get_sn_customer_id():
    try:
        if os.environ.get('SN_CUSTOMER_ID'):
            return os.environ.get('SN_CUSTOMER_ID')

        return get_raw_jwt()['service_now_customer_id']
    except KeyError:
        return {"error": "You don't have ServiceNow ID"}, 400

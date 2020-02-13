import logging
import pysnow

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api.jwt_authorization import (
    access_required,
    # get_request_claims,
)

from ..models import (
    ClientListQueryParameters, ClientListQueryParametersSchema,
    CLIENT_CLAIM_SPEC,
)
from ..helpers import get_sn_client, sort_sn_result

logger = logging.getLogger(__name__)

blp = Blueprint('clients', __name__, url_prefix='/clients')


@blp.route('')
class Clients(MethodView):

    @blp.arguments(ClientListQueryParametersSchema, location='query')
    @access_required(
        'read', CLIENT_CLAIM_SPEC.resource_name,
        allowed_filter_fields=CLIENT_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: ClientListQueryParameters):
        current_user = get_current_user()
        # claims = get_request_claims()

        sn_client = get_sn_client(current_user)
        account_table = sn_client.resource(api_path='/table/customer_account', base_path='/api/now')

        query = (
            pysnow.QueryBuilder()
        )

        if query_params.sort:
            query = sort_sn_result(query, query_params.sort)

        resp = account_table.get(
            query=query,
            offset=query_params.offset,
            limit=query_params.limit,
            fields=['name', 'sys_created_on', 'sys_id']
        )

        return {
            'items': resp.all(),
            'num_items': len(resp.all()),
            'total_items': int(resp._response.headers.get('X-Total-Count')),
        }

import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api.jwt_authorization import (
    access_required,
    # get_request_claims,
)

from ..models import (
    AssignmentGroupListQueryParameters, AssignmentGroupListQueryParametersSchema,
    ASSIGNMENT_GROUP_CLAIM_SPEC,
)
from ..helpers import get_sn_config, sort_sn_result, get_sn_customer_id, Table

logger = logging.getLogger(__name__)

blp = Blueprint('assignment_groups', __name__, url_prefix='/assignment-groups')


@blp.route('')
class AssignmentGroups(MethodView):

    @blp.arguments(AssignmentGroupListQueryParametersSchema, location='query')
    @access_required(
        'read', ASSIGNMENT_GROUP_CLAIM_SPEC.resource_name,
        allowed_filter_fields=ASSIGNMENT_GROUP_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: AssignmentGroupListQueryParameters):
        current_user = get_current_user()
        # claims = get_request_claims()
        sn_config = get_sn_config(current_user)
        sn_customer_id = get_sn_customer_id()

        user_groups = Table('sys_user_group', sn_config=sn_config)
        query = user_groups.company == sn_customer_id

        if query_params.sort:
            query = sort_sn_result(query, query_params.sort)

        # Service Now handles `limit==0` as if there was no limit.
        # We want to handle `limit==0` as a limit of 0. (only return a total count of items)
        resp = user_groups.get_all(
            query=query,
            limit=query_params.limit if query_params.limit != 0 else 1,
            offset=query_params.offset,
            display_value='false',
            exclude_reference_link=True,
            fields=['name', 'description', 'sys_id', 'parent'],
        )

        raw_items = resp.json().get('result')
        items = list()
        if query_params.limit != 0:
            items = [raw_item for raw_item in raw_items]

        return {
            'items': items,
            'num_items': len(items),
            'total_items': int(resp.headers.get('X-Total-Count')),
        }

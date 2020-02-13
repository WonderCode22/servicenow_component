import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user, jwt_required
from flask_smorest import Blueprint

from ..helpers import get_sn_config, Table

logger = logging.getLogger(__name__)

blp = Blueprint('ui_data', __name__, url_prefix='/ui-data')


@blp.route('/incidents')
class IncidentUIData(MethodView):

    @jwt_required
    def get(self):
        current_user = get_current_user()
        # claims = get_request_claims()
        sn_config = get_sn_config(current_user)

        sys_choice = Table('sys_choice', sn_config=sn_config)
        query = (
            sys_choice.inactive.eq('false')
            & sys_choice.name.eq('incident')
            | sys_choice.name.eq('task')
        )

        resp = sys_choice.get_all(
            query=query,
            fields=[
                'element',
                'value',
                'label',
                'language',
                'dependent_value'
            ],
            limit=1000
        )

        raw_items = resp.json().get('result')

        return {
            'items': raw_items,
            'num_items': len(raw_items),
        }

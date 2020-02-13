import logging
import pytz
from datetime import timedelta
from datetime import datetime

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api.jwt_authorization import (
    access_required,
)
from techlock.common.util.helper import log_execution_time

from ..models import (
    TimeSeriesQueryParameters, TimeSeriesQueryParametersSchema,
    TIMESERIES_CLAIM_SPEC,
)
from ..helpers import get_sn_config, get_sn_customer_id, Table

logger = logging.getLogger(__name__)

blp = Blueprint('timeseries', __name__, url_prefix='/timeseries')


@blp.route('/open_incidents')
class Incidents(MethodView):

    def _get_dates_tuple(self, incident):
        opened_at = datetime.fromisoformat(incident['opened_at'])
        closed_at = datetime.fromisoformat(incident['closed_at']) if incident['closed_at'] else None

        if opened_at.tzinfo is None:
            opened_at = opened_at.replace(tzinfo=pytz.UTC)

        if closed_at and closed_at.tzinfo is None:
            closed_at = closed_at.replace(tzinfo=pytz.UTC)

        return (opened_at, closed_at)

    @blp.arguments(TimeSeriesQueryParametersSchema, location='query')
    @access_required(
        'read', TIMESERIES_CLAIM_SPEC.resource_name,
        allowed_filter_fields=TIMESERIES_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: TimeSeriesQueryParameters):
        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        customer_id = get_sn_customer_id()

        with log_execution_time(logger, message='Took: %(human_time)s to get the data from Service Now.'):
            # Get a count of all items that are open for the entire time window.
            incident = Table('incident', sn_config=sn_config)
            stat_query = (
                incident.company.eq(customer_id)
                & incident.opened_at.lt(query_params.start_date)
                & incident.closed_at.gt(query_params.end_date)
                | incident.closed_at.is_empty()
            )

            resp = incident.stats(
                query=stat_query,
                count=True,
            )

            base_count = int(resp.json()['result']['stats']['count'])

            # Now get all other items that were either opened or closed during the timewindow
            incident_time_series = []
            limit = 10000
            idx = 0
            while True:
                offset = idx * limit
                incident_query = (
                    incident.company.eq(customer_id)
                    & incident.closed_at.between(query_params.start_date, query_params.end_date)
                    | incident.opened_at.between(query_params.start_date, query_params.end_date)
                )

                resp = incident.get_all(
                    limit=limit,
                    offset=offset,
                    query=incident_query,
                    fields=['opened_at', 'closed_at'],
                    display_value=False,
                    exclude_reference_link=True,
                )

                incident_time_series = incident_time_series + resp.json()['result']

                total_count = int(resp.headers.get('X-Total-Count'))
                if offset + limit >= total_count:
                    break
                idx += 1

        incident_dates = [self._get_dates_tuple(x) for x in incident_time_series]
        result = {}
        from_date = query_params.start_date
        while from_date <= query_params.end_date:
            # default interval is 'day'
            to_date = from_date + timedelta(days=1)

            # if interval is 'month', to_date is get by adding 1 month to from_date
            if query_params.interval != 'day':
                pass

            data_count = len([x for x in incident_dates if x[0] <= to_date and (x[1] is None or x[1] >= from_date)])

            if query_params.as_epoch is True:
                date = int(to_date.timestamp())
            else:
                date = to_date.strftime("%Y-%m-%dT%H:%M")

            result[date] = base_count + data_count
            from_date = to_date

        return result

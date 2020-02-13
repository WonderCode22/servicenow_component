import logging
from datetime import datetime

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api import NotFoundException
from techlock.common.api.jwt_authorization import (
    access_required,
    # get_request_claims,
)

from ..models import (
    WriteIncident, IncidentSchema,
    IncidentListQueryParameters, IncidentListQueryParametersSchema,
    PostIncidentComment, PostIncidentCommentSchema,
    PostIncidentWorkNote, PostIncidentWorkNoteSchema,
    INCIDENT_CLAIM_SPEC,
)
from ..helpers import get_sn_config, sort_sn_result, get_sn_customer_id, Table

logger = logging.getLogger(__name__)

blp = Blueprint('incidents', __name__, url_prefix='/incidents')


def _dump_incident(raw_incident):
    # Clean up the response.
    # We want display_values with actual values for some fields, but not others.
    # i.e.: for `opened_by` we want the name and id, but for `opened_at` we want the utc time in military format, not a localized one with 'AM/PM'
    # TODO: create mapping api so we can return only 'value'
    # display_value_fields = (
    #     'opened_by',
    #     'closed_by',
    #     'reopened_by',
    #     'resolved_by',
    #     'caller_id',
    #     'assignment_group',
    #     'assigned_to',
    #     'company',
    #     'sys_domain',
    # )
    # get_value = lambda k, v: v if k in display_value_fields else v['value']
    # return {k: get_value(k, v) for k, v in raw_item.items()}
    return raw_incident


def _dump_comment(raw_comment):
    return raw_comment


def _validate_user_has_access_to_incident(incident_id):
    current_user = get_current_user()
    sn_customer_id = get_sn_customer_id()
    sn_config = get_sn_config(current_user)
    incident = Table('incident', sn_config=sn_config)

    resp = incident.get(
        sys_id=incident_id,
        params={
            'sysparm_display_value': 'false',
            'sysparm_exclude_reference_link': 'true',
            'sysparm_fields': 'company'
        }
    )
    raw_item = resp.json().get('result')
    if raw_item['company'] != sn_customer_id:
        raise NotFoundException(f'No record found with id: {incident_id}')


@blp.route('')
class Incidents(MethodView):

    @blp.arguments(IncidentListQueryParametersSchema, location='query')
    @access_required(
        'read', INCIDENT_CLAIM_SPEC.resource_name,
        allowed_filter_fields=INCIDENT_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: IncidentListQueryParameters):
        current_user = get_current_user()
        # claims = get_request_claims()
        sn_config = get_sn_config(current_user)
        sn_customer_id = get_sn_customer_id()

        incident = Table('incident', sn_config=sn_config)
        query = incident.company == sn_customer_id
        if query_params.sort:
            query = sort_sn_result(query, query_params.sort)

        if query_params.start_date:
            end_date = datetime.today()
            if query_params.end_date:
                end_date = query_params.end_date
            query &= incident.opened_at <= end_date
            query &= incident.closed_at >= query_params.start_date
            query |= incident.closed_at.is_empty()

        filters = query_params.get_sn_filters()
        for f in filters:
            query &= f

        # Service Now handles `limit==0` as if there was no limit.
        # We want to handle `limit==0` as a limit of 0. (only return a total count of items)
        resp = incident.get_all(
            query=query,
            limit=query_params.limit if query_params.limit != 0 else 1,
            offset=query_params.offset,
            display_value='all',
            exclude_reference_link=True,
        )

        raw_items = resp.json().get('result')
        items = list()
        if query_params.limit != 0:
            for raw_item in raw_items:
                items.append(_dump_incident(raw_item))

        return {
            'items': items,
            'num_items': len(items),
            'total_items': int(resp.headers.get('X-Total-Count')),
        }

    @blp.arguments(IncidentSchema)
    @access_required(
        'create', INCIDENT_CLAIM_SPEC.resource_name,
        allowed_filter_fields=INCIDENT_CLAIM_SPEC.filter_fields
    )
    def post(self, data: WriteIncident):
        current_user = get_current_user()
        sn_customer_id = get_sn_customer_id()

        sn_config = get_sn_config(current_user)
        incident = Table('incident', sn_config=sn_config)

        resp = incident.post(
            data={
                'company': sn_customer_id,
                # 'opened_by': current_user,  # TODO!
                'short_description': data.short_description,
                'assignment_group': data.assignment_group,
                'category': data.category,
                'subcategory': data.subcategory,
                'impact': data.impact,
                'urgency': data.urgency
            }
        )

        raw_item = resp.json().get('result')
        return _dump_incident(raw_item)


@blp.route('/<incident_id>')
class IncidentById(MethodView):

    @access_required(
        'read', INCIDENT_CLAIM_SPEC.resource_name,
        allowed_filter_fields=INCIDENT_CLAIM_SPEC.filter_fields
    )
    def get(self, incident_id: str):
        current_user = get_current_user()
        sn_customer_id = get_sn_customer_id()
        sn_config = get_sn_config(current_user)
        incident = Table('incident', sn_config=sn_config)

        display_value = 'all'
        resp = incident.get(
            sys_id=incident_id,
            params={
                'sysparm_display_value': display_value,
                'sysparm_exclude_reference_link': 'true'
            }
        )
        raw_item = resp.json().get('result')
        company = raw_item['company']['value'] if display_value in (True, 'true', 'all') else raw_item['company']
        if company != sn_customer_id:
            raise NotFoundException(f'No record found with id: {incident_id}')

        return _dump_incident(raw_item)

    @blp.arguments(IncidentSchema)
    @access_required(
        'update', INCIDENT_CLAIM_SPEC.resource_name,
        allowed_filter_fields=INCIDENT_CLAIM_SPEC.filter_fields
    )
    def put(self, data: WriteIncident, incident_id: str):
        _validate_user_has_access_to_incident(incident_id)

        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        incident = Table('incident', sn_config=sn_config)

        resp = incident.put(
            sys_id=incident_id,
            data={
                'short_description': data.short_description,
                'assignment_group': data.assignment_group,
                'category': data.category,
                'subcategory': data.subcategory,
                'impact': data.impact,
                'urgency': data.urgency
            },
            params={
                'sysparm_display_value': 'all',
                'sysparm_exclude_reference_link': 'true'
            }
        )
        raw_item = resp.json().get('result')
        return _dump_incident(raw_item)

    @blp.response(code=204)
    @access_required(
        'delete', INCIDENT_CLAIM_SPEC.resource_name,
        allowed_filter_fields=INCIDENT_CLAIM_SPEC.filter_fields
    )
    def delete(self, incident_id: str):
        _validate_user_has_access_to_incident(incident_id)

        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        incident = Table('incident', sn_config=sn_config)

        incident.delete(
            sys_id=incident_id,
        )
        return


@blp.route('/<incident_id>/comments')
class IncidentComments(MethodView):

    @access_required(
        'read', INCIDENT_CLAIM_SPEC.resource_name,
    )
    def get(self, incident_id: str):
        _validate_user_has_access_to_incident(incident_id)

        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        journals = Table('sys_journal_field', sn_config=sn_config)

        display_value = 'all'
        resp = journals.get_all(
            query=(
                journals.element_id.eq(incident_id)
                & journals.element.eq('comments')
            ),
            params={
                'sysparm_display_value': display_value,
                'sysparm_exclude_reference_link': 'true'
            }
        )
        raw_items = resp.json().get('result')
        items = [_dump_comment(raw_item) for raw_item in raw_items]

        return {
            'items': items,
            'num_items': len(items),
        }

    @blp.arguments(PostIncidentCommentSchema)
    @access_required(
        'update', INCIDENT_CLAIM_SPEC.resource_name,
    )
    def post(self, data: PostIncidentComment, incident_id: str):
        _validate_user_has_access_to_incident(incident_id)

        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        journals = Table('sys_journal_field', sn_config=sn_config)

        resp = journals.post(
            data={
                'element_id': incident_id,
                'name': 'incident',
                'element': 'comments',
                'value': data.value
            }
        )
        raw_item = resp.json().get('result')
        return _dump_comment(raw_item)


@blp.route('/<incident_id>/work-notes')
class IncidentWorkNotes(MethodView):

    @access_required(
        'read', INCIDENT_CLAIM_SPEC.resource_name,
    )
    def get(self, incident_id: str):
        _validate_user_has_access_to_incident(incident_id)

        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        journals = Table('sys_journal_field', sn_config=sn_config)

        display_value = 'all'
        resp = journals.get_all(
            query=(
                journals.element_id.eq(incident_id)
                & journals.element.eq('work_notes')
            ),
            params={
                'sysparm_display_value': display_value,
                'sysparm_exclude_reference_link': 'true'
            }
        )
        raw_items = resp.json().get('result')
        items = [_dump_comment(raw_item) for raw_item in raw_items]

        return {
            'items': items,
            'num_items': len(items),
        }

    @blp.arguments(PostIncidentWorkNoteSchema)
    @access_required(
        'update', INCIDENT_CLAIM_SPEC.resource_name,
    )
    def post(self, data: PostIncidentWorkNote, incident_id: str):
        _validate_user_has_access_to_incident(incident_id)

        current_user = get_current_user()
        sn_config = get_sn_config(current_user)
        journals = Table('sys_journal_field', sn_config=sn_config)

        resp = journals.post(
            data={
                'element_id': incident_id,
                'name': 'incident',
                'element': 'work_notes',
                'value': data.value
            }
        )
        raw_item = resp.json().get('result')
        return _dump_comment(raw_item)

import marshmallow as ma
import marshmallow.fields as mf
import operator as op

from dataclasses import dataclass, fields
from datetime import datetime
from pysnow.criterion import Field

from techlock.common.api import (
    BadRequestException,
    ClaimSpec,
    OffsetPageableQueryParameters, OffsetPageableQueryParametersSchema,
    SortableQueryParameters, SortableQueryParametersSchema,
)

from .datefilter import (DatetimeQueryParameters, DatetimeQueryParametersSchema)

INCIDENT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete'
    ],
    resource_name='incidents',
    filter_fields=[]
)


# TODO: move to common.
def get_own_fields(cls, memoize=True):
    '''
        Get's a dataclass's own (uninherited) fields.

        If you expect to call this multiple times you can memoize it,
        in which case it'll be saved as a class var, which will be returned next time it's called.
    '''
    if hasattr(cls, '__uninherited_fields__'):
        return getattr(cls, '__uninherited_fields__')

    inherited_fields = [
        f for base in cls.__bases__
        for f in fields(base)
    ]

    uninherited_fields = [
        f for f in fields(cls)
        if f not in inherited_fields
    ]

    if memoize:
        setattr(cls, '__uninherited_fields__', uninherited_fields)

    return uninherited_fields


def get_numeric_filter(value: str, field):
    '''
        Gets numeric or date filter from string value.

        Args:
            value (str): A string value. May start with '<=,>=,<, or >'
            field (any): A field object that we can apply an operation on. Examples are pypika fields, and pysnow fields.
        Returns:
            (any): A criterion object. Examples are pypika Criterion, and pysnow Criterion.
    '''
    if value.startswith('>='):
        f = op.ge(field, value[2:])
    elif value.startswith('<='):
        f = op.le(field, value[2:])
    elif value.startswith('>'):
        f = op.gt(field, value[1:])
    elif value.startswith('<'):
        f = op.lt(field, value[1:])
    else:
        f = field == value

    return f


def get_sn_string_filter(value: str, field: Field):
    # Service Now supports limited wildcards
    if value.count('*') > 1:
        # If more than 1 wildcard, we can't process it
        raise BadRequestException(f'{field.name} contains multiple wildcards. May only contain one at the start or end.')
    elif value.endswith('*'):
        return field.ends_with(value[:-1])
    elif value.startswith('*'):
        return field.starts_with(value[1:])
    else:
        return field.eq(value)


##################################
# List
##################################
class IncidentListQueryParametersSchema(
    OffsetPageableQueryParametersSchema,
    SortableQueryParametersSchema,
    DatetimeQueryParametersSchema,
):
    sort = mf.String(missing='opened_at:desc')

    sys_id = mf.String()
    name = mf.String()
    number = mf.String()
    short_description = mf.String()
    escalation = mf.String()
    state = mf.String()
    opened_at = mf.DateTime()
    closed_at = mf.DateTime()
    assigned_to = mf.String()
    resolved_by = mf.String()

    @ma.post_load
    def make_object(self, data, **kwargs):
        return IncidentListQueryParameters(**data)


@dataclass
class IncidentListQueryParameters(
    OffsetPageableQueryParameters,
    SortableQueryParameters,
    DatetimeQueryParameters,
):
    sort: str = 'opened_at:desc'  # default to

    sys_id: str = None
    name: str = None
    number: str = None
    short_description: str = None
    escalation: str = None
    state: str = None
    opened_at: datetime = None
    closed_at: datetime = None
    assigned_to: str = None
    resolved_by: str = None

    def get_sn_filters(self):
        filters = list()

        for field in get_own_fields(self.__class__):
            value = getattr(self, field.name)
            if value is None:
                continue

            if field.type == str:
                filters.append(get_sn_string_filter(value, Field(field.name)))
            elif field.type == datetime or field.type in (int, float):
                filters.append(get_numeric_filter(value, Field(field.name)))
            else:
                raise Exception(f'Unexpected type: {field.type}, field: {field.name}')

        return filters


##################################
# Single Item
##################################
class IncidentSchema(ma.Schema):
    short_description = mf.String(required=True)

    assignment_group = mf.String(required=False)

    category = mf.String(required=False)
    subcategory = mf.String(required=False)

    impact = mf.Integer(required=False)
    urgency = mf.Integer(required=False)

    # dump only fields (GET requests)
    company = mf.String(dump_only=True)
    opened_by = mf.String(dump_only=True)

    @ma.post_load
    def make_object(self, data, **kwargs):
        return WriteIncident(**data)


@dataclass
class WriteIncident:
    short_description: str

    assignment_group: str

    category: str
    subcategory: str

    impact: int
    urgency: int

    # Dump only fields
    company: str = None
    opened_by: str = None

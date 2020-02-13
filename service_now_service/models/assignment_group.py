from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf

from techlock.common.api import (
    ClaimSpec,
    OffsetPageableQueryParameters, OffsetPageableQueryParametersSchema,
    SortableQueryParameters, SortableQueryParametersSchema
)


ASSIGNMENT_GROUP_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read',
    ],
    resource_name='assignment-groups',
    filter_fields=[]
)


class AssignmentGroupSortableQueryParametersSchema(SortableQueryParametersSchema):
    name = mf.String()
    sys_id = mf.String()


class AssignmentGroupListQueryParametersSchema(
    OffsetPageableQueryParametersSchema,
    AssignmentGroupSortableQueryParametersSchema,
):
    @ma.post_load
    def make_object(self, data, **kwargs):
        return AssignmentGroupListQueryParameters(**data)


@dataclass
class AssignmentGroupListQueryParameters(
    OffsetPageableQueryParameters,
    SortableQueryParameters,
):
    pass

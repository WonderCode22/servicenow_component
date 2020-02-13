from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf

from techlock.common.api import (
    ClaimSpec,
    OffsetPageableQueryParameters, OffsetPageableQueryParametersSchema,
    SortableQueryParameters, SortableQueryParametersSchema
)


CLIENT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read',
    ],
    resource_name='clients',
    filter_fields=[]
)


class ClientSortableQueryParametersSchema(SortableQueryParametersSchema):
    name = mf.String()
    sys_id = mf.String()


class ClientListQueryParametersSchema(
    OffsetPageableQueryParametersSchema,
    ClientSortableQueryParametersSchema,
):
    @ma.post_load
    def make_object(self, data, **kwargs):
        return ClientListQueryParameters(**data)


@dataclass
class ClientListQueryParameters(
    OffsetPageableQueryParameters,
    SortableQueryParameters,
):
    pass

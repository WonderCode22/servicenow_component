from dataclasses import dataclass
from enum import Enum

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField

from techlock.common.api import (
    ClaimSpec
)

from .datefilter import (
    DatetimeQueryParameters, DatetimeQueryParametersSchema
)


TIMESERIES_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read',
    ],
    resource_name='timeseries',
    filter_fields=[]
)


class Interval(Enum):
    day = 1


@dataclass
class TimeSeriesQueryParameters(
    DatetimeQueryParameters
):
    interval: Interval = Interval.day
    as_epoch: bool = True


class TimeSeriesQueryParametersSchema(
    DatetimeQueryParametersSchema,
):
    interval = EnumField(Interval)
    as_epoch = mf.Boolean(default=True, missing=True, allow_none=True)

    @ma.post_load
    def make_object(self, data, **kwargs):
        return TimeSeriesQueryParameters(**data)

from datetime import datetime
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import pytz


class DatetimeQueryParametersSchema(ma.Schema):
    start_date = mf.DateTime(required=True)
    end_date = mf.DateTime(required=True)

    @ma.validates_schema
    def validate_dateformat(self, data, **kwargs):
        if not data.get('start_date'):
            return

        errors = {}
        # Can't compare tz naive and aware datetimes, so make everything UTC.
        start_date = data['start_date'].astimezone(pytz.UTC)
        today = datetime.now(pytz.UTC)

        if data.get('end_date'):
            end_date = data['end_date'].astimezone(pytz.UTC)
        else:
            end_date = today

        if start_date > end_date:
            errors['start_date'] = ['start_date should be less than end_date']

        if errors:
            raise ma.ValidationError(errors)

    @ma.post_load
    def convert_to_utc(self, data, **kwargs):
        # If not timezone is specified, add the UTC timezone
        if data['start_date'].tzinfo is None:
            data['start_date'] = data['start_date'].replace(tzinfo=pytz.UTC)

        if data['end_date'].tzinfo is None:
            data['end_date'] = data['end_date'].replace(tzinfo=pytz.UTC)

        return data


@dataclass
class DatetimeQueryParameters:
    start_date: datetime = None
    end_date: datetime = None

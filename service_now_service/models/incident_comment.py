import marshmallow as ma
import marshmallow.fields as mf

from dataclasses import dataclass


class PostIncidentCommentSchema(ma.Schema):
    value = mf.String(required=True)

    @ma.post_load
    def make_object(self, data, **kwargs):
        return PostIncidentComment(**data)


@dataclass
class PostIncidentComment:
    value: str

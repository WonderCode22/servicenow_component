import marshmallow as ma
import marshmallow.fields as mf

from dataclasses import dataclass


class PostIncidentWorkNoteSchema(ma.Schema):
    value = mf.String(required=True)

    @ma.post_load
    def make_object(self, data, **kwargs):
        return PostIncidentWorkNote(**data)


@dataclass
class PostIncidentWorkNote:
    value: str

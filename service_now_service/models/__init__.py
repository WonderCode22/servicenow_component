from .assignment_group import (
    AssignmentGroupListQueryParameters, AssignmentGroupListQueryParametersSchema,
    ASSIGNMENT_GROUP_CLAIM_SPEC,
)

from .client import (
    ClientListQueryParameters, ClientListQueryParametersSchema,
    CLIENT_CLAIM_SPEC,
)
from .incident import (
    WriteIncident, IncidentSchema,
    IncidentListQueryParameters, IncidentListQueryParametersSchema,
    INCIDENT_CLAIM_SPEC,
)
from .incident_comment import (
    PostIncidentComment, PostIncidentCommentSchema,
)
from .incident_work_note import (
    PostIncidentWorkNote, PostIncidentWorkNoteSchema,
)

from .timeseries import (
    TimeSeriesQueryParameters, TimeSeriesQueryParametersSchema,
    TIMESERIES_CLAIM_SPEC,
)

ALL_CLAIM_SPECS = [
    ASSIGNMENT_GROUP_CLAIM_SPEC,
    CLIENT_CLAIM_SPEC,
    INCIDENT_CLAIM_SPEC,
    TIMESERIES_CLAIM_SPEC
]

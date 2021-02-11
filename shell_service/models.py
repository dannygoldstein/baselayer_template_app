import sqlalchemy as sa
from sqlalchemy.orm import relationship

from baselayer.app.models import AccessibleIfUserMatches, Base, User, init_db

from enum import Enum

JOB_STATES = ("READY", "RUNNING", "COMPLETE", "FAILED", "SERVER_ERROR")
job_states = sa.Enum(*JOB_STATES, name="job_states", validate_strings=True)
py_job_states = Enum("job_states", JOB_STATES)
sqla_enum_types = [job_states]


class Job(Base):
    """A job (shell script) to run serverside."""

    # Record access controls: except for admins only the submitter can
    # update, delete, or trigger a job for execution. any user can read job
    # records even if they didnt submit the job. admins can update, delete,
    # or execute any job
    update = delete = execute = AccessibleIfUserMatches("submitter")

    id = sa.Column(sa.Text, primary_key=True, doc="Job ID (name).")
    submitter_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        doc="User ID of the job submitter..",
    )
    submitter = relationship(
        "User", doc="The User that submitted this job.", back_populates="jobs"
    )
    code = sa.Column(sa.Text, doc="The content of the shell script to execute.")
    status = sa.Column(job_states, default="READY", doc="Status of the job.")
    return_code = sa.Column(sa.Integer, doc="Return code of the executed script.")
    stdout = sa.Column(
        sa.Text,
        doc="stdout produced by the completed job.",
    )
    stderr = sa.Column(
        sa.Text,
        doc="stderr produced by the completed job.",
    )


User.jobs = relationship("Job", back_populates="submitter")

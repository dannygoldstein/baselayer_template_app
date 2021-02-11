"""Test fixture configuration."""

import pytest
import uuid
from baselayer.app.models import ACL, DBSession

from .fixtures import UserFactory, JobFactory
from ..model_util import create_token


acl = ACL.create_or_get("System admin")
DBSession().add(acl)
DBSession().commit()


@pytest.fixture()
def super_admin_user():
    return UserFactory(acls=[acl])


@pytest.fixture()
def user():
    return UserFactory()


@pytest.fixture()
def user_token(user):
    token_id = create_token(ACLs=[], user_id=user.id, name=str(uuid.uuid4()))
    return token_id


@pytest.fixture()
def super_admin_user_token(super_admin_user):
    token_id = create_token(
        ACLs=["System admin"], user_id=super_admin_user.id, name=str(uuid.uuid4())
    )
    return token_id


@pytest.fixture()
def user_hello_world_job(user):
    return JobFactory(submitter=user)

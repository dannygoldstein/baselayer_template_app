"""Test fixture configuration."""

import pytest
import os
import pathlib
from baselayer.app.config import load_config
from baselayer.app.test_util import set_server_url

import uuid

from baselayer.app import models
from baselayer.app.models import ACL, DBSession

from .fixtures import UserFactory, JobFactory
from ..model_util import create_token


print("Loading test configuration from test_config.yaml")
basedir = pathlib.Path(os.path.dirname(__file__)) / "../.."
cfg = load_config([basedir / "test_config.yaml"])
set_server_url(f'http://localhost:{cfg["ports.app"]}')
models.init_db(**cfg["database"])

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

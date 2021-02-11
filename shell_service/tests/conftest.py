"""Test fixture configuration."""

import pytest
import os
import pathlib
from baselayer.app.config import load_config
from baselayer.app.test_util import set_server_url

from baselayer.app import models
from baselayer.app.models import ACL, DBSession

from .fixtures import UserFactory, JobFactory


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
def user_hello_world_job(user):
    return JobFactory(submitter=user)

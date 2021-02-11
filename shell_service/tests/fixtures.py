from shell_service.models import Job, User
from baselayer.app.models import DBSession, init_db
from baselayer.app.config import load_config
from baselayer.app.env import load_env
from baselayer.app.test_util import set_server_url

import pathlib
import os

from tempfile import mkdtemp

import factory
import uuid


TMP_DIR = mkdtemp()
env, cfg = load_env()

print("Loading test configuration from _test_config.yaml")
basedir = pathlib.Path(os.path.dirname(__file__))
cfg = load_config([(basedir / "../../test_config.yaml").absolute()])
set_server_url(f'http://localhost:{cfg["ports.app"]}')
print("Setting test database to:", cfg["database"])
init_db(**cfg["database"])


class BaseMeta:
    sqlalchemy_session = DBSession()
    sqlalchemy_session_persistence = "commit"


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = User

    username = factory.LazyFunction(lambda: str(uuid.uuid4()))
    contact_email = factory.LazyFunction(lambda: f"{uuid.uuid4().hex[:10]}@gmail.com")
    first_name = factory.LazyFunction(lambda: f"{uuid.uuid4().hex[:4]}")
    last_name = factory.LazyFunction(lambda: f"{uuid.uuid4().hex[:4]}")

    @factory.post_generation
    def acls(obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for acl in extracted:
                obj.acls.append(acl)
                DBSession().add(obj)
                DBSession().commit()


class JobFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Job

    submitter = factory.SubFactory(UserFactory)
    code = """
#!/usr/bin/env bash
echo "hello world!"
"""

import json

from baselayer.app.app_server import handlers as baselayer_handlers
from shell_service import openapi
from shell_service.app_server import shell_service_handlers

spec = openapi.spec_from_handlers(baselayer_handlers + shell_service_handlers)

with open("openapi.yml", "w") as f:
    f.write(spec.to_yaml())

with open("openapi.json", "w") as f:
    json.dump(spec.to_dict(), f)

print("OpenAPI spec written to openapi.{yml,json}")

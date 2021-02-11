import tornado.web
from . import models, model_util, openapi
from .handlers.job import JobHandler, ExecutionHandler


def make_app(cfg, baselayer_handlers, baselayer_settings, process=None, env=None):
    """Create and return a `tornado.web.Application` object with specified
    handlers and settings.

    Parameters
    ----------
    cfg : Config
        Loaded configuration.  Can be specified with '--config'
        (multiple uses allowed).
    baselayer_handlers : list
        Tornado handlers needed for baselayer to function.
    baselayer_settings : cfg
        Settings needed for baselayer to function.
    process : int
        When launching multiple app servers, which number is this?
    env : dict
        Environment in which the app was launched.  Currently only has
        one key, 'debug'---true if launched with `--debug`.

    """
    if cfg["cookie_secret"] == "abc01234":
        print("!" * 80)
        print("  Your server is insecure. Please update the secret string ")
        print("  in the configuration file!")
        print("!" * 80)

    handlers = baselayer_handlers + [
        #    (r'/some_url(/.*)?', MyTornadoHandler),
        (r"/jobs", JobHandler),
        (r"/execute", ExecutionHandler),
    ]

    settings = baselayer_settings
    settings.update({})  # Specify any additional Tornado settings here

    app = tornado.web.Application(handlers, **settings)
    models.init_db(**cfg["database"])

    if process == 0:
        model_util.create_tables(add=env.debug)
    model_util.refresh_enums()
    model_util.setup_permissions()
    app.cfg = cfg

    admin_token = model_util.provision_token()
    with open(".tokens.yaml", "w") as f:
        f.write(f"INITIAL_ADMIN: {admin_token.id}\n")
    with open(".tokens.yaml", "r") as f:
        print("-" * 78)
        print("Tokens in .tokens.yaml:")
        print("\n".join(f.readlines()), end="")
        print("-" * 78)

    app.openapi_spec = openapi.spec_from_handlers(handlers)

    return app

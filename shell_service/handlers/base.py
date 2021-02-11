from baselayer.app.handlers.base import BaseHandler as BaselayerHandler
from .. import __version__


class BaseHandler(BaselayerHandler):
    @property
    def associated_user_object(self):
        if hasattr(self.current_user, "username"):
            return self.current_user
        return self.current_user.created_by

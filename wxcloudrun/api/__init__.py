from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# 触发路由注册
from wxcloudrun.api import core  # noqa: F401
from wxcloudrun.api import kf  # noqa: F401
from wxcloudrun.api import media  # noqa: F401
from wxcloudrun.api import suite  # noqa: F401
from wxcloudrun.api import enterpriseConta  # noqa: F401
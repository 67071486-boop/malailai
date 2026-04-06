from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# 触发路由注册
from wecom.api import core  # noqa: F401
from wecom.api import externalcontact  # noqa: F401
from wecom.api import kf  # noqa: F401
from wecom.api import media  # noqa: F401
from wecom.api import suite  # noqa: F401
from wecom.api import enterpriseConta  # noqa: F401
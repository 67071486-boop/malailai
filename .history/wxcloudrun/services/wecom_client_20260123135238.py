"""兼容入口：沿用 wecom_client 导出的 API，但内部拆分为子模块。"""
from wxcloudrun.services.wecom import (
    BaseClient,
    WeComApiError,
    SuiteApi,
    CorpAuthApi,
    ContactApi,
    MessageApi,
    SuiteClient,
    get_suite_client,
    get_corp_client,
    fetch_suite_access_token,
    fetch_corp_access_token,
    CorpClient,
    fetch_auth_info,
    fetch_pre_auth_code,
    fetch_app_permissions,
    fetch_corp_token,
)


__all__ = [
    "BaseClient",
    "WeComApiError",
    "SuiteApi",
    "CorpAuthApi",
    "ContactApi",
    "MessageApi",
    "SuiteClient",
    "CorpClient",
    "get_suite_client",
    "get_corp_client",
    "fetch_suite_access_token",
    "fetch_corp_access_token",
    "fetch_auth_info",
    "fetch_pre_auth_code",
    "fetch_app_permissions",
    "fetch_corp_token",
]

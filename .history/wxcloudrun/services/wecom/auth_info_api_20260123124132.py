"""DEPRECATED: auth_info_api moved into app_auth_api.AppAuthApi.

This module is kept for backward compatibility but should not be used.
Importing it will raise an ImportError to force callers to use the merged API.
"""
raise ImportError("auth_info_api has been merged into app_auth_api; use wxcloudrun.services.wecom.get_app_auth_api() or fetch_auth_info() instead")

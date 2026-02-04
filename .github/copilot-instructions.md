# Copilot Instructions — wxcloudrun-flask

## Big picture (architecture + data flow)
- Flask entry: run.py and wxcloudrun/__init__.py; HTTP routes in wxcloudrun/views.py, WeCom routes in wxcloudrun/wxwork.py (Blueprint /wxwork), and REST APIs in wxcloudrun/api/* via api_bp.
- App bootstrap: wxcloudrun/__init__.py registers blueprints, config, CORS, scheduler, and calls ensure_indexes() for Mongo collections.
- MongoDB access is centralized in wxcloudrun/dao.py (PyMongo). DAO returns plain dicts; DB name is config.MONGO_DB_NAME (defaults to "demo").
- WeCom callbacks: wxcloudrun/services/callback_service.py verifies GET via WXBizMsgCrypt.VerifyURL; POST decrypts XML and dispatches by InfoType/Event/MsgType.
- Business dispatch: wxcloudrun/services/biz/dispatcher.py routes to handlers registered in wxcloudrun/services/biz/__init__.py.
- Token flow: wxcloudrun/services/token_service.py uses token_cache (in-memory) plus wecom_client fetchers.
- Background scheduler: wxcloudrun/services/scheduler/ starts APScheduler and runs sync_service.sync_tick every 5 minutes.

## Local workflow
- Install deps: pip install -r requirements.txt
- Run: python run.py 127.0.0.1 5000 (host + port required)
- Required env: MONGO_URI, MONGO_DB_NAME (optional override), WXWORK_CORP_ID, WXWORK_SUITE_ID, WXWORK_SUITE_SECRET, WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY
- Optional env: WXWORK_OAUTH_REDIRECT for /wxwork/oauth/login redirects

## Project-specific conventions
- All DB reads/writes go through wxcloudrun/dao.py helpers (e.g., query_counterbyid, update_corp_auth); do not use PyMongo in views/services.
- API responses must use wxcloudrun/response.py helpers: make_succ_response, make_err_response, make_succ_empty_response.
- Counter flow in wxcloudrun/views.py uses new_counter() and stores timestamps in UTC when updating.
- Callback handling must always return "success" on POST after decrypt/dispatch (errors are logged but do not break the callback).
- To add a new WeCom event handler, implement BizHandler and register it in wxcloudrun/services/biz/__init__.py.
- CORS rules are enforced in wxcloudrun/__init__.py; keep API routes under /api/* and origins in sync with the allowlist.

## Concrete examples
- Batch update corp auths: /api/update_corp_auths in wxcloudrun/views.py uses fetch_auth_info() and update_corp_auth().
- OAuth: /wxwork/oauth/* in wxcloudrun/wxwork.py uses suite_access_token from token_service.

## Key integration points
- WeCom crypto: wxcloudrun/wechat_official/WXBizMsgCrypt.py (pycryptodome) for URL verification + message decrypt/encrypt.
- Templates: wxcloudrun/templates/index.html serves the root page; additional debug pages exist (kf_test.html, media_test.html).
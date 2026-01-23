#!/usr/bin/env python3
import json
import traceback

from wxcloudrun.services.wecom_client import fetch_auth_info
from wxcloudrun.dao import query_corp_auth, insert_corp_auth, update_corp_auth
from wxcloudrun.model import new_corp_auth

# 目标企业信息（来自用户提供的数据）
CORP_ID = "wpiUIVIQAAhhQ4K5PTHPOSaWQ0q0VBcw"
PERMANENT_CODE = "Ez_I2woO4faim4XQt6pCyEMRyNSv6bdJaPGuQeE075w"

print(f"Starting fetch for corp_id={CORP_ID}", flush=True)

try:
    v2 = fetch_auth_info(CORP_ID, PERMANENT_CODE)
    print("Fetched v2 auth info:", json.dumps(v2, ensure_ascii=False), flush=True)
except Exception as e:
    print("fetch_auth_info failed:", e, flush=True)
    traceback.print_exc()
    raise

try:
    corp_auth = query_corp_auth(CORP_ID)
    if corp_auth:
        corp_auth["permanent_code"] = PERMANENT_CODE
        corp_auth["auth_corp_info"] = json.dumps(v2)
        update_corp_auth(corp_auth)
        print(f"Updated existing corp_auth for {CORP_ID}", flush=True)
    else:
        doc = new_corp_auth(corp_id=CORP_ID, permanent_code=PERMANENT_CODE, auth_corp_info=json.dumps(v2))
        insert_corp_auth(doc)
        print(f"Inserted new corp_auth for {CORP_ID}", flush=True)
except Exception as e:
    print("DB save failed:", e, flush=True)
    traceback.print_exc()
    raise

print("Done.", flush=True)

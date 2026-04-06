from datetime import datetime, timezone
from typing import Optional

from wecom.dao import query_kf_cursor, upsert_kf_cursor
from wecom.model import new_kf_cursor


class KfCursorStore:
    def load(self, open_kfid: str) -> Optional[str]:
        doc = query_kf_cursor(open_kfid)
        if not doc:
            return None
        return doc.get("cursor")

    def save(self, open_kfid: str, cursor: Optional[str], corp_id: Optional[str] = None) -> None:
        if not cursor:
            return
        doc = query_kf_cursor(open_kfid)
        if doc:
            doc["cursor"] = cursor
            doc["updated_at"] = datetime.now(timezone.utc)
        else:
            doc = new_kf_cursor(open_kfid, cursor, corp_id=corp_id)
        upsert_kf_cursor(doc)

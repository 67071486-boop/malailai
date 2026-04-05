import re
import string

__all__ = ["validate_password", "is_valid_password"]


def validate_password(password: str):
    """验证密码是否满足要求。

    规则：
    - 必须包含至少一个大写字母
    - 必须包含至少一个小写字母
    - 长度 8 到 32 个字符（包含）
    - 必须包含数字或特殊字符（两者至少其一）

    返回 (bool, str) — (是否通过, 错误信息(通过时为空字符串))
    """
    if not isinstance(password, str):
        return False, "密码必须是字符串"

    length = len(password)
    if length < 8 or length > 32:
        return False, "密码长度必须在 8 到 32 个字符之间"

    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"

    if not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"

    has_digit = bool(re.search(r"\d", password))
    special_chars = re.escape(string.punctuation)
    has_special = bool(re.search(r"[" + special_chars + r"]", password))
    if not (has_digit or has_special):
        return False, "密码必须包含数字或特殊字符（至少其一）"

    return True, ""


def is_valid_password(password: str) -> bool:
    """简单布尔接口，便于快速检查。"""
    ok, _ = validate_password(password)
    return ok

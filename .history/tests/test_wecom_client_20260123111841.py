import types

from wxcloudrun.services import wecom_client


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, resp_data=None):
        self.resp_data = resp_data or {}

    def post(self, url, json=None, timeout=None):
        return FakeResponse(self.resp_data)

    def get(self, url, params=None, timeout=None):
        return FakeResponse(self.resp_data)


def test_get_permanent_code_success():
    # 模拟 token 可用
    wecom_client.get_suite_client  # ensure module loaded
    wecom_client.get_suite_client  # no-op
    # 替换模块级的 get_suite_access_token
    wecom_client.get_suite_client().get_suite_access_token = lambda: 'DUMMY'

    fake_data = {"permanent_code": "PC123456", "auth_corp_info": {"corpid": "CORPID"}}
    fake_session = FakeSession(resp_data=fake_data)
    sc = wecom_client.SuiteClient(session=fake_session)
    data = sc.get_permanent_code('AUTHCODE')
    assert data.get('permanent_code') == 'PC123456'


def test_getuserinfo3rd_success():
    wecom_client.get_suite_client().get_suite_access_token = lambda: 'DUMMY'
    fake_data = {"UserId": "user1", "DeviceId": "dev1"}
    fake_session = FakeSession(resp_data=fake_data)
    sc = wecom_client.SuiteClient(session=fake_session)
    data = sc.getuserinfo3rd('CODE')
    assert data.get('UserId') == 'user1'

"""测试脚本：调用本地运行的 Flask 应用的 /api/department/simplelist 接口。

用法:
  python scripts/test_department_simplelist.py --url http://127.0.0.1:5000 --token YOUR_TOKEN [--id 1]

"""
import argparse
import requests
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='应用基地址，例如 http://127.0.0.1:5000')
    parser.add_argument('--token', required=True, help='access_token 用于测试')
    parser.add_argument('--id', type=int, default=None, help='部门 id（可选）')
    args = parser.parse_args()

    endpoint = args.url.rstrip('/') + '/api/department/simplelist'
    payload = {'access_token': args.token}
    if args.id is not None:
        payload['id'] = args.id
    try:
        resp = requests.post(endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        print('HTTP', resp.status_code)
        print(resp.text)
    except Exception as e:
        print('请求失败:', e)
        sys.exit(2)


if __name__ == '__main__':
    main()

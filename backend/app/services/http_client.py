import requests


def api_post(url, headers, json, timeout=30):
    """统一的 JSON POST 请求。返回 (response_json, error_string)。"""
    try:
        resp = requests.post(url, headers=headers, json=json, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


def api_get(url, headers, timeout=10):
    """统一的 JSON GET 请求。返回 (response_json, error_string)。"""
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)

import json
import requests


def stream_chat(api_url, api_key, model, messages, response_format, cancel_event):
    url = api_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if response_format and response_format != "text":
        payload["response_format"] = {"type": response_format}

    try:
        resp = requests.post(
            url, headers=headers, json=payload, stream=True, timeout=120
        )
        resp.raise_for_status()

        for line in resp.iter_lines():
            if cancel_event.is_set():
                yield {"stopped": True}
                resp.close()
                return

            if not line:
                continue

            line_str = line.decode("utf-8") if isinstance(line, bytes) else line
            if not line_str.startswith("data: "):
                continue

            data_str = line_str[6:]
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield {"delta": delta}
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        yield {"done": True}

    except requests.RequestException as e:
        yield {"error": str(e)}

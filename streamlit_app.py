from __future__ import annotations

import json
import time
import uuid
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api/v1/agent"


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent_id" not in st.session_state:
        st.session_state.agent_id = "main"
    if "api_base" not in st.session_state:
        st.session_state.api_base = API_BASE
    if "session" not in st.session_state:
        st.session_state.session = requests.Session()
    if "backend_session_id" not in st.session_state:
        st.session_state.backend_session_id = str(uuid.uuid4())
    if "last_session_id" not in st.session_state:
        st.session_state.last_session_id = None
    if "use_stream" not in st.session_state:
        st.session_state.use_stream = False


def send_chat(message: str, agent_id: str) -> dict:
    payload = {
        "message": message,
        "agent_id": agent_id,
        "stream": False,
        "session_id": st.session_state.backend_session_id,
    }
    resp = st.session_state.session.post(
        f"{st.session_state.api_base}/chat",
        json=payload,
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()

    sid = (data.get("data") or {}).get("session_id")
    if sid:
        st.session_state.backend_session_id = sid
        st.session_state.last_session_id = sid

    return data


def send_chat_stream(message: str, agent_id: str):
    payload = {
        "message": message,
        "agent_id": agent_id,
        "session_id": st.session_state.backend_session_id,
    }
    resp = st.session_state.session.post(
        f"{st.session_state.api_base}/chat/stream",
        json=payload,
        stream=True,
        timeout=300,
    )

    if resp.status_code == 409:
        raise RuntimeError("Session is busy. Please switch off stream mode and send again (queued).")

    resp.raise_for_status()

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        yield event


def abort_chat() -> dict:
    resp = st.session_state.session.post(
        f"{st.session_state.api_base}/abort",
        json={"session_id": st.session_state.backend_session_id},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def poll_result(request_id: str, timeout_sec: int = 120) -> dict:
    start = time.time()
    while time.time() - start < timeout_sec:
        resp = st.session_state.session.get(
            f"{st.session_state.api_base}/chat/result",
            params={"request_id": request_id},
            timeout=30,
        )
        resp.raise_for_status()

        data = (resp.json() or {}).get("data", {})
        state = data.get("state")
        if state in ("done", "error", "aborted", "not_found"):
            return data

        time.sleep(0.8)

    return {"state": "timeout"}


init_state()

st.set_page_config(page_title="Local Memory Tool", page_icon="💬", layout="wide")
st.title("Local Memory Tool Chat")

with st.sidebar:
    st.header("Settings")
    st.session_state.api_base = st.text_input("API Base", value=st.session_state.api_base)
    st.session_state.agent_id = st.text_input("Agent ID", value=st.session_state.agent_id)
    st.session_state.use_stream = st.checkbox("Use stream mode", value=st.session_state.use_stream)

    st.divider()
    st.caption(f"Frontend session_id: {st.session_state.backend_session_id}")
    if st.session_state.last_session_id:
        st.caption(f"Backend session_id: {st.session_state.last_session_id}")

    if st.button("Abort Current Task", use_container_width=True):
        try:
            result = abort_chat()
            data = result.get("data", {})
            partial_output = data.get("partial_output", "")
            cleared_queue = data.get("cleared_queue", 0)

            if partial_output:
                st.session_state.messages.append({"role": "assistant", "content": partial_output})

            st.success(f"Aborted. Cleared queued requests: {cleared_queue}")
            st.rerun()
        except Exception as e:
            st.error(f"Abort failed: {e}")

    if st.button("New Session", use_container_width=True):
        st.session_state.backend_session_id = str(uuid.uuid4())
        st.session_state.last_session_id = None
        st.session_state.messages = []
        st.rerun()

    if st.button("Clear Chat UI Only", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        try:
            if st.session_state.use_stream:
                assistant_text = ""
                for event in send_chat_stream(user_input, st.session_state.agent_id):
                    et = event.get("type")
                    if et == "token":
                        assistant_text += event.get("content", "")
                        placeholder.markdown(assistant_text if assistant_text else "_")
                    elif et == "error":
                        raise RuntimeError(event.get("error", "stream error"))
                    elif et == "done":
                        break

                content = assistant_text if assistant_text else "_No response_"
                placeholder.markdown(content)
                st.session_state.messages.append({"role": "assistant", "content": content})

            else:
                result = send_chat(user_input, st.session_state.agent_id)

                code = result.get("code", 500)
                msg = result.get("message", "unknown")
                data = result.get("data", {})

                session_id = data.get("session_id")
                if session_id:
                    st.session_state.last_session_id = session_id
                    st.session_state.backend_session_id = session_id

                if code == 202 or msg == "queued":
                    req_id = data.get("request_id")
                    placeholder.markdown(
                        f"Message queued.\n\nPosition: {data.get('position')}\n\n{data.get('detail', '')}"
                    )

                    if req_id:
                        final_data = poll_result(req_id)
                        state = final_data.get("state")

                        if state == "done":
                            content = final_data.get("content", "")
                        elif state == "aborted":
                            content = final_data.get("content", "") or "Task aborted."
                        elif state == "error":
                            content = f"Queued task error: {final_data.get('error', 'unknown')}"
                        elif state == "timeout":
                            content = "Queued task timed out while waiting."
                        else:
                            content = f"Queued task state: {state}"

                        content = content if content else "_No response_"
                        placeholder.markdown(content)
                        st.session_state.messages.append({"role": "assistant", "content": content})
                    else:
                        content = "Queued but no request_id returned."
                        placeholder.markdown(content)
                        st.session_state.messages.append({"role": "assistant", "content": content})

                elif msg == "aborted":
                    content = data.get("response", "") or "Task aborted."
                    placeholder.markdown(content)
                    st.session_state.messages.append({"role": "assistant", "content": content})

                else:
                    content = data.get("response", "") or "_No response_"
                    placeholder.markdown(content)
                    st.session_state.messages.append({"role": "assistant", "content": content})

        except Exception as e:
            error_text = f"Request failed: {e}"
            placeholder.error(error_text)
            st.session_state.messages.append({"role": "assistant", "content": error_text})

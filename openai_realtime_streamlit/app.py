import asyncio
import json
import time
from asyncio import run_coroutine_threadsafe
from threading import Thread

import streamlit as st

from constants import (AUTOSCROLL_SCRIPT, DOCS,
                       HIDE_STREAMLIT_RUNNING_MAN_SCRIPT, OAI_LOGO_URL)
from utils import SimpleRealtime


st.set_page_config(layout="wide")


if "logs" not in st.session_state:
    st.session_state.logs = []


@st.cache_resource(show_spinner=False)
def create_loop():
    """
    Creates an event loop we can globally cache and then run in a
    separate thread.  Many, many thanks to
    https://handmadesoftware.medium.com/streamlit-asyncio-and-mongodb-f85f77aea825
    for this tip.  NOTE: globally cached resources are shared across all users
    and sessions, so this is only okay for a local R&D app like this.
    """
    loop = asyncio.new_event_loop()
    thread = Thread(target=loop.run_forever)
    thread.start()
    return loop, thread

st.session_state.event_loop, worker_thread = create_loop()


def run_async(coroutine):
    """
    Helper for running an async function in the globally cached event loop we
    just created.
    """
    return run_coroutine_threadsafe(coroutine, st.session_state.event_loop).result()


@st.cache_resource(show_spinner=False)
def setup_client():
    """
    Globally cached SimpleRealtime client.
    """
    if client := st.session_state.get("client"):
        return client
    return SimpleRealtime(event_loop=st.session_state.event_loop, debug=True)

st.session_state.client = setup_client()


@st.fragment(run_every=1)
def logs_text_area():
    logs = st.session_state.client.logs

    if st.session_state.show_full_events:
        for _, _, log in logs:
            st.json(log, expanded=False)
    else: 
        for time, event_type, log in logs:
            if event_type == "server":
                st.write(f"{time}\t:green[↓ server] {json.loads(log)['type']}")
            else:
                st.write(f"{time}\t:blue[↑ client] {json.loads(log)['type']}")
    st.components.v1.html(AUTOSCROLL_SCRIPT, height=0)


def st_app():
    """
    Our main streamlit app function.
    """
    st.markdown(HIDE_STREAMLIT_RUNNING_MAN_SCRIPT, unsafe_allow_html=True)

    main_tab, docs_tab = st.tabs(["Console", "Docs"])

    with main_tab:
        st.markdown(f"<img src='{OAI_LOGO_URL}' width='30px'/>   **realtime console**", unsafe_allow_html=True)

        with st.sidebar:
            if st.button("Connect", type="primary"):
                with st.spinner("Connecting..."):
                    try:
                        run_async(st.session_state.client.connect())
                        if st.session_state.client.is_connected():
                            st.success("Connected to OpenAI Realtime API")
                        else:
                            st.error("Failed to connect to OpenAI Realtime API")
                    except Exception as e:
                        st.error(f"Error connecting to OpenAI Realtime API: {str(e)}")

        st.session_state.show_full_events = st.checkbox("Show Full Event Payloads", value=False)
        with st.container(height=300, key="logs_container"):
            logs_text_area()

        _ = st.text_area("Enter your message:", key = "input_text_area", height=200)
        def clear_input_cb():
            """
            Callback that will clear our message input box after the user
            clicks the send button.
            """
            st.session_state.last_input = st.session_state.input_text_area
            st.session_state.input_text_area = ""

        if st.button("Send", on_click=clear_input_cb, type="primary"):
            if st.session_state.get("last_input"):
                try:
                    event = json.loads(st.session_state.get("last_input"))
                    with st.spinner("Sending message..."):
                        st.session_state.client.send(event["type"], {"item": event["item"]} if "item" in event else {})
                    st.success("Message sent successfully")
                except json.JSONDecodeError:
                    st.error("Invalid JSON input. Please check your message format.")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
            else:
                st.warning("Please enter a message before sending.")

    with docs_tab:
        st.markdown(DOCS)


if __name__ == '__main__':
    st_app()
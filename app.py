import asyncio
import json
import time
from asyncio import run_coroutine_threadsafe
from threading import Thread

import streamlit as st

from utils import SimpleRealtime


st.set_page_config(layout="wide")


if "logs" not in st.session_state:
    st.session_state.logs = []

def get_event_loop():
    return asyncio.new_event_loop()


@st.cache_resource(show_spinner=False)
def create_loop():
    loop = asyncio.new_event_loop()
    thread = Thread(target=loop.run_forever)
    thread.start()
    return loop, thread

st.session_state.event_loop, worker_thread = create_loop()

def run_async(coroutine):
    return run_coroutine_threadsafe(coroutine, st.session_state.event_loop).result()


@st.cache_resource(show_spinner=False)
def setup_client():
    if client := st.session_state.get("client"):
        return client
    return SimpleRealtime(event_loop=st.session_state.event_loop, debug=True)


st.session_state.client = setup_client()


@st.fragment(run_every=1)
def logs_text_area():
    scroll_script = """
<script>
    let lastScrollHeight = 0;
    let userHasScrolledUp = false;

    function autoScroll() {
        const streamlitDoc = window.parent.document;
        const textArea = streamlitDoc.getElementsByClassName('st-key-logs_container')[0];
        const scrollArea = textArea.parentElement.parentElement;
        
        // Check if content height has changed
        if (scrollArea.scrollHeight !== lastScrollHeight) {
            // Only auto-scroll if user hasn't scrolled up
            if (!userHasScrolledUp) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
            lastScrollHeight = scrollArea.scrollHeight;
        }

        // Detect if user has scrolled up
        const isScrolledToBottom = scrollArea.scrollHeight - scrollArea.scrollTop <= scrollArea.clientHeight + 50; // 50px threshold
        userHasScrolledUp = !isScrolledToBottom;
    }

    // Run auto-scroll check periodically
    setInterval(autoScroll, 500);
</script>
    """

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
    st.components.v1.html(scroll_script, height=0)


def st_app():
    st.title("OpenAI Realtime Chat")

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
    
    st.session_state.show_full_events = st.checkbox("Show Full Events", value=False)
    with st.container(height=300, key="logs_container"):
        logs_text_area()

    _ = st.text_area("Enter your message:", key = "input_text_area", height=200)
    def clear_input_cb():
        st.session_state.last_input = st.session_state.input_text_area
        st.session_state.input_text_area = ""

    # Send button
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



if __name__ == '__main__':
    st_app()
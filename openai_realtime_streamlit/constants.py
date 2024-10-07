# thanks claude for this lovely js that autoscrolls when a new message is added,
# but also allows the user to scroll backwards without it snapping back down
AUTOSCROLL_SCRIPT = """
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

HIDE_STREAMLIT_RUNNING_MAN_SCRIPT = """
<style>
    div[data-testid="stStatusWidget"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
</style>
"""

OAI_LOGO_URL = "https://raw.githubusercontent.com/openai/openai-realtime-console/refs/heads/main/public/openai-logomark.svg"

EVENT_1_JSON = """
```
{
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": "This is the way the world ends..."
            }
        ]
    }
}
```
"""

EVENT_2_JSON = """
```
{
    "type": "response.create"
}
```
"""

EVENT_3_JSON = """
```
{
    "type": "session.update",
    "session": {
        "voice": "echo",
        "instructions": "Always answer like an angry pirate."
    }
}
```
"""

DOCS = f"""
First, make sure that your OpenAI API key is set in the environment variable `OPENAI_API_KEY`.  Then click the `Connect` button.
Send raw json event payloads by pasting them in the input text area and clicking `Send`.  You should then see events streaming in the logs area.
As a test, trying sending:

{EVENT_1_JSON}

followed by:

{EVENT_2_JSON}

Or, to change the voice or instructions, run this at the start of a session:

{EVENT_3_JSON}

You can find the OpenAI realtime events documented [here](https://platform.openai.com/docs/guides/realtime/events).
"""

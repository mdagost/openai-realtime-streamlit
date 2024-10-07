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

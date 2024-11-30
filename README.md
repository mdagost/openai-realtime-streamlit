# openai-realtime-streamlit
POC Port of the [openai-realtime-console](https://github.com/openai/openai-realtime-console?tab=readme-ov-file) to streamlit.

Huge thanks to [MadCowD](https://github.com/MadcowD) for ell's [POC realtime python client](https://github.com/MadcowD/ell/tree/main/x/openai_realtime), from which I ripped my simple version.

## Instructions ##
1. Create a virtualenv for python >=3.10.
2. Run `poetry install`
3. Make sure you OpenAI API key is set as an environment variable at `OPENAI_API_KEY`.
4. Run `streamlit run openai_realtime_streamlit/app.py`.

- **10/7/2024**: Added support for playing back streaming audio.
- **10/8/2024**: Added support for sending streaming audio input.
- **11/30/2024**: Added function calling

*TODO*
- Enable disconnecting from the stream
- Enable changing the voice
- Enable text input via chat interface to allow the user to easily merge modalities

<img src="/readme/screenshot.png" width="800" />


# Changelog (11/30/2024)

## New Features
- Added tools/functions support to the SimpleRealtime client
  - New tool registration system with `add_tool()` and `add_tools()` methods
  - Automatic schema generation from Python functions
  - Support for both synchronous and asynchronous tool handlers
  - Tool definitions are sent to OpenAI on connection
  - Added function call handling in the message handler

## Code Organization
- Split audio-related code into separate `audio.py` module
  - Moved StreamingAudioRecorder class to its own file
  - Cleaned up imports in main app.py

## SimpleRealtime Client Improvements
- Added tool/function management
  - New `tools` dictionary to store registered functions
  - Added `_function_to_schema()` helper method for automatic OpenAI schema generation
  - Enhanced connect() to configure session with registered tools
- Made receive() method asynchronous
- Added proper typing hints and docstrings
- Improved error handling for function calls
- Enhanced websocket connection management

## App Changes
- Added sample time function tool (`get_current_time()`)
- Updated client initialization to support tools
- Improved session state management
- Enhanced error handling and user feedback

## Technical Improvements
- Added proper type hints throughout the codebase
- Improved asyncio integration and error handling
- Enhanced websocket connection management
- Better separation of concerns between modules

## Bug Fixes
- Fixed websocket connection handling
- Improved error handling in message handler
- Fixed tool registration validation
- Enhanced session state management

The refactoring mainly focused on adding tool support while improving code organization and robustness. The core audio functionality remains largely unchanged, but is now better organized in its own module.
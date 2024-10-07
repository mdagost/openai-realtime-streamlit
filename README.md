# openai-realtime-streamlit
POC Port of the [openai-realtime-console](https://github.com/openai/openai-realtime-console?tab=readme-ov-file) to streamlit.

Huge thanks to [MadCowD](https://github.com/MadcowD) for ell's [POC realtime python client](https://github.com/MadcowD/ell/tree/main/x/openai_realtime), from which I ripped my simple version.

## Instructions ##
1. Create a virtualenv for python >=3.10.
2. Run `poetry install`
3. Make sure you OpenAI API key is set as an environment variable at `OPENAI_API_KEY`.
4. Run `streamlit run openai_realtime_streamlit/app.py`.

**TODO 10/7**: Add support for sending and playing back streaming audio.  Async and streamlit don't play well together, so this is proving to be a bit tough...

<img src="/readme/screenshot.png" width="800" />

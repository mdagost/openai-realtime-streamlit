import asyncio
import base64
import json
import numpy as np
import os
import tzlocal
from datetime import datetime
from inspect import signature, Parameter
from typing import Dict, Any, List, Optional

import websockets


class SimpleRealtime:
    def __init__(self, event_loop=None, audio_buffer_cb=None, debug=False):
        self.url = 'wss://api.openai.com/v1/realtime'
        self.debug = debug
        self.event_loop = event_loop
        self.logs = []
        self.transcript = ""
        self.ws = None
        self._message_handler_task = None
        self.audio_buffer_cb = audio_buffer_cb
        self.tools = {}  # Added for tool support

    def _function_to_schema(self, func: callable) -> Dict[str, Any]:
        """
        Converts a function into a schema suitable for the Realtime API's tool format.
        """
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null",
        }

        sig = signature(func)
        parameters = {}
        required = []

        for name, param in sig.parameters.items():
            if name == 'args':  # Skip *args
                continue

            param_type = type_map.get(param.annotation, "string")
            param_info = {"type": param_type}

            # Add description from type hints if available
            if param.annotation.__doc__:
                param_info["description"] = param.annotation.__doc__.strip()

            parameters[name] = param_info

            if param.default == Parameter.empty:
                required.append(name)

        return {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required
            }
        }

    def add_tool(self, func_or_definition: Any, handler: Optional[callable] = None) -> bool:
        """
        Add a tool that can be called by the assistant.
        Can be called with either:
        1. add_tool(function) - automatically generates schema from function
        2. add_tool(definition, handler) - manual schema definition and handler
        """
        if handler is None:
            # Called with just a function - generate schema automatically
            if not callable(func_or_definition):
                raise ValueError("When called with one argument, it must be a callable")
            handler = func_or_definition
            definition = self._function_to_schema(func_or_definition)
        else:
            # Called with definition and handler
            definition = func_or_definition
            if not definition.get('name'):
                raise ValueError("Missing tool name in definition")
            if not callable(handler):
                raise ValueError(f"Tool '{definition['name']}' handler must be a function")

        name = definition['name']
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already added")

        self.tools[name] = {'definition': definition, 'handler': handler}

        # Update session with new tool if connected
        if self.is_connected():
            self.send("session.update", {
                "session": {
                    "tools": [
                        {**tool['definition'], 'type': 'function'}
                        for tool in self.tools.values()
                    ],
                    "tool_choice": "auto"
                }
            })
        return True

    def add_tools(self, functions: List[callable]) -> bool:
        """
        Add multiple functions as tools at once, automatically generating schemas.
        """
        for func in functions:
            self.add_tool(func)
        return True

    def is_connected(self):
        return self.ws is not None #and self.ws.open

    def log_event(self, event_type, event):
        if self.debug:
            local_timezone = tzlocal.get_localzone()
            now = datetime.now(local_timezone).strftime("%H:%M:%S")
            msg = json.dumps(event)
            self.logs.append((now, event_type, msg))
        return True


    async def connect(self, model="gpt-4o-realtime-preview-2024-10-01"):
        if self.is_connected():
            raise Exception("Already connected")

        headers = {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "OpenAI-Beta": "realtime=v1"
        }

        self.ws = await websockets.connect(f"{self.url}?model={model}", additional_headers=headers)

        # Start the message handler in the same loop as the websocket
        self._message_handler_task = self.event_loop.create_task(self._message_handler())

        # Send initial session configuration with tools
        if self.tools:
            use_tools = [
                {**tool['definition'], 'type': 'function'}
                for tool in self.tools.values()
            ]
            await self.ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "tools": use_tools,
                    "tool_choice": "auto"
                }
            }))

        return True

    async def _message_handler(self):
        try:
            while True:
                if not self.ws:
                    await asyncio.sleep(0.05)
                    continue

                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=0.05)
                    data = json.loads(message)
                    await self.receive(data)  # Changed to await
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
        except Exception as e:
            print(f"Message handler error: {e}")
            await self.disconnect()

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self._message_handler_task:
            self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass
        self._message_handler_task = None
        return True

    async def handle_function_call(self, event):
        """Handle function calls from the assistant"""
        try:
            name = event.get('name')
            if name not in self.tools:
                print(f"Unknown tool: {name}")
                return

            call_id = event.get('call_id')
            arguments = json.loads(event.get('arguments', '{}'))
            tool = self.tools[name]

            # Execute the function
            result = await tool['handler'](arguments) if asyncio.iscoroutinefunction(tool['handler']) else tool[
                'handler'](arguments)

            # Send function output back
            await self.ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result)
                }
            }))

            # Request a new response
            await self.ws.send(json.dumps({
                "type": "response.create"
            }))

        except Exception as e:
            print(f"Error handling function call: {e}")
            if call_id:
                # Send error as function output
                await self.ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps({"error": str(e)})
                    }
                }))

    def handle_audio(self, event):
        if event.get("type") == "response.audio_transcript.delta":
            self.transcript += event.get("delta")

        if event.get("type") == "response.audio.delta" and self.audio_buffer_cb:
            b64_audio_chunk = event.get("delta")
            decoded_audio_chunk = base64.b64decode(b64_audio_chunk)
            pcm_audio_chunk = np.frombuffer(decoded_audio_chunk, dtype=np.int16)
            self.audio_buffer_cb(pcm_audio_chunk)

    async def receive(self, event):
        self.log_event("server", event)

        event_type = event.get("type", "")

        # Handle function calls
        if event_type == "response.function_call_arguments.done":
            await self.handle_function_call(event)

        # Handle audio responses
        elif "response.audio" in event_type:
            self.handle_audio(event)

        return True

    def send(self, event_name, data=None):
        if not self.is_connected():
            raise Exception("RealtimeAPI is not connected")

        data = data or {}
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")

        event = {
            "type": event_name,
            **data
        }

        self.log_event("client", event)

        self.event_loop.create_task(self.ws.send(json.dumps(event)))

        return True



import asyncio
import base64
import json
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from google import genai
from backend.config import get_api_keys
from backend.tools.live_capabilities import LIVE_TOOLS, create_file, read_file, list_files, run_command

router = APIRouter()

@router.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    keys = get_api_keys()
    if not keys.gemini_api_key:
        print("Error: Gemini API key missing")
        await websocket.close(code=1008, reason="API Key missing")
        return

    # Initialize Gemini Client
    # Using v1alpha as Live API is experimental/new
    client = genai.Client(api_key=keys.gemini_api_key, http_options={'api_version': 'v1alpha'})
    model = "gemini-2.0-flash-exp"
    
    # Configure session
    # We want audio back. We provide tools.
    config = {
        "response_modalities": ["AUDIO"],
        "tools": LIVE_TOOLS,
        "system_instruction": "You are Middle Manager, an intelligent AI coding assistant. You can create files, list files, and run commands. You are helpful, concise, and professional. Use the available tools to fulfill user requests immediately."
    }

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            print("Connected to Gemini Live session")
            
            # Create tasks for bidirectional communication
            
            # Task 1: Receive from Frontend -> Send to Gemini
            async def send_to_gemini():
                try:
                    while True:
                        # Receive message from frontend
                        # Expecting: {"type": "audio", "data": "base64..."} or {"type": "text", "text": "..."}
                        # OR raw bytes if structured that way. Let's assume JSON for metadata + base64 audio.
                        # For simplicity, if we get bytes, treat as audio. If text, treat as JSON.
                        
                        message = await websocket.receive()
                        
                        if "text" in message:
                            data = json.loads(message["text"])
                            if data.get("type") == "audio":
                                # Send audio chunk to Gemini
                                # data["data"] is base64 encoded PCM 16kHz
                                audio_bytes = base64.b64decode(data["data"])
                                await session.send(input={"mime_type": "audio/pcm", "data": audio_bytes}, end_of_turn=False)
                                
                            elif data.get("type") == "endpoints":
                                # User stopped talking or similar - signal end of turn if needed
                                # But Live API usually handles VAD.
                                pass
                                
                        elif "bytes" in message:
                            # Raw audio bytes
                            await session.send(input={"mime_type": "audio/pcm", "data": message["bytes"]}, end_of_turn=False)

                except WebSocketDisconnect:
                    print("Frontend disconnected (in send loop)")
                    raise
                except Exception as e:
                    print(f"Error in send_to_gemini: {e}")
                    raise

            # Task 2: Receive from Gemini -> Send to Frontend & Handle Tools
            async def receive_from_gemini():
                try:
                    async for response in session.receive():
                        # Response can contain audio, text, or tool calls
                        
                        # 1. Handle Tool Calls
                        if response.tool_calls:
                            for tool_call in response.tool_calls:
                                print(f"Tool call received: {tool_call.function_calls}")
                                for fc in tool_call.function_calls:
                                    name = fc.name
                                    args = fc.args
                                    
                                    # Execute tool
                                    result = "Tool not found"
                                    if name == "create_file":
                                        result = create_file(args["path"], args["content"])
                                    elif name == "read_file":
                                        result = read_file(args["path"])
                                    elif name == "list_files":
                                        result = list_files(args.get("path", "."))
                                    elif name == "run_command":
                                        result = run_command(args["command"])
                                    
                                    # Send result back to Gemini as text observation
                                    # This ensures the model knows the outcome even if we don't use strict ToolResponse types
                                    await session.send(input=f"Tool '{name}' executed. Output: {result}", end_of_turn=True)
                        
                        # 2. Handle Audio Response
                        # The server yields chunks with 'data' if audio is present
                        if response.data:
                            # Turn audio bytes to base64 for websocket JSON
                            # response.data is the raw audio bytes (PCM 24kHz usually)
                            b64_audio = base64.b64encode(response.data).decode("utf-8")
                            await websocket.send_json({
                                "type": "audio",
                                "data": b64_audio
                            })
                            
                        # 3. Handle Text (if any) - usually for transcripts
                        if response.text:
                             await websocket.send_json({
                                "type": "text",
                                "content": response.text
                            })

                except Exception as e:
                    print(f"Error in receive_from_gemini: {e}")
                    traceback.print_exc()
                    raise

            # Run both
            await asyncio.gather(send_to_gemini(), receive_from_gemini())

    except WebSocketDisconnect:
        print("Frontend disconnected")
    except Exception as e:
        print(f"Error establishing session: {e}")
        traceback.print_exc()
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass

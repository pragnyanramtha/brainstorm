import React, { useRef, useState, useEffect } from 'react';
import { Mic, MicOff, X, Volume2 } from 'lucide-react';

export const VoiceMode = () => {
    const [isActive, setIsActive] = useState(false);
    const [status, setStatus] = useState<'idle' | 'listening' | 'speaking' | 'processing'>('idle');
    const websocket = useRef<WebSocket | null>(null);
    const audioContext = useRef<AudioContext | null>(null);
    const playbackContext = useRef<AudioContext | null>(null);
    const processor = useRef<ScriptProcessorNode | null>(null);
    const source = useRef<MediaStreamAudioSourceNode | null>(null);
    const stream = useRef<MediaStream | null>(null);
    const audioQueue = useRef<string[]>([]); // Queue of base64 chunks
    const isPlaying = useRef(false);

    const startSession = async () => {
        setIsActive(true);
        setStatus('listening');

        try {
            // Use environment variable or default to localhost:8000
            const wsUrl = 'ws://localhost:8000/ws/voice';

            // Init playback context on user gesture
            if (!playbackContext.current) {
                playbackContext.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
            }
            if (playbackContext.current.state === 'suspended') {
                await playbackContext.current.resume();
            }

            websocket.current = new WebSocket(wsUrl);

            websocket.current.onopen = () => {
                console.log("Connected to Voice Backend");
                startRecording();
            };

            websocket.current.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'audio') {
                    // Queue audio for playback
                    audioQueue.current.push(data.data);
                    if (!isPlaying.current) {
                        playQueue();
                    }
                } else if (data.type === 'text') {
                    console.log("Transcript:", data.content);
                }
            };

            websocket.current.onclose = (event) => {
                console.log("Disconnected", event.code, event.reason);
                stopSession();
            };

            websocket.current.onerror = (error) => {
                console.error("WebSocket Error:", error);
                stopSession();
            };

        } catch (e) {
            console.error(e);
            stopSession();
        }
    };

    const stopSession = () => {
        setIsActive(false);
        setStatus('idle');
        stopRecording();
        if (websocket.current) {
            websocket.current.close();
            websocket.current = null;
        }
    };

    const startRecording = async () => {
        try {
            // Request 16kHz audio from browser
            stream.current = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Capture validation
            const track = stream.current.getAudioTracks()[0];
            const settings = track.getSettings();
            console.log("Audio Input Settings:", settings);

            // Create AudioContext for capture - stick to 16kHz if possible
            const captureRate = settings.sampleRate || 16000;
            audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)({
                sampleRate: captureRate
            });

            source.current = audioContext.current.createMediaStreamSource(stream.current);

            // ScriptProcessor to capture raw PCM
            // Buffer size 4096 is ~256ms at 16kHz
            processor.current = audioContext.current.createScriptProcessor(4096, 1, 1);

            processor.current.onaudioprocess = (e) => {
                if (!websocket.current || websocket.current.readyState !== WebSocket.OPEN) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Resample if necessary (e.g. capture is 48k, target 16k)
                // For MVP, we send what we get, but Gemini expects 16k.
                // If browser didn't give 16k, we might need simple decimation.
                // Assuming browser honors getUserMedia constraint for now or backend handles it.
                // Actually, backend sends raw bytes to Gemini. Gemini is robust but prefers 16k.

                // Convert float32 to int16 (PCM)
                const buffer = new ArrayBuffer(inputData.length * 2);
                const view = new DataView(buffer);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    // signed 16-bit integer -32768 to 32767
                    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                }

                const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));
                websocket.current.send(JSON.stringify({
                    type: "audio",
                    data: base64
                }));
            };

            // Connect to gain node 0 to avoid feedback
            const gainNode = audioContext.current.createGain();
            gainNode.gain.value = 0;

            source.current.connect(processor.current);
            processor.current.connect(gainNode);
            gainNode.connect(audioContext.current.destination);

        } catch (e) {
            console.error("Mic Error", e);
        }
    };

    const stopRecording = () => {
        if (stream.current) stream.current.getTracks().forEach(t => t.stop());
        if (processor.current) processor.current.disconnect();
        if (source.current) source.current.disconnect();
        if (audioContext.current) audioContext.current.close();
    };

    const playQueue = async () => {
        if (isPlaying.current || audioQueue.current.length === 0) return;

        isPlaying.current = true;
        setStatus('speaking');

        try {
            // Context should be init in startSession
            if (!playbackContext.current) return;

            while (audioQueue.current.length > 0) {
                const chunkBase64 = audioQueue.current.shift();
                if (!chunkBase64) continue;

                // Decode base64 
                const binaryString = atob(chunkBase64);
                const len = binaryString.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                // Convert Int16 PCM to Float32
                const int16 = new Int16Array(bytes.buffer);
                const float32 = new Float32Array(int16.length);
                for (let i = 0; i < int16.length; i++) {
                    float32[i] = int16[i] / 32768.0;
                }

                const audioBuffer = playbackContext.current.createBuffer(1, float32.length, 24000);
                audioBuffer.getChannelData(0).set(float32);

                const source = playbackContext.current.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(playbackContext.current.destination);
                source.start();

                await new Promise(resolve => {
                    source.onended = resolve;
                });
            }
        } catch (e) {
            console.error("Playback error", e);
        } finally {
            isPlaying.current = false;
            // Only set back to listening if we haven't stopped
            if (websocket.current) {
                setStatus('listening');
            }
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopSession();
        };
    }, []);

    if (!isActive) {
        return (
            <button
                onClick={startSession}
                className="fixed bottom-24 right-6 p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all z-50 flex items-center justify-center animate-in zoom-in duration-300"
                title="Start Voice Assistant"
            >
                <Mic size={24} />
            </button>
        );
    }

    return (
        <div className="fixed bottom-24 right-6 z-50 flex flex-col items-center bg-gray-900/90 backdrop-blur-lg border border-gray-700/50 rounded-2xl p-6 shadow-2xl w-72 animate-in slide-in-from-bottom-10 fade-in duration-300">
            <div className="flex justify-between w-full mb-6 items-center">
                <span className="text-white font-semibold text-lg tracking-tight bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Gemini Live</span>
                <button
                    onClick={stopSession}
                    className="text-gray-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-full"
                >
                    <X size={20} />
                </button>
            </div>

            <div className={`relative w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-all duration-500 ${status === 'listening' ? 'bg-blue-500/20 text-blue-400 ring-2 ring-blue-500/50 ring-offset-2 ring-offset-gray-900' :
                status === 'speaking' ? 'bg-green-500/20 text-green-400 ring-2 ring-green-500/50 ring-offset-2 ring-offset-gray-900 scale-110' :
                    'bg-gray-800 text-gray-400'
                }`}>
                {/* Ping animation for listening */}
                {status === 'listening' && (
                    <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-20 animate-ping"></span>
                )}

                {status === 'speaking' ? <Volume2 size={32} /> : <Mic size={32} />}
            </div>

            <div className="text-sm font-medium text-center text-gray-300 min-h-[1.5rem]">
                {status === 'listening' && (
                    <span className="animate-pulse">Listening...</span>
                )}
                {status === 'speaking' && (
                    <span className="text-green-400">Speaking...</span>
                )}
                {status === 'processing' && "Thinking..."}
            </div>

            <div className="mt-4 text-xs text-gray-500 w-full text-center border-t border-gray-800 pt-3">
                Say "Create a file called..." or "List files"
            </div>
        </div>
    );
};

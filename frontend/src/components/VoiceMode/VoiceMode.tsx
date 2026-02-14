import React, { useRef, useState, useEffect } from 'react';
import { Mic, MicOff, X, Volume2, Activity, Square } from 'lucide-react';

export const VoiceMode = ({ className, renderTrigger }: { className?: string, renderTrigger?: (onClick: () => void) => React.ReactNode }) => {
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
        if (renderTrigger) {
            return <>{renderTrigger(startSession)}</>;
        }
        return (
            <button
                onClick={startSession}
                className={className || "fixed bottom-24 right-6 p-4 bg-slate-900 text-white rounded-full shadow-lg hover:shadow-xl transition-all z-50 flex items-center justify-center hover:bg-slate-800"}
                title="Start Voice Assistant"
            >
                <Mic size={24} />
            </button>
        );
    }

    return (
        <>
            {/* Voice Mode Overlay */}
            <div className="fixed bottom-24 right-6 z-50 flex flex-col items-center bg-white border border-slate-200 rounded-xl p-6 shadow-2xl w-80 animate-in slide-in-from-bottom-10 fade-in duration-300">
                <div className="flex justify-between w-full mb-6 items-center border-b border-slate-100 pb-4">
                    <div className="flex items-center gap-2">
                        <Activity size={16} className="text-slate-900" />
                        <span className="text-slate-900 font-bold text-sm uppercase tracking-wide">Voice Interface</span>
                    </div>
                    <button
                        onClick={stopSession}
                        className="text-slate-400 hover:text-slate-900 transition-colors p-1.5 hover:bg-slate-100 rounded-md"
                    >
                        <X size={16} />
                    </button>
                </div>

                <div className={`relative w-16 h-16 rounded-full flex items-center justify-center mb-6 transition-all duration-300 border ${status === 'listening' ? 'bg-blue-50 border-blue-200 text-blue-600' :
                    status === 'speaking' ? 'bg-emerald-50 border-emerald-200 text-emerald-600' :
                        'bg-slate-50 border-slate-200 text-slate-400'
                    }`}>

                    {status === 'speaking' ? <Volume2 size={24} /> : <Mic size={24} />}
                </div>

                <div className="text-sm font-bold uppercase tracking-widest text-center text-slate-500 min-h-[1.5rem] flex items-center gap-2 justify-center">
                    {status === 'listening' && (
                        <>
                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                            <span>Listening</span>
                        </>
                    )}
                    {status === 'speaking' && (
                        <>
                            <span className="w-2 h-2 bg-emerald-500 rounded-full" />
                            <span className="text-emerald-600">Active</span>
                        </>
                    )}
                    {status === 'processing' && (
                        <>
                            <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                            <span>Processing</span>
                        </>
                    )}
                </div>

                <div className="mt-6 text-[11px] font-medium text-slate-400 w-full text-center border-t border-slate-100 pt-4 uppercase tracking-wide">
                    Voice Command System Active
                </div>
            </div>
        </>
    );
};


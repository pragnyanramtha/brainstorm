import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Sparkles, Zap, ArrowUp } from 'lucide-react';
import { Message as MessageComponent } from './Message';
import { ProQuestionnaire } from './ProQuestionnaire';
import { StatusBar } from './StatusBar';
import { VoiceMode } from './VoiceMode/VoiceMode';
import type { Message, ClarificationQuestion } from '../types';

interface ChatAreaProps {
    messages: Message[];
    onSendMessage: (content: string) => void;
    status: string | null;
    clarificationQuestions: ClarificationQuestion[] | null;
    onClarificationResponse: (answers: Record<string, string>) => void;
    error: string | null;
    hasProject: boolean;
    onNewChat: () => void;
}

const STATUS_LABELS: Record<string, string> = {
    analyzing: 'Understanding request...',
    clarifying: 'Asking clarifying questions...',
    optimizing: 'Optimizing prompt...',
    executing: 'Generating response...',
    complete: 'Ready',
};

export function ChatArea({
    messages, onSendMessage, status, clarificationQuestions,
    onClarificationResponse, error, hasProject, onNewChat
}: ChatAreaProps) {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, status, clarificationQuestions]);

    // Auto-resize
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
        }
    }, [input]);

    const handleSend = () => {
        const trimmed = input.trim();
        if (!trimmed) return;

        if (!hasProject) {
            onNewChat();
            setTimeout(() => onSendMessage(trimmed), 300);
        } else {
            onSendMessage(trimmed);
        }
        setInput('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant');

    // Empty State
    if (!hasProject && messages.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center relative overflow-hidden">
                <div className="bg-surface-raised/30 absolute inset-0 -z-10" />

                <div className="max-w-2xl w-full px-6 flex flex-col items-center text-center -mt-20 animate-fade-in">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-accent-muted flex items-center justify-center mb-8 shadow-glow transition-transform hover:scale-105 duration-500">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>

                    <h1 className="text-3xl font-bold text-white mb-4 tracking-tight text-balance">
                        What can I build for you?
                    </h1>
                    <p className="text-text-secondary text-lg mb-12 max-w-lg text-balance leading-relaxed">
                        I'll help you plan, reason, and execute complex tasks using the best AI models for the job.
                    </p>

                    <div className="w-full relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-accent/50 to-purple-500/50 rounded-2xl opacity-20 group-hover:opacity-40 transition-opacity blur" />
                        <div className="relative bg-surface border border-white/10 rounded-2xl shadow-2xl flex flex-col">
                            <textarea
                                ref={textareaRef}
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Describe your project or task..."
                                rows={1}
                                className="w-full bg-transparent border-none rounded-xl px-5 py-4 pr-14 text-text-primary placeholder-text-muted/50 outline-none resize-none text-base leading-relaxed max-h-[200px]"
                            />
                            <div className="px-3 pb-3 flex justify-between items-center">
                                <button className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors">
                                    <Paperclip size={18} />
                                </button>
                                <button
                                    onClick={handleSend}
                                    disabled={!input.trim()}
                                    className="p-2 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-accent/20"
                                >
                                    <ArrowUp size={20} />
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 flex gap-4 text-sm text-text-muted">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
                            <Zap size={14} className="text-yellow-400" />
                            <span>Gemini + Claude</span>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
                            <Sparkles size={14} className="text-purple-400" />
                            <span>MCP Tools</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col min-w-0 bg-surface relative">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 md:px-0 py-6 scroll-smooth">
                <div className="max-w-3xl mx-auto space-y-8">
                    {messages.map((msg, i) => (
                        <div key={msg.id} className="animate-fade-in" style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'both' }}>
                            <MessageComponent message={msg} />
                        </div>
                    ))}

                    {clarificationQuestions && (
                        <div className="animate-slide-up py-4">
                            <ProQuestionnaire
                                questions={clarificationQuestions}
                                lastIntent={lastAssistantMessage?.metadata?.interpreted_intent}
                                onSubmit={onClarificationResponse}
                            />
                        </div>
                    )}

                    {status && status !== 'complete' && (
                        <div className="flex items-center gap-3 py-4 animate-fade-in pl-4">
                            <div className="flex gap-1.5">
                                <div className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{ animationDelay: '0ms' }} />
                                <div className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{ animationDelay: '150ms' }} />
                                <div className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                            <span className="text-text-secondary text-sm font-medium">{STATUS_LABELS[status] || status}</span>
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-5 py-4 text-red-200 text-sm animate-fade-in mx-4">
                            {error}
                        </div>
                    )}

                    <div ref={messagesEndRef} className="h-4" />
                </div>
            </div>

            {/* Input Area */}
            <div className="flex-shrink-0 px-4 pb-6 pt-2">
                <div className="max-w-3xl mx-auto relative group">
                    {/* Glass Blur Background */}
                    <div className="absolute -inset-4 bg-surface/80 backdrop-blur-lg -z-10 bg-gradient-to-t from-surface via-surface to-transparent pointer-events-none" />

                    <div className="relative bg-surface-raised border border-white/10 rounded-2xl shadow-2xl transition-all focus-within:border-accent/30 focus-within:shadow-[0_0_20px_-5px_rgba(37,99,235,0.15)]">
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Message Middle Manager..."
                            rows={1}
                            className="w-full bg-transparent border-none rounded-xl px-4 py-3.5 pr-24 text-text-primary placeholder-text-muted/60 outline-none resize-none text-sm leading-relaxed max-h-[200px]"
                        />

                        <div className="absolute right-2 bottom-2 flex items-center gap-1">
                            <button className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors">
                                <Paperclip size={18} />
                            </button>
                            <VoiceMode renderTrigger={(start) => (
                                <button
                                    onClick={start}
                                    className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
                                    title="Voice Mode"
                                >
                                    <Zap size={18} />
                                </button>
                            )} />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || !!status}
                                className="p-1.5 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                            >
                                <ArrowUp size={18} />
                            </button>
                        </div>
                    </div>

                    {/* Status Bar Floating */}
                    {lastAssistantMessage && (
                        <div className="absolute -top-8 right-0 left-0">
                            <div className="flex justify-center">
                                <StatusBar metadata={lastAssistantMessage.metadata} />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Activity, Terminal, ArrowUp, Cpu, Layout, HelpCircle } from 'lucide-react';
import { Message as MessageComponent } from './Message';
import { ProQuestionnaire } from './ProQuestionnaire';
import { ApproachCard } from './ApproachCard';
import { StatusBar } from './StatusBar';
import { VoiceMode } from './VoiceMode/VoiceMode';
import type { Message, ClarificationQuestion, ApproachProposal } from '../types';

interface ChatAreaProps {
    messages: Message[];
    onSendMessage: (content: string) => void;
    status: string | null;
    statusDetail: string | null;
    clarificationQuestions: ClarificationQuestion[] | null;
    onClarificationResponse: (answers: Record<string, string>) => void;
    approachProposals: ApproachProposal[] | null;
    approachContextSummary: string | null;
    onApproachSelection: (approach: ApproachProposal) => void;
    error: string | null;
    hasProject: boolean;
    onNewChat: () => void;
}

const STATUS_LABELS: Record<string, string> = {
    analyzing: 'Analyzing requirements...',
    clarifying: 'Configuring parameters...',
    brainstorming: 'Generating proposals...',
    optimizing: 'Optimizing context...',
    executing: 'Processing...',
    scaffolding: 'Initializing project structure...',
    complete: 'Ready',
};

export function ChatArea({
    messages, onSendMessage, status, statusDetail, clarificationQuestions,
    onClarificationResponse, approachProposals, approachContextSummary,
    onApproachSelection, error, hasProject, onNewChat
}: ChatAreaProps) {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
    }, [messages, status, clarificationQuestions, approachProposals]);

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
            <div className="flex-1 flex flex-col items-center justify-center bg-surface p-6 relative">
                <div className="max-w-xl w-full flex flex-col items-center -mt-16 animate-fade-in">
                    <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center mb-6 shadow-sm">
                        <Terminal className="w-5 h-5 text-primary-foreground" />
                    </div>

                    <h1 className="text-2xl font-semibold text-foreground mb-2 tracking-tight">
                        Start a new conversation
                    </h1>
                    <p className="text-muted-foreground text-sm mb-10 max-w-sm text-center leading-relaxed font-medium">
                        Describe your technical requirements or project goals to begin a structured workspace session.
                    </p>

                    <div className="w-full bg-surface border border-border rounded-xl shadow-lg flex flex-col overflow-hidden transition-all focus-within:border-primary/50 focus-within:shadow-xl ring-1 ring-border/50">
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Message Brainstorm AI..."
                            rows={1}
                            className="w-full bg-transparent border-none px-5 py-4 text-foreground placeholder:text-muted-foreground outline-none resize-none text-sm leading-relaxed max-h-[200px]"
                            autoFocus
                        />
                        <div className="px-4 pb-3 flex justify-between items-center bg-surface-container/50 border-t border-border/50">
                            <div className="flex items-center gap-2">
                                <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-raised transition-colors" title="Attach Files">
                                    <Paperclip size={16} />
                                </button>
                                <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-raised transition-colors" title="Help">
                                    <HelpCircle size={16} />
                                </button>
                            </div>
                            <button
                                onClick={handleSend}
                                disabled={!input.trim()}
                                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm"
                            >
                                <span>Send Message</span>
                                <ArrowUp size={14} />
                            </button>
                        </div>
                    </div>

                    <div className="mt-10 grid grid-cols-2 gap-3 w-full max-w-md">
                        <div className="flex items-center gap-3 p-3 rounded-xl border border-border bg-surface-container/50 text-muted-foreground hover:text-foreground transition-colors">
                            <Cpu size={14} />
                            <span className="text-[11px] font-semibold uppercase tracking-wider">Dual Core Logic</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 rounded-xl border border-border bg-surface-container/50 text-muted-foreground hover:text-foreground transition-colors">
                            <Layout size={14} />
                            <span className="text-[11px] font-semibold uppercase tracking-wider">Workspace Sync</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col min-w-0 bg-surface relative">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 md:px-0 py-8 scroll-smooth">
                <div className="max-w-3xl mx-auto space-y-10">
                    {messages.map((msg, i) => (
                        <div key={msg.id} className="animate-fade-in">
                            <MessageComponent message={msg} />
                        </div>
                    ))}

                    {clarificationQuestions && (
                        <div className="animate-slide-up py-4 px-4">
                            <ProQuestionnaire
                                questions={clarificationQuestions}
                                lastIntent={lastAssistantMessage?.metadata?.interpreted_intent}
                                onSubmit={onClarificationResponse}
                            />
                        </div>
                    )}

                    {approachProposals && approachProposals.length > 0 && (
                        <div className="animate-slide-up py-4 px-4">
                            <ApproachCard
                                approaches={approachProposals}
                                contextSummary={approachContextSummary}
                                onSelect={onApproachSelection}
                            />
                        </div>
                    )}

                    {status && status !== 'complete' && (
                        <div className="flex items-center gap-4 py-4 px-6 animate-fade-in">
                            <div className="flex gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse" />
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse delay-75" />
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse delay-150" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">{STATUS_LABELS[status] || status}</span>
                                {statusDetail && (
                                    <span className="text-secondary-muted text-[11px] mt-0.5 font-medium">{statusDetail}</span>
                                )}
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="bg-error/5 border border-error/20 rounded-xl px-5 py-4 text-error text-sm mx-4 flex items-center gap-3">
                            <div className="w-1 h-3 bg-error rounded-full" />
                            <span className="font-medium">{error}</span>
                        </div>
                    )}

                    <div ref={messagesEndRef} className="h-8" />
                </div>
            </div>

            {/* Input Area */}
            <div className="flex-shrink-0 px-6 pb-8 pt-2 bg-surface">
                <div className="max-w-3xl mx-auto relative group">
                    <div className="flex flex-col bg-surface border border-border rounded-xl shadow-lg transition-all focus-within:border-primary/50 focus-within:shadow-xl overflow-hidden ring-1 ring-border/50">

                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Message Middle Manager..."
                            rows={1}
                            className="w-full bg-transparent border-none px-4 py-4 text-foreground placeholder:text-muted-foreground outline-none resize-none text-sm leading-relaxed max-h-[300px] min-h-[60px]"
                        />

                        {/* Toolbar */}
                        <div className="flex items-center justify-between px-3 py-2 bg-surface-container/50 border-t border-border/50">
                            <div className="flex items-center gap-1">
                                <button
                                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface-raised transition-colors text-xs font-medium"
                                    title="Attach Files"
                                >
                                    <Paperclip size={14} />
                                    <span>Attach</span>
                                </button>

                                <VoiceMode renderTrigger={(start) => (
                                    <button
                                        onClick={start}
                                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface-raised transition-colors text-xs font-medium"
                                        title="Voice Input"
                                    >
                                        <Activity size={14} />
                                        <span>Voice Mode</span>
                                    </button>
                                )} />
                            </div>

                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || !!status}
                                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm text-xs font-bold uppercase tracking-wide"
                            >
                                <span>Send</span>
                                <ArrowUp size={14} />
                            </button>
                        </div>
                    </div>

                    {/* Status Bar Floating */}
                    {lastAssistantMessage && (
                        <div className="absolute -top-12 left-0 right-0 flex justify-center pointer-events-none">
                            <div className="pointer-events-auto shadow-sm">
                                <StatusBar metadata={lastAssistantMessage.metadata} />
                            </div>
                        </div>
                    )}
                </div>

                <div className="max-w-3xl mx-auto flex justify-center mt-3 gap-6 text-[10px] text-muted-foreground font-medium">
                    <span className="flex items-center gap-1.5 hover:text-foreground transition-colors cursor-pointer">
                        <Cpu size={12} /> Dual Core Logic
                    </span>
                    <span className="flex items-center gap-1.5 hover:text-foreground transition-colors cursor-pointer">
                        <Layout size={12} /> Local Workspace
                    </span>
                </div>
            </div>
        </div>
    );
}

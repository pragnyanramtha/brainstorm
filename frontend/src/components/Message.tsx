import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, Eye, ThumbsUp, ThumbsDown, Terminal, ExternalLink, FolderOpen } from 'lucide-react';
import { DebugPanel } from './DebugPanel';
import type { Message as MessageType } from '../types';

interface MessageProps {
    message: MessageType;
}

function CodeBlock({ children, className }: { children: any; className?: string }) {
    const [copied, setCopied] = useState(false);
    const language = (className || '').replace('language-', '');
    const code = String(children).replace(/\n$/, '');

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="my-4 rounded-xl overflow-hidden border border-surface-border bg-surface-raised/50 group">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <Terminal size={14} className="text-text-muted" />
                    <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">{language || 'text'}</span>
                </div>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-white/5 text-xs text-text-muted hover:text-text-primary transition-all"
                >
                    {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                    <span className={copied ? 'text-emerald-400' : ''}>{copied ? 'Copied' : 'Copy'}</span>
                </button>
            </div>

            {/* Code */}
            <div className="overflow-x-auto p-4 bg-surface-raised font-mono text-sm leading-relaxed text-text-secondary whitespace-pre">
                {/* We render children directly which is the code text */}
                <code>{code}</code>
            </div>
        </div>
    );
}

export function Message({ message }: MessageProps) {
    const [showDebug, setShowDebug] = useState(false);
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';

    return (
        <div className={`flex flex-col group ${isUser ? 'items-end' : 'items-start'}`}>

            {/* Header/Name (Optional - keep minimal for now) */}
            <div className={`flex items-center gap-2 mb-1 px-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                <span className="text-xs font-semibold text-text-primary/70">
                    {isUser ? 'You' : 'Middle Manager'}
                </span>
                <span className="text-[10px] text-text-muted transition-opacity opacity-0 group-hover:opacity-100">
                    {new Date(message.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>

            <div className={`max-w-[85%] sm:max-w-[75%] ${isUser ? '' : 'w-full'}`}>
                <div
                    className={`relative px-5 py-3.5 text-sm leading-7 shadow-sm transition-all duration-200 ${isUser
                        ? 'bg-accent text-white rounded-2xl rounded-tr-sm shadow-[0_2px_10px_-2px_rgba(37,99,235,0.2)]'
                        : 'bg-surface-raised/80 border border-white/5 backdrop-blur-sm text-text-primary rounded-2xl rounded-tl-sm hover:border-white/10'
                        }`}
                >
                    {isAssistant ? (
                        <div className="markdown-content">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    code({ node, className, children, ...props }) {
                                        const match = /language-(\w+)/.exec(className || '');
                                        const isInline = !match;

                                        if (isInline) {
                                            return <code className="font-mono text-[0.9em] bg-surface-overlay/50 px-1.5 py-0.5 rounded border border-white/5 text-accent-hover" {...props}>{children}</code>;
                                        }

                                        return <CodeBlock className={className}>{children}</CodeBlock>;
                                    },
                                    // Override pre to do nothing since CodeBlock handles the wrapper
                                    pre({ children }) {
                                        return <>{children}</>;
                                    }
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap font-sans">{message.content}</div>
                    )}
                </div>

                {/* Actions Row */}
                {!isUser && message.metadata && (
                    <div className="flex items-center gap-3 mt-2 px-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button
                            onClick={() => setShowDebug(!showDebug)}
                            className={`flex items-center gap-1.5 text-xs transition-colors ${showDebug ? 'text-accent' : 'text-text-muted hover:text-text-primary'}`}
                        >
                            <Eye size={12} />
                            <span>{showDebug ? 'Hide Prompt' : 'See Prompt'}</span>
                        </button>

                        <div className="h-3 w-px bg-surface-border" />

                        <div className="flex items-center gap-1">
                            <button className="p-1 text-text-muted hover:text-emerald-400 hover:bg-white/5 rounded transition-all">
                                <ThumbsUp size={12} />
                            </button>
                            <button className="p-1 text-text-muted hover:text-red-400 hover:bg-white/5 rounded transition-all">
                                <ThumbsDown size={12} />
                            </button>
                        </div>
                    </div>
                )}

                {/* Debug Panel */}
                {showDebug && message.id && (
                    <div className="mt-4 animate-slide-up origin-top">
                        <DebugPanel messageId={message.id} />
                    </div>
                )}
            </div>
        </div>
    );
}

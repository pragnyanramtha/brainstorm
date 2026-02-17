import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, Eye, ThumbsUp, ThumbsDown, Terminal, ExternalLink, FolderOpen, User, Activity } from 'lucide-react';
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
        <div className="my-6 rounded-lg overflow-hidden border border-border bg-surface-container shadow-sm group">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-surface-raised border-b border-border">
                <div className="flex items-center gap-2">
                    <Terminal size={12} className="text-muted-foreground" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{language || 'text'}</span>
                </div>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-surface-raised-high text-[10px] font-bold text-muted-foreground hover:text-foreground transition-all uppercase tracking-wider"
                >
                    {copied ? <Check size={12} className="text-success" /> : <Copy size={12} />}
                    <span className={copied ? 'text-success' : ''}>{copied ? 'Copied' : 'Copy'}</span>
                </button>
            </div>

            {/* Code */}
            <div className="overflow-x-auto p-4 font-mono text-[13px] leading-relaxed text-foreground">
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
        <div className={`flex flex-col group ${isUser ? 'items-end' : 'items-start'} max-w-full px-4`}>

            {/* Project Info Banner */}
            {isAssistant && message.metadata?.dev_server_url && (
                <div className="w-full mb-4 bg-accent/10 border border-accent/20 rounded-xl px-4 py-3 animate-fade-in shadow-sm">
                    <div className="flex items-center gap-4 flex-wrap">
                        {message.metadata.dev_server_url && (
                            <a
                                href={message.metadata.dev_server_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-xs text-accent hover:text-accent-foreground transition-colors font-semibold"
                            >
                                <ExternalLink size={14} />
                                <span>{message.metadata.dev_server_url}</span>
                            </a>
                        )}
                        {message.metadata.project_dir && (
                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                                <FolderOpen size={12} />
                                <span>{message.metadata.project_dir}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Header/Name */}
            <div className={`flex items-center gap-2 mb-1.5 px-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-6 h-6 rounded-lg flex items-center justify-center ${isUser ? 'bg-surface-raised-high text-muted-foreground' : 'bg-gradient-to-br from-primary to-primary-hover text-primary-foreground shadow-md'}`}>
                    {isUser ? <User size={14} /> : <Activity size={14} />}
                </div>
                <span className="text-[11px] font-bold text-foreground uppercase tracking-wider">
                    {isUser ? 'User Session' : 'Brainstorm AI'}
                </span>
                <span className="text-[10px] font-medium text-muted-foreground transition-opacity opacity-0 group-hover:opacity-100">
                    {new Date(message.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>

            <div className={`max-w-[90%] sm:max-w-[85%] ${isUser ? '' : 'w-full'}`}>
                <div
                    className={`relative px-5 py-4 text-[14px] leading-relaxed transition-all duration-200 border ${isUser
                        ? 'bg-gradient-to-br from-primary to-primary-hover border-primary/80 text-primary-foreground rounded-2xl rounded-tr-sm shadow-lg shadow-primary/15'
                        : 'bg-surface border-border text-foreground rounded-2xl rounded-tl-sm shadow-sm'
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
                                            return <code className="font-mono text-[0.9em] bg-surface-raised px-1.5 py-0.5 rounded border border-border text-foreground" {...props}>{children}</code>;
                                        }

                                        return <CodeBlock className={className}>{children}</CodeBlock>;
                                    },
                                    pre({ children }) {
                                        return <>{children}</>;
                                    }
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap font-medium">{message.content}</div>
                    )}
                </div>

                {/* Actions Row */}
                {!isUser && (
                    <div className="flex items-center gap-4 mt-2 px-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                            onClick={() => setShowDebug(!showDebug)}
                            className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider transition-colors ${showDebug ? 'text-accent' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            <Eye size={12} />
                            <span>{showDebug ? 'Hide Technical Details' : 'View Technical Details'}</span>
                        </button>

                        <div className="h-2 w-px bg-border" />

                        <div className="flex items-center gap-2">
                            <button className="p-1 text-muted-foreground hover:text-foreground hover:bg-surface-raised rounded transition-colors">
                                <ThumbsUp size={12} />
                            </button>
                            <button className="p-1 text-muted-foreground hover:text-foreground hover:bg-surface-raised rounded transition-colors">
                                <ThumbsDown size={12} />
                            </button>
                        </div>
                    </div>
                )}

                {/* Debug Panel */}
                {showDebug && message.id && (
                    <div className="mt-4 border-t border-border pt-4 animate-slide-up">
                        <DebugPanel messageId={message.id} />
                    </div>
                )}
            </div>
        </div>
    );
}

import { useState } from 'react';
import { Activity, ArrowRight, Eye, EyeOff, Shield, Check, Terminal, Layout } from 'lucide-react';
import { updateSettings } from '../api';

interface WelcomeScreenProps {
    onComplete: () => void;
}

export function WelcomeScreen({ onComplete }: WelcomeScreenProps) {
    const [geminiKey, setGeminiKey] = useState('');
    const [claudeKey, setClaudeKey] = useState('');
    const [showGemini, setShowGemini] = useState(false);
    const [showClaude, setShowClaude] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleContinue = async () => {
        if (!geminiKey.trim()) {
            setError('Gemini API key is required to proceed.');
            return;
        }

        setSaving(true);
        setError(null);

        try {
            await updateSettings({
                gemini_api_key: geminiKey.trim(),
                anthropic_api_key: claudeKey.trim() || undefined,
            });
            setTimeout(onComplete, 500);
        } catch (e: any) {
            setError(e.message || 'Failed to verify and save API keys.');
            setSaving(false);
        }
    };

    return (
        <div className="h-screen w-full flex items-center justify-center bg-mesh relative overflow-hidden">
            {/* Decorative elements */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-72 h-72 rounded-full bg-primary/5 blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-accent/5 blur-3xl" />
            </div>
            <div className="max-w-md w-full p-6 animate-scale-in relative z-10">
                <div className="bg-surface/95 backdrop-blur-xl border border-border shadow-2xl shadow-primary/5 rounded-2xl overflow-hidden ring-1 ring-border/30">
                    {/* Header */}
                    <div className="p-8 pb-4 text-center">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-primary-hover flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary/20">
                            <Activity className="w-7 h-7 text-primary-foreground" />
                        </div>
                        <h1 className="text-2xl font-bold text-foreground mb-2 tracking-tight">Brainstorm AI</h1>
                        <p className="text-muted-foreground text-sm max-w-xs mx-auto leading-relaxed">
                            Professional local middleware for connecting advanced reasoning models to your workflow.
                        </p>
                    </div>

                    <div className="p-8 pt-4 space-y-6">
                        {/* Features List */}
                        <div className="flex items-center justify-between py-4 px-5 rounded-xl bg-surface-container/80 border border-border/80">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
                                    <Shield size={16} className="text-success" />
                                </div>
                                <span className="text-xs font-semibold text-foreground">Enterprise Privacy</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                                    <Terminal size={16} className="text-primary" />
                                </div>
                                <span className="text-xs font-semibold text-foreground">Local Only</span>
                            </div>
                        </div>

                        {/* Input Area */}
                        <div className="space-y-4">
                            <div className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Gemini API Key</label>
                                    <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="text-[10px] text-accent hover:underline font-medium">
                                        Get Key ↗
                                    </a>
                                </div>
                                <div className="relative">
                                    <input
                                        type={showGemini ? 'text' : 'password'}
                                        value={geminiKey}
                                        onChange={e => setGeminiKey(e.target.value)}
                                        placeholder="Enter Google AI Studio key"
                                        className="w-full bg-surface-container border border-border rounded-lg px-3 py-2.5 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:bg-surface focus:border-accent focus:ring-1 focus:ring-accent outline-none transition-all font-mono"
                                        autoFocus
                                    />
                                    <button
                                        onClick={() => setShowGemini(!showGemini)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Claude API Key <span className="text-muted-foreground/70 font-normal lowercase">(Optional)</span></label>
                                    <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="text-[10px] text-accent hover:underline font-medium">
                                        Get Key ↗
                                    </a>
                                </div>
                                <div className="relative">
                                    <input
                                        type={showClaude ? 'text' : 'password'}
                                        value={claudeKey}
                                        onChange={e => setClaudeKey(e.target.value)}
                                        placeholder="Enter Anthropic key"
                                        className="w-full bg-surface-container border border-border rounded-lg px-3 py-2.5 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:bg-surface focus:border-accent focus:ring-1 focus:ring-accent outline-none transition-all font-mono"
                                    />
                                    <button
                                        onClick={() => setShowClaude(!showClaude)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {error && (
                            <div className="p-3 bg-error/10 border border-error/20 rounded-lg text-error text-xs font-medium flex items-center gap-2">
                                <span className="w-1 h-3 bg-error rounded-full" />
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleContinue}
                            disabled={saving || !geminiKey.trim()}
                            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary to-primary-hover hover:opacity-95 text-primary-foreground rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/25 active:scale-[0.99]"
                        >
                            {saving ? (
                                <>
                                    <div className="w-3.5 h-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                                    <span>Configuring...</span>
                                </>
                            ) : (
                                <>
                                    <span>Setup Workspace</span>
                                    <ArrowRight size={16} />
                                </>
                            )}
                        </button>
                    </div>

                    <div className="px-8 py-4 bg-surface-container border-t border-border text-center">
                        <p className="text-[10px] text-muted-foreground font-medium">
                            Private instance. All execution is local and secure.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

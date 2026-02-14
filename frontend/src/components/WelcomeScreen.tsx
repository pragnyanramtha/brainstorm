import { useState } from 'react';
import { Sparkles, ArrowRight, Eye, EyeOff, Shield, Check, Cpu } from 'lucide-react';
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
            // Add a small delay for better UX
            setTimeout(onComplete, 800);
        } catch (e: any) {
            setError(e.message || 'Failed to verify and save API keys.');
            setSaving(false);
        }
    };

    return (
        <div className="h-screen w-full flex items-center justify-center bg-surface relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-accent/10 rounded-full blur-[120px] opacity-40 animate-pulse" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-purple-500/10 rounded-full blur-[150px] opacity-30 animate-pulse" style={{ animationDelay: '2s' }} />
            </div>

            <div className="max-w-xl w-full relative z-10 p-6 animate-scale-in">
                <div className="glass-card rounded-2xl border-white/10 shadow-2xl overflow-hidden backdrop-blur-xl">
                    {/* Header */}
                    <div className="p-8 text-center border-b border-white/5 bg-surface-raised/30">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-purple-600 flex items-center justify-center mx-auto mb-6 shadow-glow transform rotate-3 hover:rotate-6 transition-transform duration-500">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Middle Manager AI</h1>
                        <p className="text-text-secondary text-sm max-w-sm mx-auto leading-relaxed">
                            Your local intelligent middleware. Connects you to advanced reasoning models while keeping your data safe on your machine.
                        </p>
                    </div>

                    <div className="p-8 space-y-8 bg-surface/50">
                        {/* Features Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-2 p-3 rounded-xl bg-surface-raised/50 border border-white/5 hover:bg-surface-raised/80 transition-colors">
                                <Shield className="w-5 h-5 text-emerald-400" />
                                <div className="text-xs font-semibold text-text-primary">Privacy First</div>
                                <div className="text-[10px] text-text-muted leading-snug">Keys stored locally in .env</div>
                            </div>
                            <div className="flex flex-col gap-2 p-3 rounded-xl bg-surface-raised/50 border border-white/5 hover:bg-surface-raised/80 transition-colors">
                                <Cpu className="w-5 h-5 text-blue-400" />
                                <div className="text-xs font-semibold text-text-primary">Dual Engine</div>
                                <div className="text-[10px] text-text-muted leading-snug">Gemini + Claude support</div>
                            </div>
                        </div>

                        {/* Input Area */}
                        <div className="space-y-5">
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium text-text-secondary">Google Gemini API Key <span className="text-accent">*</span></label>
                                    <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="text-[10px] text-accent hover:underline flex items-center gap-1">
                                        Get Key <span className="opacity-50">↗</span>
                                    </a>
                                </div>
                                <div className="relative group">
                                    <input
                                        type={showGemini ? 'text' : 'password'}
                                        value={geminiKey}
                                        onChange={e => setGeminiKey(e.target.value)}
                                        placeholder="Enter AI Studio key here"
                                        className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3.5 pr-10 text-sm text-text-primary placeholder-text-muted/50 outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all font-mono"
                                        autoFocus
                                    />
                                    <button
                                        onClick={() => setShowGemini(!showGemini)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-primary transition-colors"
                                    >
                                        {showGemini ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium text-text-secondary">Anthropic Claude API Key <span className="text-text-muted text-xs font-normal">(optional)</span></label>
                                    <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="text-[10px] text-accent hover:underline flex items-center gap-1">
                                        Get Key <span className="opacity-50">↗</span>
                                    </a>
                                </div>
                                <div className="relative group">
                                    <input
                                        type={showClaude ? 'text' : 'password'}
                                        value={claudeKey}
                                        onChange={e => setClaudeKey(e.target.value)}
                                        placeholder="Enter Anthropic key here"
                                        className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3.5 pr-10 text-sm text-text-primary placeholder-text-muted/50 outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all font-mono"
                                    />
                                    <button
                                        onClick={() => setShowClaude(!showClaude)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-primary transition-colors"
                                    >
                                        {showClaude ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {error && (
                            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs font-medium flex items-center gap-2 animate-shake">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleContinue}
                            disabled={saving || !geminiKey.trim()}
                            className="group w-full flex items-center justify-center gap-2 px-6 py-4 bg-accent hover:bg-accent-hover text-white rounded-xl text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg shadow-accent/20"
                        >
                            {saving ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    <span>Verifying Configuration...</span>
                                </>
                            ) : (
                                <>
                                    <span>Start Using Middle Manager</span>
                                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </div>
                </div>

                <div className="mt-6 text-center">
                    <p className="text-[10px] text-text-muted opacity-60">
                        By continuing, you acknowledge that this is a local-only tool. <br />
                        No data is synced to the cloud.
                    </p>
                </div>
            </div>
        </div>
    );
}

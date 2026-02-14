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
        <div className="h-screen w-full flex items-center justify-center bg-surface-container relative">
            <div className="max-w-md w-full p-6 animate-scale-in">
                <div className="bg-white border border-slate-200 shadow-xl rounded-2xl overflow-hidden">
                    {/* Header */}
                    <div className="p-8 pb-4 text-center">
                        <div className="w-12 h-12 rounded-xl bg-slate-900 flex items-center justify-center mx-auto mb-6 shadow-sm">
                            <Activity className="w-6 h-6 text-white" />
                        </div>
                        <h1 className="text-2xl font-semibold text-slate-900 mb-2 tracking-tight">Middle Manager</h1>
                        <p className="text-slate-500 text-sm max-w-xs mx-auto leading-relaxed">
                            Professional local middleware for connecting advanced reasoning models to your workflow.
                        </p>
                    </div>

                    <div className="p-8 pt-4 space-y-6">
                        {/* Features List */}
                        <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-slate-50 border border-slate-100">
                            <div className="flex items-center gap-3">
                                <Shield size={16} className="text-slate-600" />
                                <span className="text-xs font-medium text-slate-700">Enterprise Privacy</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Terminal size={16} className="text-slate-600" />
                                <span className="text-xs font-medium text-slate-700">Local Only</span>
                            </div>
                        </div>

                        {/* Input Area */}
                        <div className="space-y-4">
                            <div className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Gemini API Key</label>
                                    <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="text-[10px] text-blue-600 hover:underline font-medium">
                                        Get Key ↗
                                    </a>
                                </div>
                                <div className="relative">
                                    <input
                                        type={showGemini ? 'text' : 'password'}
                                        value={geminiKey}
                                        onChange={e => setGeminiKey(e.target.value)}
                                        placeholder="Enter Google AI Studio key"
                                        className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 pr-10 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono"
                                        autoFocus
                                    />
                                    <button
                                        onClick={() => setShowGemini(!showGemini)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 transition-colors"
                                    >
                                        {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Claude API Key <span className="text-slate-400 font-normal lowercase">(Optional)</span></label>
                                    <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="text-[10px] text-blue-600 hover:underline font-medium">
                                        Get Key ↗
                                    </a>
                                </div>
                                <div className="relative">
                                    <input
                                        type={showClaude ? 'text' : 'password'}
                                        value={claudeKey}
                                        onChange={e => setClaudeKey(e.target.value)}
                                        placeholder="Enter Anthropic key"
                                        className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 pr-10 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono"
                                    />
                                    <button
                                        onClick={() => setShowClaude(!showClaude)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 transition-colors"
                                    >
                                        {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 border border-red-100 rounded-lg text-red-600 text-xs font-medium flex items-center gap-2">
                                <span className="w-1 h-3 bg-red-500 rounded-full" />
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleContinue}
                            disabled={saving || !geminiKey.trim()}
                            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                        >
                            {saving ? (
                                <>
                                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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

                    <div className="px-8 py-4 bg-slate-50 border-t border-slate-100 text-center">
                        <p className="text-[10px] text-slate-400 font-medium">
                            Private instance. All execution is local and secure.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}


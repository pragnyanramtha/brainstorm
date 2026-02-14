import { useState } from 'react';
import { Sparkles, ArrowRight, Eye, EyeOff } from 'lucide-react';
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
    const [error, setError] = useState('');

    const handleContinue = async () => {
        if (!geminiKey.trim()) {
            setError('Gemini API key is required');
            return;
        }

        setSaving(true);
        setError('');

        try {
            await updateSettings({
                gemini_api_key: geminiKey.trim(),
                anthropic_api_key: claudeKey.trim() || undefined,
            });
            onComplete();
        } catch (e: any) {
            setError(e.message || 'Failed to save keys');
        }
        setSaving(false);
    };

    return (
        <div className="h-screen flex items-center justify-center bg-surface px-4">
            <div className="max-w-md w-full space-y-8 animate-fade-in">
                {/* Logo & Title */}
                <div className="text-center space-y-3">
                    <div className="w-14 h-14 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto">
                        <Sparkles className="w-7 h-7 text-accent" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-text-primary">Middle Manager AI</h1>
                        <p className="text-text-secondary text-sm mt-1">
                            Your intelligent middleware between you and AI models. Everything runs locally.
                        </p>
                    </div>
                </div>

                {/* API Key Inputs */}
                <div className="space-y-4">
                    {/* Gemini */}
                    <div className="space-y-1.5">
                        <label className="text-sm text-text-secondary font-medium">
                            Google Gemini API Key <span className="text-accent">*</span>
                        </label>
                        <div className="relative">
                            <input
                                type={showGemini ? 'text' : 'password'}
                                value={geminiKey}
                                onChange={e => setGeminiKey(e.target.value)}
                                placeholder="Enter your Gemini API key"
                                className="w-full bg-surface-raised border border-surface-border rounded-lg px-3 py-2.5 pr-10 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent/50 transition-smooth"
                                autoFocus
                            />
                            <button
                                onClick={() => setShowGemini(!showGemini)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                            >
                                {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                            </button>
                        </div>
                        <a
                            href="https://aistudio.google.com/app/apikey"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-accent hover:underline"
                        >
                            Get a free key →
                        </a>
                    </div>

                    {/* Claude */}
                    <div className="space-y-1.5">
                        <label className="text-sm text-text-secondary font-medium">
                            Anthropic Claude API Key <span className="text-text-muted text-xs">(optional, recommended for code)</span>
                        </label>
                        <div className="relative">
                            <input
                                type={showClaude ? 'text' : 'password'}
                                value={claudeKey}
                                onChange={e => setClaudeKey(e.target.value)}
                                placeholder="Enter your Claude API key"
                                className="w-full bg-surface-raised border border-surface-border rounded-lg px-3 py-2.5 pr-10 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent/50 transition-smooth"
                            />
                            <button
                                onClick={() => setShowClaude(!showClaude)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                            >
                                {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                            </button>
                        </div>
                        <a
                            href="https://console.anthropic.com/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-accent hover:underline"
                        >
                            Get an API key →
                        </a>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Continue */}
                    <button
                        onClick={handleContinue}
                        disabled={saving || !geminiKey.trim()}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {saving ? 'Setting up...' : 'Continue'}
                        <ArrowRight size={16} />
                    </button>
                </div>

                {/* Privacy Note */}
                <p className="text-center text-text-muted text-xs leading-relaxed">
                    🔒 Keys are stored locally on your machine. They never leave your computer
                    except in direct API calls to Google and Anthropic.
                </p>
            </div>
        </div>
    );
}

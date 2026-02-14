import { useState, useEffect } from 'react';
import { X, Key, User, Info, Eye, EyeOff, ToggleLeft, ToggleRight } from 'lucide-react';
import { getSettings, updateSettings, saveProfile } from '../api';
import type { Settings } from '../types';

interface SettingsModalProps {
    onClose: () => void;
}

type Tab = 'api_keys' | 'tools' | 'profile' | 'about';

export function SettingsModal({ onClose }: SettingsModalProps) {
    const [tab, setTab] = useState<Tab>('api_keys');
    const [settings, setSettings] = useState<Settings | null>(null);
    const [geminiKey, setGeminiKey] = useState('');
    const [claudeKey, setClaudeKey] = useState('');
    const [showGemini, setShowGemini] = useState(false);
    const [showClaude, setShowClaude] = useState(false);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        (async () => {
            try {
                const data = await getSettings();
                setSettings(data);
            } catch { }
        })();
    }, []);

    const handleSaveKeys = async () => {
        setSaving(true);
        try {
            const update: any = {};
            if (geminiKey) update.gemini_api_key = geminiKey;
            if (claudeKey) update.anthropic_api_key = claudeKey;
            await updateSettings(update);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
            // Refresh settings
            const data = await getSettings();
            setSettings(data);
            setGeminiKey('');
            setClaudeKey('');
        } catch { }
        setSaving(false);
    };

    const tabs: { id: Tab; label: string; icon: any }[] = [
        { id: 'api_keys', label: 'API Keys', icon: Key },
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'about', label: 'About', icon: Info },
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in" onClick={onClose}>
            <div
                className="bg-surface-raised border border-surface-border rounded-xl w-[560px] max-h-[80vh] flex flex-col shadow-2xl animate-slide-up"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-3.5 border-b border-surface-border">
                    <h2 className="text-text-primary font-semibold text-sm">Settings</h2>
                    <button onClick={onClose} className="p-1 rounded-md hover:bg-surface-hover text-text-muted transition-smooth">
                        <X size={16} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex gap-0 px-5 border-b border-surface-border">
                    {tabs.map(t => (
                        <button
                            key={t.id}
                            onClick={() => setTab(t.id)}
                            className={`flex items-center gap-1.5 px-3 py-2.5 text-sm border-b-2 transition-smooth ${tab === t.id
                                    ? 'border-accent text-text-primary'
                                    : 'border-transparent text-text-muted hover:text-text-secondary'
                                }`}
                        >
                            <t.icon size={14} />
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                    {tab === 'api_keys' && (
                        <>
                            {/* Gemini */}
                            <div className="space-y-2">
                                <label className="text-sm text-text-secondary font-medium flex items-center justify-between">
                                    <span>Google Gemini API Key <span className="text-accent text-xs">(required)</span></span>
                                    {settings?.api_keys.gemini.configured && (
                                        <span className="text-xs text-emerald-400">✓ {settings.api_keys.gemini.masked}</span>
                                    )}
                                </label>
                                <div className="relative">
                                    <input
                                        type={showGemini ? 'text' : 'password'}
                                        value={geminiKey}
                                        onChange={e => setGeminiKey(e.target.value)}
                                        placeholder={settings?.api_keys.gemini.configured ? 'Enter new key to update' : 'Enter your API key'}
                                        className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 pr-10 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent/50 transition-smooth"
                                    />
                                    <button
                                        onClick={() => setShowGemini(!showGemini)}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                                    >
                                        {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                </div>
                                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="text-xs text-accent hover:underline">
                                    Get a free key →
                                </a>
                            </div>

                            {/* Claude */}
                            <div className="space-y-2">
                                <label className="text-sm text-text-secondary font-medium flex items-center justify-between">
                                    <span>Anthropic Claude API Key <span className="text-text-muted text-xs">(optional)</span></span>
                                    {settings?.api_keys.anthropic.configured && (
                                        <span className="text-xs text-emerald-400">✓ {settings.api_keys.anthropic.masked}</span>
                                    )}
                                </label>
                                <div className="relative">
                                    <input
                                        type={showClaude ? 'text' : 'password'}
                                        value={claudeKey}
                                        onChange={e => setClaudeKey(e.target.value)}
                                        placeholder={settings?.api_keys.anthropic.configured ? 'Enter new key to update' : 'Enter your API key'}
                                        className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 pr-10 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent/50 transition-smooth"
                                    />
                                    <button
                                        onClick={() => setShowClaude(!showClaude)}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                                    >
                                        {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                </div>
                                <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="text-xs text-accent hover:underline">
                                    Get an API key →
                                </a>
                            </div>

                            {(geminiKey || claudeKey) && (
                                <button
                                    onClick={handleSaveKeys}
                                    disabled={saving}
                                    className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-smooth disabled:opacity-50"
                                >
                                    {saving ? 'Saving...' : saved ? '✓ Saved!' : 'Save Keys'}
                                </button>
                            )}
                        </>
                    )}

                    {tab === 'profile' && settings?.user_profile && (
                        <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-text-muted block mb-1">Technical Level</label>
                                    <div className="text-sm text-text-primary capitalize">{settings.user_profile.technical_level.replace('_', ' ')}</div>
                                </div>
                                <div>
                                    <label className="text-xs text-text-muted block mb-1">Domain</label>
                                    <div className="text-sm text-text-primary">{settings.user_profile.domain || 'Not set'}</div>
                                </div>
                                <div>
                                    <label className="text-xs text-text-muted block mb-1">Role</label>
                                    <div className="text-sm text-text-primary">{settings.user_profile.role || 'Not set'}</div>
                                </div>
                                <div>
                                    <label className="text-xs text-text-muted block mb-1">Interactions</label>
                                    <div className="text-sm text-text-primary">{settings.user_profile.interaction_count}</div>
                                </div>
                            </div>
                            {settings.user_profile.stack.length > 0 && (
                                <div>
                                    <label className="text-xs text-text-muted block mb-1">Tech Stack</label>
                                    <div className="flex flex-wrap gap-1">
                                        {settings.user_profile.stack.map(s => (
                                            <span key={s} className="px-2 py-0.5 bg-accent/10 text-accent rounded text-xs">{s}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {tab === 'profile' && !settings?.user_profile && (
                        <p className="text-text-muted text-sm">No profile yet. Have a chat and the system will learn about you!</p>
                    )}

                    {tab === 'about' && (
                        <div className="space-y-4">
                            <div>
                                <h3 className="text-text-primary font-medium text-sm mb-1">Middle Manager AI</h3>
                                <p className="text-text-secondary text-xs">Version 0.1.0</p>
                            </div>
                            <div className="bg-surface border border-surface-border rounded-lg p-3 space-y-2">
                                <p className="text-sm text-text-secondary leading-relaxed">
                                    🔒 <strong className="text-text-primary">Everything runs locally.</strong> Your data never leaves your machine.
                                    API keys are stored in a local file and only used for direct calls to Google and Anthropic.
                                </p>
                                <p className="text-sm text-text-secondary leading-relaxed">
                                    No cloud. No accounts. No telemetry. No tracking.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

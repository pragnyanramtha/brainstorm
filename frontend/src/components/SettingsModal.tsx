import { useState, useEffect } from 'react';
import { X, Key, User, Info, Eye, EyeOff, Check, Shield, Cpu, Activity, History } from 'lucide-react';
import { getSettings, updateSettings } from '../api';
import type { Settings } from '../types';

interface SettingsModalProps {
    onClose: () => void;
}

type Tab = 'api_keys' | 'profile' | 'about';

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

            // Refresh
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" />

            <div
                className="relative bg-surface border border-surface-border rounded-2xl w-full max-w-xl flex flex-col shadow-2xl animate-scale-in overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-surface-border bg-surface-raised/30">
                    <h2 className="text-text-primary font-semibold text-lg tracking-tight">Settings</h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="flex h-[500px]">
                    {/* Sidebar Tabs */}
                    <div className="w-48 border-r border-surface-border bg-surface-raised/20 p-2 space-y-1">
                        {tabs.map(t => (
                            <button
                                key={t.id}
                                onClick={() => setTab(t.id)}
                                className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${tab === t.id
                                        ? 'bg-accent text-white shadow-lg shadow-accent/20'
                                        : 'text-text-secondary hover:bg-surface-overlay hover:text-text-primary'
                                    }`}
                            >
                                <t.icon size={16} />
                                {t.label}
                            </button>
                        ))}
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 overflow-y-auto p-6 bg-surface">
                        {tab === 'api_keys' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="space-y-1">
                                    <h3 className="text-sm font-medium text-text-primary flex items-center gap-2">
                                        <Shield size={16} className="text-accent" />
                                        Secure Storage
                                    </h3>
                                    <p className="text-xs text-text-muted leading-relaxed">
                                        API keys are stored locally on your device in <code className="bg-surface-raised px-1 py-0.5 rounded border border-surface-border text-text-secondary">.env</code>.
                                        They are never sent to any middleware server.
                                    </p>
                                </div>

                                <div className="space-y-5">
                                    {/* Gemini */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-sm font-medium text-text-secondary">Google Gemini API Key</label>
                                            {settings?.api_keys.gemini.configured && (
                                                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                                                    <Check size={10} /> Active
                                                </span>
                                            )}
                                        </div>
                                        <div className="relative group">
                                            <input
                                                type={showGemini ? 'text' : 'password'}
                                                value={geminiKey}
                                                onChange={e => setGeminiKey(e.target.value)}
                                                placeholder={settings?.api_keys.gemini.configured ? '••••••••••••••••' : 'Enter AI Studio key'}
                                                className="w-full bg-surface-raised border border-surface-border rounded-xl px-4 py-3 pr-10 text-sm text-text-primary placeholder-text-muted/50 outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all font-mono"
                                            />
                                            <button
                                                onClick={() => setShowGemini(!showGemini)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-text-muted hover:text-text-primary transition-colors"
                                            >
                                                {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                        <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="inline-flex items-center gap-1 text-xs text-accent hover:text-accent-hover hover:underline mt-1.5 transition-colors">
                                            Get API Key <span className="opacity-50">↗</span>
                                        </a>
                                    </div>

                                    {/* Claude */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-sm font-medium text-text-secondary">Anthropic Claude API Key</label>
                                            {settings?.api_keys.anthropic.configured && (
                                                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                                                    <Check size={10} /> Active
                                                </span>
                                            )}
                                        </div>
                                        <div className="relative group">
                                            <input
                                                type={showClaude ? 'text' : 'password'}
                                                value={claudeKey}
                                                onChange={e => setClaudeKey(e.target.value)}
                                                placeholder={settings?.api_keys.anthropic.configured ? '••••••••••••••••' : 'Enter Anthropic key'}
                                                className="w-full bg-surface-raised border border-surface-border rounded-xl px-4 py-3 pr-10 text-sm text-text-primary placeholder-text-muted/50 outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all font-mono"
                                            />
                                            <button
                                                onClick={() => setShowClaude(!showClaude)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-text-muted hover:text-text-primary transition-colors"
                                            >
                                                {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                        <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="inline-flex items-center gap-1 text-xs text-accent hover:text-accent-hover hover:underline mt-1.5 transition-colors">
                                            Get API Key <span className="opacity-50">↗</span>
                                        </a>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-surface-border">
                                    <button
                                        onClick={handleSaveKeys}
                                        disabled={saving || (!geminiKey && !claudeKey)}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-accent hover:bg-accent-hover active:bg-accent-muted text-white rounded-xl text-sm font-medium transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg shadow-accent/20"
                                    >
                                        {saving ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Check size={16} />}
                                        {saving ? 'Verifying & Saving...' : saved ? 'Saved Successfully' : 'Save Changes'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {tab === 'profile' && (
                            <div className="space-y-6 animate-fade-in">
                                <div className="space-y-1">
                                    <h3 className="text-sm font-medium text-text-primary flex items-center gap-2">
                                        <User size={16} className="text-accent" />
                                        User Profile
                                    </h3>
                                    <p className="text-xs text-text-muted leading-relaxed">
                                        This info helps the AI tailor its responses to your expertise level and preferred tools.
                                    </p>
                                </div>

                                {settings?.user_profile ? (
                                    <div className="grid gap-3">
                                        <div className="glass-card bg-surface-raised/50 p-4 rounded-xl space-y-3 border-white/5">
                                            <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                                                <Activity size={12} />
                                                <span>Stats</span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <div className="text-[10px] text-text-muted mb-0.5">Interaction Count</div>
                                                    <div className="text-lg font-mono text-text-primary">{settings.user_profile.interaction_count}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-text-muted mb-0.5">Role</div>
                                                    <div className="text-sm text-text-primary font-medium">{settings.user_profile.role || 'Developer'}</div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="glass-card bg-surface-raised/50 p-4 rounded-xl space-y-3 border-white/5">
                                            <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                                                <Cpu size={12} />
                                                <span>Preferences</span>
                                            </div>
                                            <div className="space-y-3">
                                                <div>
                                                    <div className="text-[10px] text-text-muted mb-1">Technical Level</div>
                                                    <div className="inline-flex px-2 py-1 bg-accent/10 border border-accent/20 rounded text-xs text-accent font-medium capitalize">
                                                        {settings.user_profile.technical_level.replace('_', ' ')}
                                                    </div>
                                                </div>
                                                {settings.user_profile.stack.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] text-text-muted mb-1.5">Tech Stack</div>
                                                        <div className="flex flex-wrap gap-1.5">
                                                            {settings.user_profile.stack.map(s => (
                                                                <span key={s} className="px-2 py-1 bg-surface-raised border border-surface-border rounded text-[11px] text-text-secondary">
                                                                    {s}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center py-10 bg-surface-raised/30 rounded-xl border border-dashed border-surface-border">
                                        <User size={24} className="mx-auto text-text-muted mb-2 opacity-50" />
                                        <p className="text-sm text-text-secondary font-medium">No profile generated yet</p>
                                        <p className="text-xs text-text-muted mt-1 max-w-[200px] mx-auto">
                                            Start chatting with Brainstorm AI, and it will automatically learn your preferences.
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                        {tab === 'about' && (
                            <div className="space-y-6 animate-fade-in">
                                <div className="text-center py-4">
                                    <div className="w-16 h-16 bg-gradient-to-br from-accent to-purple-600 rounded-2xl mx-auto flex items-center justify-center shadow-glow mb-4">
                                        <span className="text-2xl font-bold text-white">BS</span>
                                    </div>
                                    <h3 className="text-lg font-bold text-text-primary">Brainstorm AI</h3>
                                    <p className="text-sm text-text-muted mt-1">Version 0.1.0 • Early Access</p>
                                </div>

                                <div className="space-y-3">
                                    <div className="glass-card bg-surface-raised p-4 rounded-xl border-white/5">
                                        <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center gap-2">
                                            <Shield size={14} className="text-emerald-400" />
                                            Privacy First
                                        </h4>
                                        <p className="text-xs text-text-muted leading-relaxed">
                                            Brainstorm AI runs entirely locally. Your code, projects, and conversations never leave your machine except when strictly required to call LLM APIs (Gemini/Claude).
                                        </p>
                                    </div>

                                    <div className="glass-card bg-surface-raised p-4 rounded-xl border-white/5">
                                        <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center gap-2">
                                            <History size={14} className="text-blue-400" />
                                            Local History
                                        </h4>
                                        <p className="text-xs text-text-muted leading-relaxed">
                                            All chat history and project metadata are stored in standard JSON files within your project directories. You own your data.
                                        </p>
                                    </div>
                                </div>

                                <div className="text-center pt-4">
                                    <a href="#" className="text-xs text-text-muted hover:text-text-primary underline transition-colors">
                                        View Source Code
                                    </a>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

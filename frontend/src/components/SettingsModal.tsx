import { useState, useEffect } from 'react';
import { X, Key, User, Info, Eye, EyeOff, Check, Shield, Cpu, Activity, History, Lock, Server } from 'lucide-react';
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
        { id: 'api_keys', label: 'API Credentials', icon: Key },
        { id: 'profile', label: 'User Profile', icon: User },
        { id: 'about', label: 'System Info', icon: Info },
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            {/* Backdrop */}
            <div className="absolute inset-0 bg-background/50 backdrop-blur-sm animate-fade-in" />

            <div
                className="relative bg-surface border border-border rounded-lg w-full max-w-2xl flex flex-col shadow-xl animate-scale-in overflow-hidden ring-1 ring-border/50"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-container">
                    <div className="flex items-center gap-2">
                        <div className="p-1 rounded bg-surface-raised text-muted-foreground">
                            <Server size={16} />
                        </div>
                        <h2 className="text-foreground font-bold text-sm uppercase tracking-wide">System Configuration</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-md hover:bg-surface-raised text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <X size={16} />
                    </button>
                </div>

                <div className="flex h-[500px]">
                    {/* Sidebar Tabs */}
                    <div className="w-56 border-r border-border bg-surface-container p-3 space-y-1">
                        {tabs.map(t => (
                            <button
                                key={t.id}
                                onClick={() => setTab(t.id)}
                                className={`w-full flex items-center gap-3 px-3 py-2 text-xs font-semibold rounded-md transition-all duration-200 ${tab === t.id
                                    ? 'bg-surface text-foreground shadow-sm border border-border'
                                    : 'text-muted-foreground hover:bg-surface-raised hover:text-foreground'
                                    }`}
                            >
                                <t.icon size={14} className={tab === t.id ? 'text-primary' : 'text-muted-foreground'} />
                                {t.label}
                            </button>
                        ))}
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 overflow-y-auto p-8 bg-surface">
                        {tab === 'api_keys' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="space-y-1.5 border-b border-border pb-4">
                                    <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                                        <Lock size={16} className="text-muted-foreground" />
                                        Credential Management
                                    </h3>
                                    <p className="text-xs text-muted-foreground leading-relaxed max-w-sm">
                                        API keys are encrypted and stored locally in <code className="bg-surface-container px-1 py-0.5 rounded border border-border text-foreground font-mono">.env</code>.
                                    </p>
                                </div>

                                <div className="space-y-6">
                                    {/* Gemini */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Google Gemini API Key</label>
                                            {settings?.api_keys.gemini.configured && (
                                                <span className="flex items-center gap-1 text-[10px] font-bold text-success bg-success/10 px-2 py-0.5 rounded border border-success/20 uppercase tracking-wide">
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
                                                className="w-full bg-surface-container border border-border rounded-lg px-3 py-2.5 pr-10 text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all font-mono"
                                            />
                                            <button
                                                onClick={() => setShowGemini(!showGemini)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-surface-raised text-muted-foreground hover:text-foreground transition-colors"
                                            >
                                                {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                        <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="inline-flex items-center gap-1 text-[10px] uppercase font-bold text-accent hover:text-accent-foreground hover:underline mt-1 transition-colors tracking-wide">
                                            Generate Key <span className="opacity-50">↗</span>
                                        </a>
                                    </div>

                                    {/* Claude */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Anthropic Claude API Key</label>
                                            {settings?.api_keys.anthropic.configured && (
                                                <span className="flex items-center gap-1 text-[10px] font-bold text-success bg-success/10 px-2 py-0.5 rounded border border-success/20 uppercase tracking-wide">
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
                                                className="w-full bg-surface-container border border-border rounded-lg px-3 py-2.5 pr-10 text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all font-mono"
                                            />
                                            <button
                                                onClick={() => setShowClaude(!showClaude)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-surface-raised text-muted-foreground hover:text-foreground transition-colors"
                                            >
                                                {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                        <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="inline-flex items-center gap-1 text-[10px] uppercase font-bold text-accent hover:text-accent-foreground hover:underline mt-1 transition-colors tracking-wide">
                                            Generate Key <span className="opacity-50">↗</span>
                                        </a>
                                    </div>
                                </div>

                                <div className="pt-6 border-t border-border">
                                    <button
                                        onClick={handleSaveKeys}
                                        disabled={saving || (!geminiKey && !claudeKey)}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-hover active:bg-primary-hover text-primary-foreground rounded-lg text-xs font-bold uppercase tracking-widest transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                                    >
                                        {saving ? <div className="w-3 h-3 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" /> : <div className="w-3 h-3 bg-primary-foreground rounded-full" />}
                                        {saving ? 'Verifying...' : saved ? 'Configuration Saved' : 'Save Configuration'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {tab === 'profile' && (
                            <div className="space-y-6 animate-fade-in">
                                <div className="space-y-1.5 border-b border-border pb-4">
                                    <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                                        <User size={16} className="text-muted-foreground" />
                                        User Telemetry
                                    </h3>
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        Profile data used for response contextualization.
                                    </p>
                                </div>

                                {settings?.user_profile ? (
                                    <div className="grid gap-4">
                                        <div className="bg-surface-container border border-border rounded-lg p-5 space-y-4">
                                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                                <Activity size={12} />
                                                <span>Session Metrics</span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Interactions</div>
                                                    <div className="text-xl font-mono text-foreground">{settings.user_profile.interaction_count}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Role</div>
                                                    <div className="text-sm text-foreground font-semibold">{settings.user_profile.role || 'Developer'}</div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-surface-container border border-border rounded-lg p-5 space-y-4">
                                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                                <Cpu size={12} />
                                                <span>Context Configuration</span>
                                            </div>
                                            <div className="space-y-4">
                                                <div>
                                                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1.5">Technical Proficiency</div>
                                                    <div className="inline-flex px-2 py-1 bg-surface border border-border rounded text-xs text-foreground font-semibold uppercase tracking-wide">
                                                        {settings.user_profile.technical_level.replace('_', ' ')}
                                                    </div>
                                                </div>
                                                {settings.user_profile.stack.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Tech Stack Detected</div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {settings.user_profile.stack.map(s => (
                                                                <span key={s} className="px-2 py-1 bg-surface border border-border rounded text-[10px] font-bold text-muted-foreground uppercase tracking-wide">
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
                                    <div className="text-center py-12 bg-surface-container rounded-lg border border-dashed border-border">
                                        <div className="w-10 h-10 bg-surface rounded-lg border border-border mx-auto flex items-center justify-center mb-3">
                                            <User size={20} className="text-muted-foreground" />
                                        </div>
                                        <p className="text-xs font-bold text-foreground uppercase tracking-wide">Profile Not Initialized</p>
                                        <p className="text-xs text-muted-foreground mt-1 max-w-[200px] mx-auto">
                                            Interact with the system to generate a profile.
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                        {tab === 'about' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="text-center py-6 border-b border-border">
                                    <div className="w-12 h-12 bg-primary rounded-lg mx-auto flex items-center justify-center shadow-lg mb-4">
                                        <span className="text-xl font-bold text-primary-foreground tracking-tighter">B</span>
                                    </div>
                                    <h3 className="text-sm font-bold text-foreground uppercase tracking-widest">Brainstorm</h3>
                                    <p className="text-xs text-muted-foreground mt-1 font-mono">v0.1.0-alpha</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="bg-surface-container p-4 rounded-lg border border-border">
                                        <h4 className="text-xs font-bold text-foreground mb-2 flex items-center gap-2 uppercase tracking-wide">
                                            <Shield size={12} className="text-muted-foreground" />
                                            Privacy Architecture
                                        </h4>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            Local-first execution environment. Code generation and project metadata remain on-device. LLM interaction occurs via secure HTTPS TLS 1.3 channels directly to provider APIs.
                                        </p>
                                    </div>

                                    <div className="bg-surface-container p-4 rounded-lg border border-border">
                                        <h4 className="text-xs font-bold text-foreground mb-2 flex items-center gap-2 uppercase tracking-wide">
                                            <History size={12} className="text-muted-foreground" />
                                            Data Sovereignty
                                        </h4>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            Session history and configuration persists in standard JSON format within the project root (`.brainstorm/`).
                                        </p>
                                    </div>
                                </div>

                                <div className="text-center pt-2">
                                    <a href="#" className="text-[10px] font-bold text-muted-foreground hover:text-foreground uppercase tracking-widest transition-colors">
                                        Repository
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

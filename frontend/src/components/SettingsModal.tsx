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
            <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px] animate-fade-in" />

            <div
                className="relative bg-white border border-slate-200 rounded-lg w-full max-w-2xl flex flex-col shadow-xl animate-scale-in overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50">
                    <div className="flex items-center gap-2">
                        <div className="p-1 rounded bg-slate-200 text-slate-600">
                            <Server size={16} />
                        </div>
                        <h2 className="text-slate-900 font-bold text-sm uppercase tracking-wide">System Configuration</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-md hover:bg-slate-200 text-slate-400 hover:text-slate-900 transition-colors"
                    >
                        <X size={16} />
                    </button>
                </div>

                <div className="flex h-[500px]">
                    {/* Sidebar Tabs */}
                    <div className="w-56 border-r border-slate-100 bg-slate-50 p-3 space-y-1">
                        {tabs.map(t => (
                            <button
                                key={t.id}
                                onClick={() => setTab(t.id)}
                                className={`w-full flex items-center gap-3 px-3 py-2 text-xs font-semibold rounded-md transition-all duration-200 ${tab === t.id
                                    ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                                    : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
                                    }`}
                            >
                                <t.icon size={14} className={tab === t.id ? 'text-slate-900' : 'text-slate-400'} />
                                {t.label}
                            </button>
                        ))}
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 overflow-y-auto p-8 bg-white">
                        {tab === 'api_keys' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="space-y-1.5 border-b border-slate-100 pb-4">
                                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                                        <Lock size={16} className="text-slate-400" />
                                        Credential Management
                                    </h3>
                                    <p className="text-xs text-slate-500 leading-relaxed max-w-sm">
                                        API keys are encrypted and stored locally in <code className="bg-slate-100 px-1 py-0.5 rounded border border-slate-200 text-slate-700 font-mono">.env</code>.
                                    </p>
                                </div>

                                <div className="space-y-6">
                                    {/* Gemini */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Google Gemini API Key</label>
                                            {settings?.api_keys.gemini.configured && (
                                                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 uppercase tracking-wide">
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
                                                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2.5 pr-10 text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-400 transition-all font-mono"
                                            />
                                            <button
                                                onClick={() => setShowGemini(!showGemini)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                                            >
                                                {showGemini ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                        <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" className="inline-flex items-center gap-1 text-[10px] uppercase font-bold text-blue-600 hover:text-blue-700 hover:underline mt-1 transition-colors tracking-wide">
                                            Generate Key <span className="opacity-50">↗</span>
                                        </a>
                                    </div>

                                    {/* Claude */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Anthropic Claude API Key</label>
                                            {settings?.api_keys.anthropic.configured && (
                                                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 uppercase tracking-wide">
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
                                                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2.5 pr-10 text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-400 transition-all font-mono"
                                            />
                                            <button
                                                onClick={() => setShowClaude(!showClaude)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                                            >
                                                {showClaude ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                        <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="inline-flex items-center gap-1 text-[10px] uppercase font-bold text-blue-600 hover:text-blue-700 hover:underline mt-1 transition-colors tracking-wide">
                                            Generate Key <span className="opacity-50">↗</span>
                                        </a>
                                    </div>
                                </div>

                                <div className="pt-6 border-t border-slate-100">
                                    <button
                                        onClick={handleSaveKeys}
                                        disabled={saving || (!geminiKey && !claudeKey)}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white rounded-lg text-xs font-bold uppercase tracking-widest transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                                    >
                                        {saving ? <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <div className="w-3 h-3 bg-white rounded-full" />}
                                        {saving ? 'Verifying...' : saved ? 'Configuration Saved' : 'Save Configuration'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {tab === 'profile' && (
                            <div className="space-y-6 animate-fade-in">
                                <div className="space-y-1.5 border-b border-slate-100 pb-4">
                                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                                        <User size={16} className="text-slate-400" />
                                        User Telemetry
                                    </h3>
                                    <p className="text-xs text-slate-500 leading-relaxed">
                                        Profile data used for response contextualization.
                                    </p>
                                </div>

                                {settings?.user_profile ? (
                                    <div className="grid gap-4">
                                        <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 space-y-4">
                                            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                                <Activity size={12} />
                                                <span>Session Metrics</span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Interactions</div>
                                                    <div className="text-xl font-mono text-slate-900">{settings.user_profile.interaction_count}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Role</div>
                                                    <div className="text-sm text-slate-900 font-semibold">{settings.user_profile.role || 'Developer'}</div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 space-y-4">
                                            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                                <Cpu size={12} />
                                                <span>Context Configuration</span>
                                            </div>
                                            <div className="space-y-4">
                                                <div>
                                                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Technical Proficiency</div>
                                                    <div className="inline-flex px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-700 font-semibold uppercase tracking-wide">
                                                        {settings.user_profile.technical_level.replace('_', ' ')}
                                                    </div>
                                                </div>
                                                {settings.user_profile.stack.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Tech Stack Detected</div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {settings.user_profile.stack.map(s => (
                                                                <span key={s} className="px-2 py-1 bg-white border border-slate-200 rounded text-[10px] font-bold text-slate-600 uppercase tracking-wide">
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
                                    <div className="text-center py-12 bg-slate-50 rounded-lg border border-dashed border-slate-200">
                                        <div className="w-10 h-10 bg-white rounded-lg border border-slate-200 mx-auto flex items-center justify-center mb-3">
                                            <User size={20} className="text-slate-300" />
                                        </div>
                                        <p className="text-xs font-bold text-slate-900 uppercase tracking-wide">Profile Not Initialized</p>
                                        <p className="text-xs text-slate-500 mt-1 max-w-[200px] mx-auto">
                                            Interact with the system to generate a profile.
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                        {tab === 'about' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="text-center py-6 border-b border-slate-100">
                                    <div className="w-12 h-12 bg-slate-900 rounded-lg mx-auto flex items-center justify-center shadow-lg mb-4">
                                        <span className="text-xl font-bold text-white tracking-tighter">B</span>
                                    </div>
                                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest">Brainstorm</h3>
                                    <p className="text-xs text-slate-500 mt-1 font-mono">v0.1.0-alpha</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                                        <h4 className="text-xs font-bold text-slate-900 mb-2 flex items-center gap-2 uppercase tracking-wide">
                                            <Shield size={12} className="text-slate-500" />
                                            Privacy Architecture
                                        </h4>
                                        <p className="text-xs text-slate-500 leading-relaxed">
                                            Local-first execution environment. Code generation and project metadata remain on-device. LLM interaction occurs via secure HTTPS TLS 1.3 channels directly to provider APIs.
                                        </p>
                                    </div>

                                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                                        <h4 className="text-xs font-bold text-slate-900 mb-2 flex items-center gap-2 uppercase tracking-wide">
                                            <History size={12} className="text-slate-500" />
                                            Data Sovereignty
                                        </h4>
                                        <p className="text-xs text-slate-500 leading-relaxed">
                                            Session history and configuration persists in standard JSON format within the project root (`.brainstorm/`).
                                        </p>
                                    </div>
                                </div>

                                <div className="text-center pt-2">
                                    <a href="#" className="text-[10px] font-bold text-slate-400 hover:text-slate-900 uppercase tracking-widest transition-colors">
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

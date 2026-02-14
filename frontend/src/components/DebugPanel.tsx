import { useState, useEffect } from 'react';
import { getDebugInfo } from '../api';
import { Brain, Zap, Wrench, Target, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';
import type { DebugInfo } from '../types';

interface DebugPanelProps {
    messageId: string;
}

export function DebugPanel({ messageId }: DebugPanelProps) {
    const [debug, setDebug] = useState<DebugInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;
        (async () => {
            try {
                const data = await getDebugInfo(messageId);
                if (mounted) setDebug(data);
            } catch (e: any) {
                if (mounted) setError(e.message || 'Failed to load debug info');
            } finally {
                if (mounted) setLoading(false);
            }
        })();
        return () => { mounted = false; };
    }, [messageId]);

    if (loading) {
        return (
            <div className="glass-card rounded-xl p-4 animate-fade-in flex items-center gap-3">
                <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                <span className="text-text-muted text-xs font-medium">Analyzing process trace...</span>
            </div>
        );
    }

    if (error || !debug) {
        return (
            <div className="glass-card rounded-xl p-4 animate-fade-in border-red-500/20 bg-red-500/5 flex items-center gap-2 text-red-400">
                <AlertCircle size={14} />
                <span className="text-xs">{error || 'Trace data unavailable'}</span>
            </div>
        );
    }

    return (
        <div className="glass-card rounded-xl p-5 space-y-6 animate-slide-up text-sm backdrop-blur-2xl">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-surface-raised border border-white/10">
                        <Brain size={14} className="text-accent" />
                    </div>
                    <div>
                        <div className="text-xs font-semibold text-text-primary">Reasoning Trace</div>
                        <div className="text-[10px] text-text-muted">{debug.model_used || 'Unknown Model'}</div>
                    </div>
                </div>
                {debug.intake_analysis.confidence_score !== undefined && (
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-surface-raised border border-white/5">
                        <CheckCircle2 size={12} className="text-emerald-400" />
                        <span className="text-[10px] font-medium text-text-secondary">{debug.intake_analysis.confidence_score}% Confidence</span>
                    </div>
                )}
            </div>

            <div className="grid gap-6">
                {/* Intake Analysis */}
                {debug.intake_analysis.interpreted_intent && (
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-xs font-medium text-text-secondary uppercase tracking-wider">
                            <Target size={12} />
                            <span>Analysis</span>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-surface-raised/50 rounded-lg p-3 border border-white/5">
                                <span className="text-[10px] text-text-muted block mb-1">Intent</span>
                                <span className="text-xs text-text-primary font-medium">{debug.intake_analysis.interpreted_intent}</span>
                            </div>
                            <div className="bg-surface-raised/50 rounded-lg p-3 border border-white/5">
                                <span className="text-[10px] text-text-muted block mb-1">Task Type</span>
                                <span className="text-xs text-text-primary font-medium capitalize">{(debug.intake_analysis.task_type || 'Unknown').replace('_', ' ')}</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs">
                            <span className="text-text-muted">Complexity:</span>
                            <div className="flex-1 h-1.5 bg-surface-raised rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-emerald-400 to-accent"
                                    style={{ width: `${((debug.intake_analysis.complexity || 0) / 10) * 100}%` }}
                                />
                            </div>
                            <span className="text-text-primary font-mono">{debug.intake_analysis.complexity || 0}/10</span>
                        </div>
                    </div>
                )}

                {/* Skills & Tools */}
                {(debug.skills_applied.length > 0 || debug.mcps_used.length > 0) && (
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-xs font-medium text-text-secondary uppercase tracking-wider">
                            <Wrench size={12} />
                            <span>Execution</span>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {debug.skills_applied.map(skill => (
                                <div key={skill} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-accent/10 border border-accent/20 text-accent text-xs">
                                    <Zap size={10} />
                                    {skill}
                                </div>
                            ))}
                            {debug.mcps_used.map(mcp => (
                                <div key={mcp} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs">
                                    <Wrench size={10} />
                                    {mcp}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Optimized Prompt */}
                {debug.optimized_prompt && (
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-xs font-medium text-text-secondary uppercase tracking-wider">
                            <ChevronRight size={12} />
                            <span>Optimized Prompt</span>
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-surface-raised/10 pointer-events-none" />
                            <pre className="glass-card bg-surface-raised/30 p-4 rounded-lg text-[10px] font-mono leading-relaxed text-text-muted overflow-x-auto max-h-[200px] scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                                {debug.optimized_prompt}
                            </pre>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

import { useState, useEffect } from 'react';
import { getDebugInfo } from '../api';
import { Activity, Database, Wrench, Target, ChevronRight, CheckCircle2, AlertCircle, Terminal, Cpu, Layers } from 'lucide-react';
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
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex items-center gap-3">
                <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Retrieving Telemetry...</span>
            </div>
        );
    }

    if (error || !debug) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-600">
                <AlertCircle size={14} />
                <span className="text-xs font-medium">{error || 'Trace data unavailable'}</span>
            </div>
        );
    }

    return (
        <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-6 shadow-sm text-sm animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                        <Activity size={16} />
                    </div>
                    <div>
                        <div className="text-xs font-bold text-slate-800 uppercase tracking-wider">Execution Telemetry</div>
                        <div className="text-[10px] font-mono text-slate-500 mt-0.5">{debug.model_used || 'UNKNOWN_MODEL_ID'}</div>
                    </div>
                </div>
                {debug.intake_analysis.confidence_score !== undefined && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-50 border border-slate-200">
                        <CheckCircle2 size={12} className={(debug.intake_analysis.confidence_score || 0) > 80 ? "text-emerald-600" : "text-amber-600"} />
                        <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{debug.intake_analysis.confidence_score}% Match</span>
                    </div>
                )}
            </div>

            <div className="grid gap-6">
                {/* Intake Analysis */}
                {debug.intake_analysis.interpreted_intent && (
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                            <Target size={12} />
                            <span>Request Analysis</span>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-slate-50 rounded-md p-3 border border-slate-100">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Intent Detected</span>
                                <span className="text-xs text-slate-700 font-medium leading-relaxed">{debug.intake_analysis.interpreted_intent}</span>
                            </div>
                            <div className="bg-slate-50 rounded-md p-3 border border-slate-100">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Operation Type</span>
                                <span className="text-xs text-slate-700 font-mono font-medium capitalize">{(debug.intake_analysis.task_type || 'generic_op').replace('_', ' ')}</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 text-xs bg-slate-50 px-3 py-2 rounded-md border border-slate-100">
                            <span className="text-slate-500 font-medium">Complexity score:</span>
                            <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-slate-600 rounded-full"
                                    style={{ width: `${((debug.intake_analysis.complexity || 0) / 10) * 100}%` }}
                                />
                            </div>
                            <span className="text-slate-700 font-mono font-bold">{debug.intake_analysis.complexity || 0}/10</span>
                        </div>
                    </div>
                )}

                {/* Skills & Tools */}
                {(debug.skills_applied.length > 0 || debug.mcps_used.length > 0) && (
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                            <Cpu size={12} />
                            <span>System Resources</span>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {debug.skills_applied.map(skill => (
                                <div key={skill} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-blue-50 border border-blue-100 text-blue-700 text-[11px] font-semibold uppercase tracking-wide">
                                    <Layers size={10} />
                                    {skill}
                                </div>
                            ))}
                            {debug.mcps_used.map(mcp => (
                                <div key={mcp} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-100 border border-slate-200 text-slate-600 text-[11px] font-semibold uppercase tracking-wide">
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
                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                            <Terminal size={12} />
                            <span>Context Contextualization</span>
                        </div>
                        <div className="relative group">
                            <pre className="bg-slate-50 border border-slate-200 p-4 rounded-lg text-[10px] font-mono leading-relaxed text-slate-600 overflow-x-auto max-h-[200px]">
                                {debug.optimized_prompt}
                            </pre>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

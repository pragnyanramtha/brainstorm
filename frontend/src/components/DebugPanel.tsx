import { useState, useEffect } from 'react';
import { getDebugInfo } from '../api';
import { Brain, Zap, Wrench, Target } from 'lucide-react';
import type { DebugInfo } from '../types';

interface DebugPanelProps {
    messageId: string;
}

export function DebugPanel({ messageId }: DebugPanelProps) {
    const [debug, setDebug] = useState<DebugInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        (async () => {
            try {
                const data = await getDebugInfo(messageId);
                setDebug(data);
            } catch (e: any) {
                setError(e.message || 'Failed to load debug info');
            } finally {
                setLoading(false);
            }
        })();
    }, [messageId]);

    if (loading) {
        return (
            <div className="mt-2 bg-surface border border-surface-border rounded-lg p-3 animate-fade-in">
                <span className="text-text-muted text-xs">Loading debug info...</span>
            </div>
        );
    }

    if (error || !debug) {
        return (
            <div className="mt-2 bg-surface border border-surface-border rounded-lg p-3 animate-fade-in">
                <span className="text-text-muted text-xs">{error || 'No debug info available'}</span>
            </div>
        );
    }

    return (
        <div className="mt-2 bg-surface border border-surface-border rounded-lg p-4 space-y-3 animate-slide-up text-xs">
            {/* Intake Analysis */}
            {debug.intake_analysis.interpreted_intent && (
                <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-text-secondary font-medium">
                        <Target size={12} />
                        <span>Intake Analysis</span>
                    </div>
                    <div className="pl-5 space-y-1 text-text-muted">
                        <div><span className="text-text-secondary">Intent:</span> {debug.intake_analysis.interpreted_intent}</div>
                        <div className="flex gap-3">
                            <span><span className="text-text-secondary">Type:</span> {debug.intake_analysis.task_type}</span>
                            <span><span className="text-text-secondary">Complexity:</span> {debug.intake_analysis.complexity}/10</span>
                            <span><span className="text-text-secondary">Confidence:</span> {debug.intake_analysis.confidence_score}%</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Model */}
            {debug.model_used && (
                <div className="flex items-center gap-1.5 text-text-secondary">
                    <Brain size={12} />
                    <span className="font-medium">Model:</span>
                    <span className="text-text-muted">{debug.model_used}</span>
                </div>
            )}

            {/* Skills */}
            {debug.skills_applied.length > 0 && (
                <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-text-secondary font-medium">
                        <Zap size={12} />
                        <span>Skills Applied</span>
                    </div>
                    <div className="pl-5 flex flex-wrap gap-1">
                        {debug.skills_applied.map(skill => (
                            <span key={skill} className="px-1.5 py-0.5 bg-accent/10 text-accent rounded">
                                {skill}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* MCPs */}
            {debug.mcps_used.length > 0 && (
                <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-text-secondary font-medium">
                        <Wrench size={12} />
                        <span>Tools Used</span>
                    </div>
                    <div className="pl-5 flex flex-wrap gap-1">
                        {debug.mcps_used.map(mcp => (
                            <span key={mcp} className="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 rounded">
                                {mcp}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Optimized Prompt */}
            {debug.optimized_prompt && (
                <div className="space-y-1">
                    <div className="text-text-secondary font-medium">Optimized Prompt</div>
                    <pre className="bg-[#0d0d0f] border border-surface-border rounded-lg p-3 text-text-muted whitespace-pre-wrap font-mono text-[11px] max-h-[300px] overflow-y-auto">
                        {debug.optimized_prompt}
                    </pre>
                </div>
            )}
        </div>
    );
}

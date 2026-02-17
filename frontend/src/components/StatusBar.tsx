import { Cpu, Activity, Wrench, CheckCircle, BarChart3, Settings } from 'lucide-react';
import type { MessageMetadata } from '../types';

interface StatusBarProps {
    metadata: MessageMetadata;
}

export function StatusBar({ metadata }: StatusBarProps) {
    if (!metadata || (!metadata.model_used && !metadata.skills_applied?.length && !metadata.mcps_used?.length)) {
        return null;
    }

    return (
        <div className="flex items-center gap-4 px-4 py-2 rounded-xl bg-surface border border-border text-[10px] font-bold text-muted-foreground shadow-md animate-fade-in group/status uppercase tracking-widest backdrop-blur-sm">
            {metadata.model_used && (
                <div className="flex items-center gap-2 hover:text-foreground transition-colors cursor-help group relative">
                    <Cpu size={12} className="text-muted-foreground" />
                    <span>{metadata.model_used.split('-')[0]}</span>
                </div>
            )}

            {(metadata.skills_applied?.length ?? 0) > 0 && (
                <>
                    <div className="w-px h-3 bg-border" />
                    <div className="flex items-center gap-2 hover:text-foreground transition-colors cursor-help group relative">
                        <Settings size={12} className="text-muted-foreground" />
                        <span>{metadata.skills_applied!.length} Modules</span>

                        {/* Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] p-3 rounded-xl bg-surface border border-border shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 flex flex-wrap gap-1.5">
                            {metadata.skills_applied!.map(skill => (
                                <span key={skill} className="px-2 py-1 rounded-lg bg-surface-container border border-border text-[9px] font-bold text-muted-foreground uppercase tracking-wider">
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                </>
            )}

            {(metadata.mcps_used?.length ?? 0) > 0 && (
                <>
                    <div className="w-px h-3 bg-border" />
                    <div className="flex items-center gap-2 hover:text-foreground transition-colors cursor-help group">
                        <Wrench size={12} className="text-muted-foreground" />
                        <span>{metadata.mcps_used!.length} Capabilities</span>
                    </div>
                </>
            )}

            {metadata.confidence_score !== undefined && (
                <>
                    <div className="w-px h-3 bg-border" />
                    <div className="flex items-center gap-2">
                        <BarChart3 size={12} className="text-muted-foreground" />
                        <span>{metadata.confidence_score}% Match</span>
                    </div>
                </>
            )}
        </div>
    );
}


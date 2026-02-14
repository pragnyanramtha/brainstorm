import { Cpu, Zap, Wrench, Sparkles } from 'lucide-react';
import type { MessageMetadata } from '../types';

interface StatusBarProps {
    metadata: MessageMetadata;
}

export function StatusBar({ metadata }: StatusBarProps) {
    if (!metadata || (!metadata.model_used && !metadata.skills_applied?.length && !metadata.mcps_used?.length)) {
        return null;
    }

    return (
        <div className="flex items-center gap-3 px-3 py-1.5 rounded-full glass-card border-white/10 text-[10px] font-medium text-text-muted shadow-lg animate-fade-in backdrop-blur-md bg-surface-raised/80">
            {metadata.model_used && (
                <div className="flex items-center gap-1.5 hover:text-text-primary transition-colors cursor-help group relative">
                    <Cpu size={12} className="text-accent" />
                    <span className="opacity-80 group-hover:opacity-100">{metadata.model_used.split('-')[0]}</span>
                </div>
            )}

            {(metadata.skills_applied?.length ?? 0) > 0 && (
                <>
                    <div className="w-px h-3 bg-white/10" />
                    <div className="flex items-center gap-1.5 hover:text-text-primary transition-colors cursor-help group relative">
                        <Zap size={12} className="text-yellow-400" />
                        <span className="opacity-80 group-hover:opacity-100">{metadata.skills_applied!.length} skills</span>

                        {/* Simple Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] p-2 rounded-lg bg-surface-overlay border border-white/10 shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 flex flex-wrap gap-1">
                            {metadata.skills_applied!.map(skill => (
                                <span key={skill} className="px-1.5 py-0.5 rounded bg-white/5 border border-white/5 text-[10px] text-text-secondary">
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                </>
            )}

            {(metadata.mcps_used?.length ?? 0) > 0 && (
                <>
                    <div className="w-px h-3 bg-white/10" />
                    <div className="flex items-center gap-1.5 hover:text-text-primary transition-colors cursor-help group">
                        <Wrench size={12} className="text-purple-400" />
                        <span className="opacity-80 group-hover:opacity-100">{metadata.mcps_used!.length} tools</span>
                    </div>
                </>
            )}

            {metadata.confidence_score && (
                <>
                    <div className="w-px h-3 bg-white/10" />
                    <div className="flex items-center gap-1">
                        <Sparkles size={10} className={metadata.confidence_score > 80 ? "text-emerald-400" : "text-amber-400"} />
                        <span>{metadata.confidence_score}%</span>
                    </div>
                </>
            )}
        </div>
    );
}

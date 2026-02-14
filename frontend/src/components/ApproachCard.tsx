import { useState } from 'react';
import { ChevronRight, Star, Zap, Clock, TrendingUp, AlertTriangle } from 'lucide-react';
import type { ApproachProposal } from '../types';

interface ApproachCardProps {
    approaches: ApproachProposal[];
    contextSummary?: string | null;
    onSelect: (approach: ApproachProposal) => void;
}

const EFFORT_CONFIG = {
    low: { label: 'Quick', icon: Zap, color: 'text-green-400', bg: 'bg-green-400/10 border-green-400/20' },
    medium: { label: 'Moderate', icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/20' },
    high: { label: 'Involved', icon: TrendingUp, color: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/20' },
};

export function ApproachCard({ approaches, contextSummary, onSelect }: ApproachCardProps) {
    const [selected, setSelected] = useState<string | null>(
        approaches.find(a => a.recommended)?.id || null
    );

    const handleConfirm = () => {
        const approach = approaches.find(a => a.id === selected);
        if (approach) onSelect(approach);
    };

    return (
        <div className="w-full max-w-3xl mx-auto space-y-6 animate-fade-in mb-8">
            {/* Thinking / Agent State */}
            <div className="flex items-start gap-4 text-sm">
                <div className="relative mt-1">
                    <div className="w-2.5 h-2.5 rounded-full bg-purple-400 animate-pulse shadow-[0_0_8px_rgba(168,85,247,0.5)]" />
                    <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-purple-400 animate-ping opacity-20" />
                </div>
                <div className="space-y-1">
                    <div className="flex items-center gap-2">
                        <span className="text-text-primary font-medium">Brainstorming</span>
                    </div>
                    {contextSummary && (
                        <p className="text-text-secondary leading-relaxed max-w-2xl italic">
                            {contextSummary}
                        </p>
                    )}
                </div>
            </div>

            {/* Approaches Container */}
            <div className="bg-surface-container/30 border border-white/5 rounded-3xl overflow-hidden backdrop-blur-xl shadow-2xl">
                <div className="px-8 py-5 border-b border-white/5 bg-white/[0.02]">
                    <h3 className="text-[11px] font-bold text-text-muted uppercase tracking-[0.1em] flex items-center gap-2.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-purple-400/60" />
                        Choose your approach
                    </h3>
                </div>

                <div className="px-8 py-8 space-y-4">
                    {approaches.map((approach) => {
                        const isSelected = selected === approach.id;
                        const effort = EFFORT_CONFIG[approach.effort_level] || EFFORT_CONFIG.medium;
                        const EffortIcon = effort.icon;

                        return (
                            <button
                                key={approach.id}
                                onClick={() => setSelected(approach.id)}
                                className={`w-full text-left rounded-2xl border p-6 transition-all duration-300 relative group ${
                                    isSelected
                                        ? 'bg-accent/[0.08] border-accent/30 shadow-[0_0_30px_-10px_rgba(37,99,235,0.15)]'
                                        : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.05] hover:border-white/[0.12]'
                                }`}
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between gap-4 mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                                            isSelected ? 'border-accent bg-accent' : 'border-text-muted/30 group-hover:border-text-muted/50'
                                        }`}>
                                            {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                                        </div>
                                        <h4 className={`text-base font-semibold transition-colors ${
                                            isSelected ? 'text-text-primary' : 'text-text-secondary group-hover:text-text-primary'
                                        }`}>
                                            {approach.title}
                                        </h4>
                                        {approach.recommended && (
                                            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent/15 border border-accent/20 text-[10px] font-bold text-accent uppercase tracking-wider">
                                                <Star size={10} className="fill-accent" />
                                                Recommended
                                            </span>
                                        )}
                                    </div>
                                    <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-medium ${effort.bg} ${effort.color}`}>
                                        <EffortIcon size={12} />
                                        {effort.label}
                                    </span>
                                </div>

                                {/* Description */}
                                <p className={`text-sm leading-relaxed mb-4 pl-8 ${
                                    isSelected ? 'text-text-secondary' : 'text-text-muted'
                                }`}>
                                    {approach.description}
                                </p>

                                {/* Pros & Cons */}
                                <div className={`grid grid-cols-2 gap-4 pl-8 transition-all duration-300 ${
                                    isSelected ? 'opacity-100 max-h-96' : 'opacity-0 max-h-0 overflow-hidden'
                                }`}>
                                    {approach.pros.length > 0 && (
                                        <div className="space-y-1.5">
                                            {approach.pros.map((pro, i) => (
                                                <div key={i} className="flex items-start gap-2 text-xs text-green-400/80">
                                                    <TrendingUp size={12} className="mt-0.5 flex-shrink-0" />
                                                    <span>{pro}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {approach.cons.length > 0 && (
                                        <div className="space-y-1.5">
                                            {approach.cons.map((con, i) => (
                                                <div key={i} className="flex items-start gap-2 text-xs text-yellow-400/70">
                                                    <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
                                                    <span>{con}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Footer */}
                <div className="px-8 py-6 bg-white/[0.02] border-t border-white/5 flex justify-end">
                    <button
                        onClick={handleConfirm}
                        disabled={!selected}
                        className={`group flex items-center gap-2.5 px-7 py-3 rounded-2xl text-sm font-bold transition-all ${
                            selected
                                ? 'bg-white text-surface hover:bg-white/90 shadow-xl shadow-black/20 active:scale-[0.98]'
                                : 'bg-white/5 text-text-muted border border-white/5 cursor-not-allowed'
                        }`}
                    >
                        <span>Build it</span>
                        <ChevronRight size={18} className={`transition-transform duration-300 group-hover:translate-x-0.5 ${!selected ? 'opacity-20' : ''}`} />
                    </button>
                </div>
            </div>
        </div>
    );
}

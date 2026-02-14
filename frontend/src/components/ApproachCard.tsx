import { useState } from 'react';
import { ChevronRight, Star, Clock, TrendingUp, AlertTriangle, GitBranch, Shield, Zap } from 'lucide-react';
import type { ApproachProposal } from '../types';

interface ApproachCardProps {
    approaches: ApproachProposal[];
    contextSummary?: string | null;
    onSelect: (approach: ApproachProposal) => void;
}

const EFFORT_CONFIG = {
    low: { label: 'Quick Implementation', icon: Zap, color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
    medium: { label: 'Moderate Effort', icon: Clock, color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
    high: { label: 'Complex Architecture', icon: TrendingUp, color: 'text-slate-700', bg: 'bg-slate-100 border-slate-200' },
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
            {/* Context/Analysis */}
            {contextSummary && (
                <div className="flex items-start gap-4 text-xs">
                    <div className="mt-0.5 p-1 rounded bg-slate-100 text-slate-500">
                        <GitBranch size={14} />
                    </div>
                    <div className="space-y-1">
                        <span className="font-bold text-slate-400 uppercase tracking-widest text-[10px]">Strategic Analysis</span>
                        <p className="text-slate-600 leading-relaxed font-medium max-w-2xl">
                            {contextSummary}
                        </p>
                    </div>
                </div>
            )}

            {/* Approaches Container */}
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-lg">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em] flex items-center gap-2">
                        <Shield size={14} className="text-slate-400" />
                        Implementation Proposals
                    </h3>
                </div>

                <div className="p-4 space-y-3">
                    {approaches.map((approach) => {
                        const isSelected = selected === approach.id;
                        const effort = EFFORT_CONFIG[approach.effort_level] || EFFORT_CONFIG.medium;
                        const EffortIcon = effort.icon;

                        return (
                            <button
                                key={approach.id}
                                onClick={() => setSelected(approach.id)}
                                className={`w-full text-left rounded-lg border p-5 transition-all duration-200 relative group ${isSelected
                                    ? 'bg-slate-50 border-slate-300 shadow-sm ring-1 ring-slate-200'
                                    : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                                    }`}
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between gap-4 mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-4 h-4 rounded-full border flex items-center justify-center transition-colors ${isSelected ? 'border-slate-900 bg-slate-900' : 'border-slate-300'
                                            }`}>
                                            {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                                        </div>
                                        <h4 className={`text-sm font-bold transition-colors ${isSelected ? 'text-slate-900' : 'text-slate-700'
                                            }`}>
                                            {approach.title}
                                        </h4>
                                        {approach.recommended && (
                                            <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-100 uppercase tracking-wider">
                                                <Star size={10} className="fill-blue-700" />
                                                Recommended
                                            </span>
                                        )}
                                    </div>
                                    <span className={`flex items-center gap-1.5 px-2 py-1 rounded border text-[10px] font-bold uppercase tracking-wider ${effort.bg} ${effort.color}`}>
                                        <EffortIcon size={12} />
                                        {effort.label}
                                    </span>
                                </div>

                                {/* Description */}
                                <p className="text-xs text-slate-500 leading-relaxed mb-4 pl-7 max-w-2xl">
                                    {approach.description}
                                </p>

                                {/* Pros & Cons - Only show when selected or hovered for cleaner look, or always show if space permits. Let's toggle. */}
                                <div className={`grid grid-cols-2 gap-6 pl-7 transition-all duration-300 ${isSelected ? 'opacity-100 max-h-96 mt-4 pt-4 border-t border-slate-200' : 'opacity-0 max-h-0 overflow-hidden'
                                    }`}>
                                    {approach.pros.length > 0 && (
                                        <div className="space-y-2">
                                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Benefits</span>
                                            {approach.pros.map((pro, i) => (
                                                <div key={i} className="flex items-start gap-2 text-xs text-slate-600">
                                                    <TrendingUp size={12} className="mt-0.5 flex-shrink-0 text-emerald-600" />
                                                    <span>{pro}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {approach.cons.length > 0 && (
                                        <div className="space-y-2">
                                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Trade-offs</span>
                                            {approach.cons.map((con, i) => (
                                                <div key={i} className="flex items-start gap-2 text-xs text-slate-600">
                                                    <AlertTriangle size={12} className="mt-0.5 flex-shrink-0 text-amber-600" />
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
                <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end">
                    <button
                        onClick={handleConfirm}
                        disabled={!selected}
                        className={`group flex items-center gap-2 px-6 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${selected
                            ? 'bg-slate-900 text-white hover:bg-slate-800 shadow-md active:scale-[0.98]'
                            : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                            }`}
                    >
                        <span>Initialize Strategy</span>
                        <ChevronRight size={14} className={`transition-transform duration-300 group-hover:translate-x-0.5 ${!selected ? 'opacity-20' : ''}`} />
                    </button>
                </div>
            </div>
        </div>
    );
}


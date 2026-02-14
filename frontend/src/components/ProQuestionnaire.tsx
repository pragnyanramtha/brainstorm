import { useState } from 'react';
import { ChevronRight, Zap } from 'lucide-react';
import type { ClarificationQuestion } from '../types';

interface ProQuestionnaireProps {
    questions: ClarificationQuestion[];
    lastIntent?: string;
    onSubmit: (answers: Record<string, string>) => void;
}

export function ProQuestionnaire({ questions, lastIntent, onSubmit }: ProQuestionnaireProps) {
    const [answers, setAnswers] = useState<Record<string, string>>(() => {
        const defaults: Record<string, string> = {};
        questions.forEach(q => {
            if (q.default) defaults[q.question] = q.default;
        });
        return defaults;
    });

    const [focusedField, setFocusedField] = useState<string | null>(null);

    const handleChipClick = (question: string, value: string) => {
        setAnswers((prev: Record<string, string>) => ({ ...prev, [question]: value }));
    };

    const handleInputChange = (question: string, value: string) => {
        setAnswers((prev: Record<string, string>) => ({ ...prev, [question]: value }));
    };

    const handleSubmit = () => {
        onSubmit(answers);
    };

    const allAnswered = questions.every(q => (answers[q.question] || '').trim());
    const remainingCount = questions.length - Object.values(answers).filter(v => (v || '').trim()).length;

    return (
        <div className="w-full max-w-3xl mx-auto space-y-6 animate-fade-in mb-8">
            {/* Thinking / Agent State */}
            <div className="flex items-start gap-4 text-sm">
                <div className="relative mt-1">
                    <div className="w-2.5 h-2.5 rounded-full bg-accent animate-pulse shadow-[0_0_8px_rgba(11,87,208,0.5)]" />
                    <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-accent animate-ping opacity-20" />
                </div>
                <div className="space-y-1">
                    <div className="flex items-center gap-2">
                        <span className="text-text-primary font-medium">Thinking</span>
                    </div>
                    {lastIntent && (
                        <p className="text-text-secondary leading-relaxed max-w-2xl italic">
                            {lastIntent}
                        </p>
                    )}
                </div>
            </div>

            {/* Questions Container */}
            <div className="bg-surface-container/30 border border-white/5 rounded-3xl overflow-hidden backdrop-blur-xl shadow-2xl">
                <div className="px-8 py-5 border-b border-white/5 bg-white/[0.02]">
                    <h3 className="text-[11px] font-bold text-text-muted uppercase tracking-[0.1em] flex items-center gap-2.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-accent/60" />
                        Quick questions so the research is actually useful for you
                    </h3>
                </div>

                <div className="px-8 py-8 space-y-12">
                    {questions.map((q, idx) => (
                        <div key={idx} className="space-y-5">
                            <label className="block text-[17px] font-semibold text-text-primary tracking-tight">
                                {q.question}
                            </label>

                            <div className="relative space-y-4">
                                <input
                                    type="text"
                                    value={answers[q.question] || ''}
                                    onChange={(e) => handleInputChange(q.question, e.target.value)}
                                    onFocus={() => setFocusedField(q.question)}
                                    onBlur={() => setTimeout(() => setFocusedField(null), 200)}
                                    placeholder={q.default || "Type your answer..."}
                                    className="w-full bg-white/[0.03] border border-white/[0.08] rounded-2xl px-5 py-4 text-text-primary placeholder-text-muted/30 outline-none transition-all focus:border-accent/40 focus:bg-white/[0.05] focus:shadow-[0_0_20px_-10px_rgba(11,87,208,0.2)] text-base"
                                />

                                {q.options && q.options.length > 0 && (
                                    <div className="flex flex-wrap gap-2.5">
                                        {q.options.map((opt) => (
                                            <button
                                                key={opt}
                                                onClick={() => handleChipClick(q.question, opt)}
                                                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${answers[q.question] === opt
                                                    ? 'bg-accent/20 border-accent/40 text-primary shadow-[0_0_15px_-5px_rgba(11,87,208,0.2)]'
                                                    : 'bg-white/[0.03] border-white/[0.08] text-text-secondary hover:bg-white/[0.08] hover:border-white/[0.15] hover:text-text-primary'
                                                    }`}
                                            >
                                                {opt}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Footer */}
                <div className="px-8 py-6 bg-white/[0.02] border-t border-white/5 flex justify-end">
                    <button
                        onClick={handleSubmit}
                        disabled={!allAnswered && remainingCount > 0}
                        className={`group flex items-center gap-2.5 px-7 py-3 rounded-2xl text-sm font-bold transition-all ${allAnswered
                            ? 'bg-white text-surface hover:bg-white/90 shadow-xl shadow-black/20 active:scale-[0.98]'
                            : 'bg-white/5 text-text-muted border border-white/5 cursor-not-allowed'
                            }`}
                    >
                        <span>Continue</span>
                        {remainingCount > 0 && (
                            <span className="opacity-40 font-medium font-mono text-xs">({remainingCount})</span>
                        )}
                        <ChevronRight size={18} className={`transition-transform duration-300 group-hover:translate-x-0.5 ${!allAnswered ? 'opacity-20' : ''}`} />
                    </button>
                </div>
            </div>
        </div>
    );
}

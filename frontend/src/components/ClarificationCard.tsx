import { useState, useEffect } from 'react';
import { HelpCircle, ChevronRight, Check } from 'lucide-react';
import type { ClarificationQuestion } from '../types';

interface ClarificationCardProps {
    questions: ClarificationQuestion[];
    onSubmit: (answers: Record<string, string>) => void;
}

export function ClarificationCard({ questions, onSubmit }: ClarificationCardProps) {
    const [answers, setAnswers] = useState<Record<string, string>>(() => {
        const defaults: Record<string, string> = {};
        questions.forEach(q => {
            if (q.default) defaults[q.question] = q.default;
        });
        return defaults;
    });

    const [mounted, setMounted] = useState(false);
    useEffect(() => setMounted(true), []);

    const handleSubmit = () => {
        onSubmit(answers);
    };

    const setAnswer = (question: string, value: string) => {
        setAnswers(prev => ({ ...prev, [question]: value }));
    };

    return (
        <div className={`glass-card rounded-2xl p-6 max-w-2xl w-full mx-auto transition-all duration-500 ease-out ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            {/* Header */}
            <div className="flex items-start gap-4 mb-8">
                <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0 border border-accent/20 text-accent shadow-glow">
                    <HelpCircle size={20} />
                </div>
                <div>
                    <h3 className="text-base font-semibold text-text-primary mb-1">
                        I need a few details to get this right
                    </h3>
                    <p className="text-sm text-text-secondary leading-relaxed">
                        Your answers help me tailor the solution exactly to your needs.
                    </p>
                </div>
            </div>

            {/* Questions */}
            <div className="space-y-8">
                {questions.map((q, idx) => (
                    <div
                        key={idx}
                        className="animate-slide-up"
                        style={{ animationDelay: `${idx * 100}ms`, animationFillMode: 'both' }}
                    >
                        <div className="flex items-baseline gap-2 mb-3">
                            <span className="text-xs font-mono text-accent/80 bg-accent/10 px-1.5 py-0.5 rounded">
                                {idx + 1}/{questions.length}
                            </span>
                            <label className="text-sm font-medium text-text-primary">
                                {q.question}
                            </label>
                        </div>

                        {q.why_it_matters && (
                            <p className="text-xs text-text-muted mb-3 pl-1">
                                {q.why_it_matters}
                            </p>
                        )}

                        <div className="pl-1">
                            {/* Multiple Choice */}
                            {q.question_type === 'multiple_choice' && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {q.options.map(option => {
                                        const isSelected = answers[q.question] === option;
                                        return (
                                            <button
                                                key={option}
                                                onClick={() => setAnswer(q.question, option)}
                                                className={`group relative flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition-all duration-200 ${isSelected
                                                        ? 'bg-accent/10 border-accent text-text-primary shadow-[0_0_15px_-3px_rgba(37,99,235,0.2)]'
                                                        : 'bg-surface-overlay/30 border-white/5 text-text-secondary hover:bg-surface-overlay/50 hover:border-white/10'
                                                    }`}
                                            >
                                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center transition-colors ${isSelected ? 'border-accent bg-accent' : 'border-text-muted/40 group-hover:border-text-muted'
                                                    }`}>
                                                    {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                                                </div>
                                                <span className="text-sm">{option}</span>
                                            </button>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Yes/No */}
                            {q.question_type === 'yes_no' && (
                                <div className="flex gap-3">
                                    {['Yes', 'No'].map(opt => {
                                        const isSelected = answers[q.question] === opt;
                                        return (
                                            <button
                                                key={opt}
                                                onClick={() => setAnswer(q.question, opt)}
                                                className={`flex-1 px-4 py-3 rounded-xl border text-sm font-medium transition-all duration-200 ${isSelected
                                                        ? 'bg-accent/10 border-accent text-accent shadow-[0_0_15px_-3px_rgba(37,99,235,0.2)]'
                                                        : 'bg-surface-overlay/30 border-white/5 text-text-secondary hover:bg-surface-overlay/50 hover:border-white/10'
                                                    }`}
                                            >
                                                {opt}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Free Text */}
                            {q.question_type === 'free_text' && (
                                <div className="relative group">
                                    <input
                                        type="text"
                                        value={answers[q.question] || ''}
                                        onChange={e => setAnswer(q.question, e.target.value)}
                                        placeholder={q.default || 'Type your answer...'}
                                        className="w-full bg-surface-overlay/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-text-primary placeholder-text-muted/60 outline-none focus:border-accent/50 focus:bg-surface-overlay/50 focus:shadow-[0_0_15px_-3px_rgba(37,99,235,0.1)] transition-all"
                                    />
                                </div>
                            )}

                            {/* Skip Link */}
                            {q.default && answers[q.question] !== q.default && (
                                <div className="mt-2 text-right">
                                    <button
                                        onClick={() => setAnswer(q.question, q.default!)}
                                        className="text-[10px] uppercase tracking-wider font-medium text-text-muted hover:text-accent transition-colors"
                                    >
                                        Use default: {q.default}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-white/5 flex justify-end">
                <button
                    onClick={handleSubmit}
                    className="group flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-all hover:shadow-lg hover:shadow-accent/25 active:scale-95"
                >
                    Continue Journey
                    <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                </button>
            </div>
        </div>
    );
}

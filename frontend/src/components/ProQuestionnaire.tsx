import { useState } from 'react';
import { ChevronRight, ClipboardList, Target } from 'lucide-react';
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
        <div className="w-full max-w-2xl mx-auto space-y-6 animate-fade-in mb-10">
            {/* Context/Intent */}
            {lastIntent && (
                <div className="flex items-start gap-3 text-xs">
                    <div className="mt-0.5 p-1 rounded bg-surface-raised text-muted-foreground">
                        <Target size={12} />
                    </div>
                    <div className="space-y-1">
                        <span className="font-bold text-muted-foreground uppercase tracking-widest text-[10px]">Interpreted Requirements</span>
                        <p className="text-foreground leading-relaxed font-medium">
                            {lastIntent}
                        </p>
                    </div>
                </div>
            )}

            {/* Questions Container */}
            <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-xl shadow-primary/5">
                <div className="px-6 py-4 border-b border-border bg-surface-container">
                    <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.15em] flex items-center gap-2">
                        <ClipboardList size={14} className="text-muted-foreground/70" />
                        Configuration Parameters Required
                    </h3>
                </div>

                <div className="px-6 py-8 space-y-10">
                    {questions.map((q, idx) => (
                        <div key={idx} className="space-y-4">
                            <label className="block text-sm font-semibold text-foreground tracking-tight">
                                {q.question}
                            </label>

                            <div className="relative space-y-3">
                                <input
                                    type="text"
                                    value={answers[q.question] || ''}
                                    onChange={(e) => handleInputChange(q.question, e.target.value)}
                                    placeholder={q.default || "Specify requirements..."}
                                    className="w-full bg-surface-container border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground outline-none transition-all focus:border-accent focus:bg-surface text-sm font-medium"
                                />

                                {q.options && q.options.length > 0 && (
                                    <div className="flex flex-wrap gap-2">
                                        {q.options.map((opt) => (
                                            <button
                                                key={opt}
                                                onClick={() => handleChipClick(q.question, opt)}
                                                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-all border uppercase tracking-wider ${answers[q.question] === opt
                                                    ? 'bg-primary border-primary text-primary-foreground shadow-sm'
                                                    : 'bg-surface border-border text-muted-foreground hover:border-foreground/20 hover:text-foreground'
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
                <div className="px-6 py-4 bg-surface-container border-t border-border flex items-center justify-between">
                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        {remainingCount > 0 ? `${remainingCount} parameters remaining` : 'System configuration complete'}
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={!allAnswered && remainingCount > 0}
                        className={`group flex items-center gap-2 px-6 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${allAnswered
                            ? 'bg-primary text-primary-foreground hover:bg-primary-hover shadow-md active:scale-[0.98]'
                            : 'bg-surface-raised text-muted-foreground border border-border cursor-not-allowed'
                            }`}
                    >
                        <span>Apply Parameters</span>
                        <ChevronRight size={14} className={`transition-transform duration-300 group-hover:translate-x-0.5 ${!allAnswered ? 'opacity-20' : ''}`} />
                    </button>
                </div>
            </div>
        </div>
    );
}

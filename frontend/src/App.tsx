import { useState, useEffect } from 'react';
import { getOnboardingStatus } from './api';
import { useProjects } from './hooks/useProjects';
import { useChat } from './hooks/useChat';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';

import { WelcomeScreen } from './components/WelcomeScreen';
import { SettingsModal } from './components/SettingsModal';

import type { OnboardingStatus } from './types';
import { AlertCircle, Loader2 } from 'lucide-react';

export default function App() {
    const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
    const [showSettings, setShowSettings] = useState(false);

    const [isLoading, setIsLoading] = useState(true);

    const {
        projects, activeProject, loading: projectsLoading,
        createNewProject, selectProject, archiveProject, renameProject
    } = useProjects();

    const {
        messages, setMessages, sendMessage, sendClarificationResponse,
        sendApproachSelection, status, statusDetail, isConnected, clarificationQuestions,
        approachProposals, approachContextSummary, error
    } = useChat(activeProject?.id || null);

    // Check onboarding status
    useEffect(() => {
        (async () => {
            try {
                const data = await getOnboardingStatus();
                setOnboarding(data);
            } catch {
                // Backend not ready yet
            } finally {
                setIsLoading(false);
            }
        })();
    }, []);

    // Load messages when project changes
    useEffect(() => {
        if (activeProject?.messages) {
            setMessages(activeProject.messages);
        } else {
            setMessages([]);
        }
    }, [activeProject?.id]);

    const handleOnboardingComplete = () => {
        setOnboarding({ has_api_keys: true, has_profile: true, onboarding_complete: true });
    };

    const handleNewChat = async () => {
        await createNewProject();
    };

    if (isLoading) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-slate-50">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 size={24} className="text-slate-400 animate-spin" />
                    <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Loading System</span>
                </div>
            </div>
        );
    }

    // Show welcome screen if onboarding not complete
    if (onboarding && !onboarding.has_api_keys) {
        return <WelcomeScreen onComplete={handleOnboardingComplete} />;
    }

    return (
        <div className="h-screen w-full flex bg-background overflow-hidden text-foreground selection:bg-accent/30 selection:text-foreground font-sans">
            {/* Sidebar with Settings trigger */}
            <Sidebar
                projects={projects}
                activeProjectId={activeProject?.id || null}
                onSelectProject={selectProject}
                onNewChat={handleNewChat}
                onArchiveProject={archiveProject}
                onRenameProject={renameProject}
                onOpenSettings={() => setShowSettings(true)}
            />

            {/* Main Content Area */}
            <main className="flex-1 flex min-w-0 relative z-0 bg-surface">
                <ChatArea
                    messages={messages}
                    onSendMessage={sendMessage}
                    status={status}
                    statusDetail={statusDetail}
                    clarificationQuestions={clarificationQuestions}
                    onClarificationResponse={sendClarificationResponse}
                    approachProposals={approachProposals}
                    approachContextSummary={approachContextSummary}
                    onApproachSelection={sendApproachSelection}
                    error={error}
                    hasProject={!!activeProject}
                    onNewChat={handleNewChat}
                />
            </main>

            {/* Settings Modal */}
            {showSettings && (
                <SettingsModal onClose={() => setShowSettings(false)} />
            )}

            {/* Connection Status Indicator (Subtle overlay) */}
            {!isConnected && !isLoading && activeProject && (
                <div className="fixed top-4 right-4 z-50 bg-red-50 border border-red-200 text-red-600 px-3 py-1.5 rounded-md text-xs font-bold shadow-sm flex items-center gap-2">
                    <Loader2 size={12} className="animate-spin" />
                    <span>Reconnecting...</span>
                </div>
            )}
        </div>
    );
}


import { useState, useEffect } from 'react';
import { getOnboardingStatus } from './api';
import { useProjects } from './hooks/useProjects';
import { useChat } from './hooks/useChat';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { FileExplorer } from './components/FileExplorer';
import { WelcomeScreen } from './components/WelcomeScreen';
import { SettingsModal } from './components/SettingsModal';
import type { OnboardingStatus } from './types';

export default function App() {
    const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
    const [showSettings, setShowSettings] = useState(false);
    const [showFiles, setShowFiles] = useState(true);
    const [isLoading, setIsLoading] = useState(true);

    const {
        projects, activeProject, loading: projectsLoading,
        createNewProject, selectProject, archiveProject, renameProject
    } = useProjects();

    const {
        messages, setMessages, sendMessage, sendClarificationResponse,
        status, isConnected, clarificationQuestions, error
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
            <div className="h-screen flex items-center justify-center bg-surface w-full overflow-hidden">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin shadow-glow" />
                    <span className="text-text-secondary text-sm font-medium animate-pulse">Middle Manager AI</span>
                </div>
            </div>
        );
    }

    // Show welcome screen if onboarding not complete
    if (onboarding && !onboarding.has_api_keys) {
        return <WelcomeScreen onComplete={handleOnboardingComplete} />;
    }

    return (
        <div className="h-screen w-full flex bg-surface overflow-hidden text-text-primary selection:bg-accent/30 selection:text-white">
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
            <main className="flex-1 flex min-w-0 relative z-0">
                <ChatArea
                    messages={messages}
                    onSendMessage={sendMessage}
                    status={status}
                    clarificationQuestions={clarificationQuestions}
                    onClarificationResponse={sendClarificationResponse}
                    error={error}
                    hasProject={!!activeProject}
                    onNewChat={handleNewChat}
                />

                {/* File Explorer (Overlay or persistent based on width - sticking to persistent for now as per minimal requirment) */}
                {activeProject && showFiles && (
                    <FileExplorer
                        projectPath={activeProject.folder_path}
                        onClose={() => setShowFiles(false)}
                    />
                )}
            </main>

            {/* Settings Modal */}
            {showSettings && (
                <SettingsModal onClose={() => setShowSettings(false)} />
            )}

            {/* Connection Status Indicator (Subtle overlay) */}
            {!isConnected && !isLoading && (
                <div className="fixed top-4 right-4 z-50 bg-red-500/10 border border-red-500/20 text-red-400 px-3 py-1.5 rounded-full text-xs font-medium animate-pulse backdrop-blur-sm">
                    Reconnecting...
                </div>
            )}
        </div>
    );
}

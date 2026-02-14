import { useState, useEffect, useRef, useCallback } from 'react';
import { createWebSocket } from '../api';
import type { Message, WSMessageIncoming, ClarificationQuestion, ApproachProposal } from '../types';

interface UseChatReturn {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    sendMessage: (content: string) => void;
    sendClarificationResponse: (answers: Record<string, string>) => void;
    sendApproachSelection: (approach: ApproachProposal) => void;
    status: string | null;
    isConnected: boolean;
    clarificationQuestions: ClarificationQuestion[] | null;
    approachProposals: ApproachProposal[] | null;
    approachContextSummary: string | null;
    error: string | null;
}

export function useChat(projectId: string | null): UseChatReturn {
    const [messages, setMessages] = useState<Message[]>([]);
    const [status, setStatus] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [clarificationQuestions, setClarificationQuestions] = useState<ClarificationQuestion[] | null>(null);
    const [approachProposals, setApproachProposals] = useState<ApproachProposal[] | null>(null);
    const [approachContextSummary, setApproachContextSummary] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<number | null>(null);
    const lastClarificationAnswersRef = useRef<Record<string, string> | null>(null);

    const connect = useCallback(() => {
        if (!projectId) return;

        // Close existing connection
        if (wsRef.current) {
            wsRef.current.close();
        }

        const ws = createWebSocket(projectId);

        ws.onopen = () => {
            setIsConnected(true);
            setError(null);
        };

        ws.onmessage = (event) => {
            try {
                const data: WSMessageIncoming = JSON.parse(event.data);

                switch (data.type) {
                    case 'message':
                        setMessages(prev => [...prev, {
                            id: crypto.randomUUID(),
                            project_id: projectId,
                            role: data.role || 'assistant',
                            content: data.content || '',
                            message_type: 'chat',
                            metadata: data.metadata || {},
                            created_at: new Date().toISOString(),
                        }]);
                        setStatus(null);
                        setClarificationQuestions(null);
                        break;

                    case 'clarification':
                        setClarificationQuestions(data.questions || null);
                        setApproachProposals(null);
                        setStatus(null);
                        break;

                    case 'approach_proposal':
                        setApproachProposals(data.approaches || null);
                        setApproachContextSummary(data.context_summary || null);
                        setClarificationQuestions(null);
                        setStatus(null);
                        break;

                    case 'status':
                        setStatus(data.state || null);
                        break;

                    case 'error':
                        setError(data.message || 'Unknown error');
                        setStatus(null);
                        break;

                    case 'file_update':
                        // Trigger file explorer refresh
                        break;
                }
            } catch (e) {
                console.error('Failed to parse WS message:', e);
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            // Auto-reconnect after 3 seconds
            reconnectTimeoutRef.current = window.setTimeout(() => {
                if (projectId) connect();
            }, 3000);
        };

        ws.onerror = () => {
            setError('Connection error');
        };

        wsRef.current = ws;
    }, [projectId]);

    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) wsRef.current.close();
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        };
    }, [connect]);

    const sendMessage = useCallback((content: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            setError('Not connected');
            return;
        }

        // Add user message immediately
        setMessages(prev => [...prev, {
            id: crypto.randomUUID(),
            project_id: projectId || '',
            role: 'user',
            content,
            message_type: 'chat',
            metadata: {},
            created_at: new Date().toISOString(),
        }]);

        wsRef.current.send(JSON.stringify({ type: 'message', content }));
    }, [projectId]);

    const sendClarificationResponse = useCallback((answers: Record<string, string>) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        // Save answers so we can send them back with approach selection
        lastClarificationAnswersRef.current = answers;

        wsRef.current.send(JSON.stringify({ type: 'clarification_response', answers }));
        setClarificationQuestions(null);
        setStatus('brainstorming');
    }, []);

    const sendApproachSelection = useCallback((approach: ApproachProposal) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        wsRef.current.send(JSON.stringify({
            type: 'approach_selection',
            approach,
            clarification_answers: lastClarificationAnswersRef.current || {},
        }));
        setApproachProposals(null);
        setApproachContextSummary(null);
        lastClarificationAnswersRef.current = null;
        setStatus('optimizing');
    }, []);

    return {
        messages,
        setMessages,
        sendMessage,
        sendClarificationResponse,
        sendApproachSelection,
        status,
        isConnected,
        clarificationQuestions,
        approachProposals,
        approachContextSummary,
        error,
    };
}

/** TypeScript interfaces matching backend schemas */

export interface UserProfile {
    id: number;
    technical_level: 'non_technical' | 'semi_technical' | 'technical' | 'expert';
    domain: string;
    role: string;
    stack: string[];
    communication_preferences: {
        detail_level: string;
        tone: string;
        format: string;
    };
    pet_peeves: string[];
    positive_patterns: string[];
    interaction_count: number;
    created_at: string;
    updated_at: string;
}

export interface CoreMemory {
    id: number;
    category: 'identity' | 'preference' | 'project_context' | 'technical' | 'relationship';
    content: string;
    source_session_id: string | null;
    importance: number;
    created_at: string;
    last_accessed: string;
    access_count: number;
    active: boolean;
}

export interface Project {
    id: string;
    name: string;
    folder_path: string;
    summary: string | null;
    task_types_used: string[];
    models_used: string[];
    message_count: number;
    created_at: string;
    updated_at: string;
    archived: boolean;
    messages?: Message[];
}

export interface MessageMetadata {
    model_used?: string;
    skills_applied?: string[];
    mcps_used?: string[];
    confidence_score?: number;
    optimized_prompt?: string;
    task_type?: string;
    complexity?: number;
    interpreted_intent?: string;
}

export interface Message {
    id: string;
    project_id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    message_type: 'chat' | 'clarification_question' | 'clarification_answer' | 'status';
    metadata: MessageMetadata;
    created_at: string;
}

export interface ClarificationQuestion {
    question: string;
    question_type: 'multiple_choice' | 'yes_no' | 'free_text';
    options: string[];
    default: string;
    why_it_matters: string;
}

export interface Skill {
    id: number;
    name: string;
    category: string;
    description: string;
    best_for_task_types: string[];
    effectiveness_score: number;
    usage_count: number;
    active: boolean;
}

export interface MCPServer {
    id: number;
    name: string;
    description: string;
    category: string;
    capabilities: string[];
    requires_user_config: boolean;
    enabled: boolean;
    health_status: string;
    priority: number;
}

export interface Settings {
    api_keys: {
        gemini: { configured: boolean; masked: string | null };
        anthropic: { configured: boolean; masked: string | null };
    };
    user_profile: UserProfile | null;
}

export interface OnboardingStatus {
    has_api_keys: boolean;
    has_profile: boolean;
    onboarding_complete: boolean;
}

// WebSocket message types
export interface WSMessageOutgoing {
    type: 'message' | 'clarification_response';
    content?: string;
    answers?: Record<string, string>;
}

export interface WSMessageIncoming {
    type: 'message' | 'clarification' | 'status' | 'error' | 'file_update';
    role?: 'assistant' | 'system';
    content?: string;
    metadata?: MessageMetadata;
    questions?: ClarificationQuestion[];
    state?: string;
    message?: string;
}

export interface DebugInfo {
    message_id: string;
    optimized_prompt: string | null;
    intake_analysis: {
        interpreted_intent: string | null;
        task_type: string | null;
        complexity: number | null;
        confidence_score: number | null;
    };
    skills_applied: string[];
    mcps_used: string[];
    model_used: string | null;
}

import { useState, useEffect, useCallback } from 'react';
import { getProjects, createProject, deleteProject, updateProject, getProject } from '../api';
import type { Project } from '../types';

interface UseProjectsReturn {
    projects: Project[];
    activeProject: Project | null;
    loading: boolean;
    error: string | null;
    createNewProject: (name?: string) => Promise<Project>;
    selectProject: (id: string) => Promise<void>;
    archiveProject: (id: string) => Promise<void>;
    renameProject: (id: string, name: string) => Promise<void>;
    refreshProjects: () => Promise<void>;
}

export function useProjects(): UseProjectsReturn {
    const [projects, setProjects] = useState<Project[]>([]);
    const [activeProject, setActiveProject] = useState<Project | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refreshProjects = useCallback(async () => {
        try {
            const data = await getProjects();
            setProjects(data);
        } catch (e: any) {
            setError(e.message);
        }
    }, []);

    useEffect(() => {
        (async () => {
            await refreshProjects();
            setLoading(false);
        })();
    }, [refreshProjects]);

    const createNewProject = useCallback(async (name?: string) => {
        const project = await createProject(name);
        setProjects(prev => [project, ...prev]);
        setActiveProject(project);
        return project;
    }, []);

    const selectProject = useCallback(async (id: string) => {
        try {
            const project = await getProject(id);
            setActiveProject(project);
        } catch (e: any) {
            setError(e.message);
        }
    }, []);

    const archiveProject = useCallback(async (id: string) => {
        await deleteProject(id);
        setProjects(prev => prev.filter(p => p.id !== id));
        if (activeProject?.id === id) {
            setActiveProject(null);
        }
    }, [activeProject]);

    const renameProject = useCallback(async (id: string, name: string) => {
        const updated = await updateProject(id, { name });
        setProjects(prev => prev.map(p => p.id === id ? { ...p, name } : p));
        if (activeProject?.id === id) {
            setActiveProject(prev => prev ? { ...prev, name } : null);
        }
    }, [activeProject]);

    return {
        projects,
        activeProject,
        loading,
        error,
        createNewProject,
        selectProject,
        archiveProject,
        renameProject,
        refreshProjects,
    };
}

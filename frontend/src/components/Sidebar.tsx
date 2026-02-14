import { useState } from 'react';
import { Plus, MessageSquare, Trash2, MoreHorizontal, LayoutGrid } from 'lucide-react';
import type { Project } from '../types';

interface SidebarProps {
    projects: Project[];
    activeProjectId: string | null;
    onSelectProject: (id: string) => void;
    onNewChat: () => void;
    onArchiveProject: (id: string) => void;
    onRenameProject: (id: string, name: string) => void;
    onOpenSettings: () => void;
}

function groupProjects(projects: Project[]) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 86400000);
    const weekAgo = new Date(today.getTime() - 7 * 86400000);

    const groups: { label: string; items: Project[] }[] = [
        { label: 'Today', items: [] },
        { label: 'Yesterday', items: [] },
        { label: 'This Week', items: [] },
        { label: 'Older', items: [] },
    ];

    for (const p of projects) {
        const d = new Date(p.updated_at);
        if (d >= today) groups[0].items.push(p);
        else if (d >= yesterday) groups[1].items.push(p);
        else if (d >= weekAgo) groups[2].items.push(p);
        else groups[3].items.push(p);
    }

    return groups.filter(g => g.items.length > 0);
}

export function Sidebar({
    projects, activeProjectId, onSelectProject, onNewChat, onArchiveProject, onRenameProject, onOpenSettings
}: SidebarProps) {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editName, setEditName] = useState('');
    const [menuId, setMenuId] = useState<string | null>(null);

    const groups = groupProjects(projects);

    const handleDoubleClick = (project: Project) => {
        setEditingId(project.id);
        setEditName(project.name);
    };

    const handleRename = (id: string) => {
        if (editName.trim()) {
            onRenameProject(id, editName.trim());
        }
        setEditingId(null);
    };

    return (
        <aside className="w-[260px] border-r border-surface-border flex flex-col flex-shrink-0 bg-surface-raised/50 h-full backdrop-blur-sm">
            {/* Header */}
            <div className="p-4 border-b border-surface-border/50">
                <button
                    onClick={onNewChat}
                    className="group w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-accent text-white shadow-lg shadow-accent/20 hover:bg-accent-hover hover:shadow-accent/30 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
                >
                    <Plus size={18} />
                    <span className="text-sm font-medium">New Project</span>
                </button>
            </div>

            {/* Project List */}
            <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-6 mt-3">
                {groups.map(group => (
                    <div key={group.label}>
                        <div className="px-3 mb-2 flex items-center gap-2">
                            <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider opacity-80">
                                {group.label}
                            </span>
                            <div className="h-px bg-surface-border flex-1 opacity-50" />
                        </div>

                        <div className="space-y-0.5">
                            {group.items.map(project => (
                                <div
                                    key={project.id}
                                    className={`group relative flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200 ${project.id === activeProjectId
                                        ? 'bg-surface-overlay text-text-primary shadow-sm'
                                        : 'text-text-secondary hover:bg-surface-overlay/50 hover:text-text-primary'
                                        }`}
                                    onClick={() => onSelectProject(project.id)}
                                    onDoubleClick={() => handleDoubleClick(project)}
                                >
                                    <MessageSquare size={16} className={`flex-shrink-0 transition-colors ${project.id === activeProjectId ? 'text-accent' : 'text-text-muted group-hover:text-text-secondary'
                                        }`} />

                                    {editingId === project.id ? (
                                        <input
                                            value={editName}
                                            onChange={e => setEditName(e.target.value)}
                                            onBlur={() => handleRename(project.id)}
                                            onKeyDown={e => {
                                                if (e.key === 'Enter') handleRename(project.id);
                                                if (e.key === 'Escape') setEditingId(null);
                                            }}
                                            className="flex-1 bg-transparent border-b border-accent outline-none text-sm text-text-primary p-0"
                                            autoFocus
                                            onClick={e => e.stopPropagation()}
                                        />
                                    ) : (
                                        <span className="flex-1 truncate text-sm font-medium">{project.name}</span>
                                    )}

                                    {/* Hover Actions */}
                                    <div className={`flex items-center gap-1 transition-opacity duration-200 ${menuId === project.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                                        }`}>
                                        <button
                                            className="p-1 rounded-md hover:bg-surface-border text-text-muted hover:text-text-primary transition-colors"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setMenuId(menuId === project.id ? null : project.id);
                                            }}
                                        >
                                            <MoreHorizontal size={14} />
                                        </button>
                                    </div>

                                    {/* Context Menu */}
                                    {menuId === project.id && (
                                        <div className="absolute right-2 top-full mt-1 z-50 bg-surface-overlay border border-surface-border rounded-lg shadow-xl py-1 transform origin-top-right animate-scale-in min-w-[140px]">
                                            <button
                                                className="w-full px-3 py-1.5 text-left text-xs font-medium text-text-secondary hover:bg-white/5 hover:text-text-primary flex items-center gap-2 transition-colors"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDoubleClick(project);
                                                    setMenuId(null);
                                                }}
                                            >
                                                <LayoutGrid size={14} />
                                                Rename
                                            </button>
                                            <div className="h-px bg-white/5 my-1" />
                                            <button
                                                className="w-full px-3 py-1.5 text-left text-xs font-medium text-red-400 hover:bg-red-500/10 flex items-center gap-2 transition-colors"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onArchiveProject(project.id);
                                                    setMenuId(null);
                                                }}
                                            >
                                                <Trash2 size={14} />
                                                Archive Project
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}

                {projects.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                        <div className="w-12 h-12 rounded-full bg-surface-raised border border-surface-border flex items-center justify-center mb-3">
                            <Plus size={20} className="text-text-muted" />
                        </div>
                        <p className="text-sm font-medium text-text-primary">No projects yet</p>
                        <p className="text-xs text-text-muted mt-1">Start a new chat to begin</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-surface-border/50 bg-black/10">
                <button
                    onClick={onOpenSettings}
                    className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-surface-overlay transition-colors group"
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-lg">
                        MM
                    </div>
                    <div className="flex-1 text-left">
                        <div className="text-xs font-medium text-text-primary group-hover:text-white transition-colors">Middle Manager</div>
                        <div className="text-[10px] text-text-muted">Pro Plan</div>
                    </div>
                    <div className="p-1.5 rounded-md hover:bg-white/10 text-text-muted hover:text-white transition-colors">
                        <MoreHorizontal size={14} />
                    </div>
                </button>
            </div>
        </aside>
    );
}

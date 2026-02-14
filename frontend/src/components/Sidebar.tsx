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

// ... imports
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
        <aside className="w-[260px] border-r border-slate-200 flex flex-col flex-shrink-0 bg-slate-50 h-full">
            {/* Header */}
            <div className="p-4 border-b border-slate-200">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-slate-900 text-white shadow-sm hover:bg-slate-800 transition-all duration-200"
                >
                    <Plus size={16} />
                    <span className="text-sm font-semibold">New Project</span>
                </button>
            </div>

            {/* Project List */}
            <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-6 mt-4">
                {groups.map(group => (
                    <div key={group.label} className="px-2">
                        <div className="px-2 mb-2 flex items-center gap-2">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none">
                                {group.label}
                            </span>
                        </div>

                        <div className="space-y-0.5">
                            {group.items.map(project => (
                                <div
                                    key={project.id}
                                    className={`group relative flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer transition-colors ${project.id === activeProjectId
                                        ? 'bg-slate-200 text-slate-900'
                                        : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900'
                                        }`}
                                    onClick={() => onSelectProject(project.id)}
                                    onDoubleClick={() => handleDoubleClick(project)}
                                >
                                    <MessageSquare size={14} className={`${project.id === activeProjectId ? 'text-slate-900' : 'text-slate-400 group-hover:text-slate-500'}`} />

                                    {editingId === project.id ? (
                                        <input
                                            value={editName}
                                            onChange={e => setEditName(e.target.value)}
                                            onBlur={() => handleRename(project.id)}
                                            onKeyDown={e => {
                                                if (e.key === 'Enter') handleRename(project.id);
                                                if (e.key === 'Escape') setEditingId(null);
                                            }}
                                            className="flex-1 bg-transparent border-b border-slate-900 outline-none text-sm text-slate-900 p-0"
                                            autoFocus
                                            onClick={e => e.stopPropagation()}
                                        />
                                    ) : (
                                        <span className="flex-1 truncate text-sm font-medium">{project.name}</span>
                                    )}

                                    <div className={`flex items-center gap-1 transition-opacity ${menuId === project.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                                        <button
                                            className="p-1 rounded hover:bg-slate-300/50 text-slate-400 hover:text-slate-900"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setMenuId(menuId === project.id ? null : project.id);
                                            }}
                                        >
                                            <MoreHorizontal size={14} />
                                        </button>
                                    </div>

                                    {menuId === project.id && (
                                        <div className="absolute right-2 top-full mt-1 z-50 bg-white border border-slate-200 rounded-lg shadow-xl py-1 min-w-[140px] animate-scale-in">
                                            <button
                                                className="w-full px-3 py-1.5 text-left text-xs font-medium text-slate-600 hover:bg-slate-50 flex items-center gap-2"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDoubleClick(project);
                                                    setMenuId(null);
                                                }}
                                            >
                                                <LayoutGrid size={14} />
                                                Rename
                                            </button>
                                            <div className="h-px bg-slate-100 my-1" />
                                            <button
                                                className="w-full px-3 py-1.5 text-left text-xs font-medium text-red-600 hover:bg-red-50 flex items-center gap-2"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onArchiveProject(project.id);
                                                    setMenuId(null);
                                                }}
                                            >
                                                <Trash2 size={14} />
                                                Archive
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-slate-200 bg-white">
                <button
                    onClick={onOpenSettings}
                    className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-slate-50 transition-colors group"
                >
                    <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 font-bold text-[10px] shadow-sm">
                        MM
                    </div>
                    <div className="flex-1 text-left">
                        <div className="text-xs font-semibold text-slate-900">Middle Manager</div>
                        <div className="text-[10px] text-slate-500 font-medium">Professional Workspace</div>
                    </div>
                </button>
            </div>
        </aside>
    );
}


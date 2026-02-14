import { useState, useEffect } from 'react';
import { Plus, MessageSquare, Trash2, MoreHorizontal, LayoutGrid, ChevronLeft, ChevronRight, Moon, Sun } from 'lucide-react';
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
    const [collapsed, setCollapsed] = useState(() => {
        return localStorage.getItem('sidebar_collapsed') === 'true';
    });
    const [isDark, setIsDark] = useState(false);

    useEffect(() => {
        localStorage.setItem('sidebar_collapsed', String(collapsed));
    }, [collapsed]);

    useEffect(() => {
        // Sync state with DOM
        const checkDarkMode = () => {
            setIsDark(document.documentElement.classList.contains('dark'));
        };

        // Initial check
        checkDarkMode();

        // Observe changes
        const observer = new MutationObserver(checkDarkMode);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

        return () => observer.disconnect();
    }, []);

    const toggleTheme = () => {
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.theme = 'light';
        } else {
            document.documentElement.classList.add('dark');
            localStorage.theme = 'dark';
        }
    };

    const groups = groupProjects(projects);

    const handleDoubleClick = (project: Project) => {
        if (collapsed) {
            setCollapsed(false);
            setTimeout(() => {
                setEditingId(project.id);
                setEditName(project.name);
            }, 100);
        } else {
            setEditingId(project.id);
            setEditName(project.name);
        }
    };

    const handleRename = (id: string) => {
        if (editName.trim()) {
            onRenameProject(id, editName.trim());
        }
        setEditingId(null);
    };

    return (
        <aside
            className={`
                relative flex flex-col flex-shrink-0 
                bg-surface-container border-r border-border h-full 
                transition-all duration-300 ease-in-out
                ${collapsed ? 'w-[72px]' : 'w-[280px]'}
            `}
        >
            {/* Collapse Toggle */}
            <button
                onClick={() => setCollapsed(!collapsed)}
                className="absolute -right-3 top-6 z-10 p-1 bg-surface border border-border rounded-full shadow-sm text-muted-foreground hover:text-foreground hover:bg-surface-raised transition-colors flex items-center justify-center transform hover:scale-105"
            >
                {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-center">
                <button
                    onClick={onNewChat}
                    className={`
                        flex items-center justify-center gap-2 rounded-lg 
                        bg-primary text-primary-foreground shadow-sm 
                        hover:bg-primary-hover transition-all duration-200
                        ${collapsed ? 'w-10 h-10 p-0' : 'w-full px-3 py-2.5'}
                    `}
                    title="New Project"
                >
                    <Plus size={collapsed ? 20 : 18} />
                    {!collapsed && <span className="text-sm font-semibold">New Project</span>}
                </button>
            </div>

            {/* Project List */}
            <div className={`flex-1 overflow-y-auto ${collapsed ? 'px-2' : 'px-3'} py-3 space-y-6 scrollbar-thin scrollbar-thumb-secondary-muted`}>
                {projects.length === 0 && !collapsed && (
                    <div className="text-center text-xs text-muted-foreground py-8">
                        No projects yet.
                        <br />Start a new chat!
                    </div>
                )}

                {groups.map(group => (
                    <div key={group.label} className={collapsed ? 'px-0' : 'px-1'}>
                        {!collapsed && (
                            <div className="px-2 mb-2 flex items-center gap-2">
                                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest leading-none">
                                    {group.label}
                                </span>
                            </div>
                        )}

                        <div className="space-y-1">
                            {group.items.map(project => (
                                <div
                                    key={project.id}
                                    className={`
                                        group relative flex items-center 
                                        rounded-md cursor-pointer transition-all duration-200
                                        ${collapsed ? 'justify-center p-2' : 'gap-2.5 px-3 py-2'}
                                        ${project.id === activeProjectId
                                            ? 'bg-surface-raised-high text-foreground font-medium shadow-sm'
                                            : 'text-muted-foreground hover:bg-surface-raised hover:text-foreground'
                                        }
                                    `}
                                    onClick={() => onSelectProject(project.id)}
                                    onDoubleClick={() => handleDoubleClick(project)}
                                    title={collapsed ? project.name : undefined}
                                >
                                    <MessageSquare
                                        size={collapsed ? 18 : 16}
                                        className={`flex-shrink-0 ${project.id === activeProjectId ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`}
                                    />

                                    {!collapsed && (
                                        <>
                                            {editingId === project.id ? (
                                                <input
                                                    value={editName}
                                                    onChange={e => setEditName(e.target.value)}
                                                    onBlur={() => handleRename(project.id)}
                                                    onKeyDown={e => {
                                                        if (e.key === 'Enter') handleRename(project.id);
                                                        if (e.key === 'Escape') setEditingId(null);
                                                    }}
                                                    className="flex-1 bg-transparent border-b border-primary outline-none text-sm text-foreground p-0 min-w-0"
                                                    autoFocus
                                                    onClick={e => e.stopPropagation()}
                                                />
                                            ) : (
                                                <span className="flex-1 truncate text-sm">{project.name}</span>
                                            )}

                                            <div className={`flex items-center gap-1 transition-opacity ${menuId === project.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                                                <button
                                                    className="p-1 rounded hover:bg-surface-raised-high text-muted-foreground hover:text-foreground"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setMenuId(menuId === project.id ? null : project.id);
                                                    }}
                                                >
                                                    <MoreHorizontal size={14} />
                                                </button>
                                            </div>
                                        </>
                                    )}

                                    {/* Dropdown Menu */}
                                    {menuId === project.id && !collapsed && (
                                        <div className="absolute right-2 top-full mt-1 z-50 bg-surface border border-border rounded-lg shadow-elevation-2 py-1 min-w-[140px] animate-scale-in">
                                            <button
                                                className="w-full px-3 py-1.5 text-left text-xs font-medium text-foreground hover:bg-surface-raised flex items-center gap-2"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDoubleClick(project);
                                                    setMenuId(null);
                                                }}
                                            >
                                                <LayoutGrid size={14} />
                                                Rename
                                            </button>
                                            <div className="h-px bg-border my-1" />
                                            <button
                                                className="w-full px-3 py-1.5 text-left text-xs font-medium text-error hover:bg-error/10 flex items-center gap-2"
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
            <div className="p-3 border-t border-border bg-surface">
                <div className={`flex items-center gap-2 ${collapsed ? 'flex-col' : 'flex-row'}`}>
                    <button
                        onClick={onOpenSettings}
                        className={`
                            flex items-center gap-3 rounded-lg hover:bg-surface-raised transition-colors group flex-1
                            ${collapsed ? 'justify-center w-full p-2' : 'p-2 w-full'}
                        `}
                        title="Settings"
                    >
                        <div className="w-8 h-8 rounded-lg bg-surface-raised border border-border flex items-center justify-center text-muted-foreground font-bold text-[10px] shadow-sm group-hover:border-primary/20 group-hover:text-primary transition-colors">
                            MM
                        </div>
                        {!collapsed && (
                            <div className="flex-1 text-left min-w-0">
                                <div className="text-xs font-semibold text-foreground truncate">BrainStrom Ai</div>
                                <div className="text-[10px] text-muted-foreground font-medium truncate">Professional Workspace</div>
                            </div>
                        )}
                    </button>

                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className={`
                            flex items-center justify-center rounded-lg hover:bg-surface-raised text-muted-foreground hover:text-foreground transition-colors
                            ${collapsed ? 'w-8 h-8' : 'w-8 h-8 ml-1'}
                        `}
                        title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
                    >
                        {isDark ? <Sun size={16} /> : <Moon size={16} />}
                    </button>
                </div>
            </div>
        </aside>
    );
}

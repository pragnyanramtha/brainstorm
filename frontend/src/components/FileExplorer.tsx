import { useState, useEffect } from 'react';
import { FolderOpen, File, ChevronRight, ChevronDown, X, ExternalLink, RefreshCw } from 'lucide-react';

interface FileExplorerProps {
    projectPath: string;
    onClose: () => void;
}

interface FileNode {
    name: string;
    path: string;
    isDirectory: boolean;
    children?: FileNode[];
}

// Simple color mapping for common files
const getFileColor = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    switch (ext) {
        case 'ts': case 'tsx': return 'text-blue-400';
        case 'js': case 'jsx': return 'text-yellow-400';
        case 'py': return 'text-green-400';
        case 'css': case 'scss': return 'text-pink-400';
        case 'html': return 'text-orange-400';
        case 'json': return 'text-yellow-200';
        case 'md': return 'text-purple-400';
        case 'sql': return 'text-cyan-400';
        case 'env': return 'text-emerald-400';
        default: return 'text-text-muted';
    }
};

function FileTreeNode({ node, depth = 0 }: { node: FileNode; depth?: number }) {
    const [expanded, setExpanded] = useState(depth < 2);

    return (
        <div>
            <div
                className={`group flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-surface-overlay transition-colors text-sm rounded ${node.isDirectory ? 'text-text-primary font-medium' : 'text-text-secondary'
                    }`}
                style={{ paddingLeft: `${depth * 14 + 12}px` }}
                onClick={() => node.isDirectory && setExpanded(!expanded)}
            >
                {node.isDirectory ? (
                    <>
                        {expanded ? <ChevronDown size={14} className="text-text-muted" /> : <ChevronRight size={14} className="text-text-muted" />}
                        <FolderOpen size={16} className="text-accent group-hover:text-accent-hover transition-colors" />
                    </>
                ) : (
                    <>
                        <span className="w-3.5" />
                        <File size={15} className={getFileColor(node.name)} />
                    </>
                )}
                <span className="truncate opacity-90 group-hover:opacity-100 transition-opacity">{node.name}</span>
            </div>

            {node.isDirectory && expanded && node.children && (
                <div>
                    {node.children.map(child => (
                        <FileTreeNode key={child.path} node={child} depth={depth + 1} />
                    ))}
                </div>
            )}
        </div>
    );
}

export function FileExplorer({ projectPath, onClose }: FileExplorerProps) {
    const [files, setFiles] = useState<FileNode[] | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    // Mock file tree for UI demo
    useEffect(() => {
        const demoFiles: FileNode[] = [
            {
                name: 'src',
                path: '/src',
                isDirectory: true,
                children: [
                    { name: 'App.tsx', path: '/src/App.tsx', isDirectory: false },
                    { name: 'index.css', path: '/src/index.css', isDirectory: false },
                    { name: 'api.ts', path: '/src/api.ts', isDirectory: false },
                ]
            },
            { name: 'package.json', path: '/package.json', isDirectory: false },
            { name: 'tsconfig.json', path: '/tsconfig.json', isDirectory: false },
            { name: 'README.md', path: '/README.md', isDirectory: false },
        ];
        setFiles(demoFiles);
    }, [projectPath]);

    const handleRefresh = () => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 800);
    };

    return (
        <aside className="w-[300px] border-l border-surface-border flex flex-col flex-shrink-0 bg-surface h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                    Explorer
                </span>
                <div className="flex items-center gap-1">
                    <button
                        onClick={handleRefresh}
                        className={`p-1.5 rounded-lg hover:bg-surface-hover text-text-muted hover:text-text-primary transition-all ${refreshing ? 'animate-spin' : ''}`}
                        title="Refresh"
                    >
                        <RefreshCw size={14} />
                    </button>
                    <button
                        className="p-1.5 rounded-lg hover:bg-surface-hover text-text-muted hover:text-text-primary transition-colors"
                        title="Open in OS"
                    >
                        <ExternalLink size={14} />
                    </button>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-surface-hover text-text-muted hover:text-text-primary transition-colors"
                    >
                        <X size={14} />
                    </button>
                </div>
            </div>

            {/* File Tree */}
            <div className="flex-1 overflow-y-auto py-2 custom-scrollbar">
                {files && files.length > 0 ? (
                    files.map(node => <FileTreeNode key={node.path} node={node} />)
                ) : (
                    <div className="px-4 py-8 text-center">
                        <div className="w-10 h-10 rounded-full bg-surface-raised border border-surface-border flex items-center justify-center mx-auto mb-3">
                            <FolderOpen size={18} className="text-text-muted" />
                        </div>
                        <p className="text-sm text-text-muted">No files found</p>
                    </div>
                )}
            </div>

            {/* Footer Info */}
            <div className="p-3 border-t border-surface-border text-[10px] text-text-muted font-mono truncate px-4 bg-surface-raised/20">
                {projectPath}
            </div>
        </aside>
    );
}

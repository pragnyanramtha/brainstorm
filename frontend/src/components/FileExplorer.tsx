import { useState, useEffect } from 'react';
import { FolderOpen, File, ChevronRight, ChevronDown, X, ExternalLink } from 'lucide-react';

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

function FileIcon({ name }: { name: string }) {
    const ext = name.split('.').pop()?.toLowerCase();
    const colors: Record<string, string> = {
        ts: 'text-blue-400',
        tsx: 'text-blue-400',
        js: 'text-yellow-400',
        jsx: 'text-yellow-400',
        py: 'text-green-400',
        css: 'text-pink-400',
        html: 'text-orange-400',
        json: 'text-yellow-300',
        md: 'text-gray-400',
        txt: 'text-gray-400',
        sql: 'text-cyan-400',
        env: 'text-emerald-400',
    };

    return <File size={14} className={colors[ext || ''] || 'text-text-muted'} />;
}

function FileTreeNode({ node, depth = 0 }: { node: FileNode; depth?: number }) {
    const [expanded, setExpanded] = useState(depth < 2);

    return (
        <div>
            <div
                className={`flex items-center gap-1.5 px-2 py-1 cursor-pointer hover:bg-surface-hover rounded text-sm transition-smooth ${node.isDirectory ? 'text-text-secondary' : 'text-text-muted'
                    }`}
                style={{ paddingLeft: `${depth * 16 + 8}px` }}
                onClick={() => node.isDirectory && setExpanded(!expanded)}
            >
                {node.isDirectory ? (
                    <>
                        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                        <FolderOpen size={14} className="text-accent/70" />
                    </>
                ) : (
                    <>
                        <span className="w-3" />
                        <FileIcon name={node.name} />
                    </>
                )}
                <span className="truncate">{node.name}</span>
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

    // Stub: would fetch file tree from backend
    useEffect(() => {
        setFiles([]);
    }, [projectPath]);

    return (
        <aside className="w-[280px] border-l border-surface-border flex flex-col flex-shrink-0 bg-surface">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2.5 border-b border-surface-border">
                <span className="text-text-secondary text-xs font-medium uppercase tracking-wider">Files</span>
                <div className="flex items-center gap-1">
                    <button
                        className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text-secondary transition-smooth"
                        title="Open folder"
                    >
                        <ExternalLink size={14} />
                    </button>
                    <button
                        onClick={onClose}
                        className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text-secondary transition-smooth"
                    >
                        <X size={14} />
                    </button>
                </div>
            </div>

            {/* File Tree */}
            <div className="flex-1 overflow-y-auto py-1">
                {files && files.length > 0 ? (
                    files.map(node => <FileTreeNode key={node.path} node={node} />)
                ) : (
                    <div className="px-3 py-8 text-center text-text-muted text-xs">
                        No files yet. Start chatting to create your project.
                    </div>
                )}
            </div>
        </aside>
    );
}

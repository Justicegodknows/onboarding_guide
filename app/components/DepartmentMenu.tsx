"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { DepartmentInfo } from "../api/backend";

interface DepartmentMenuProps {
    departments: DepartmentInfo[];
}

export default function DepartmentMenu({ departments }: DepartmentMenuProps) {
    const pathname = usePathname();

    return (
        <aside className="w-72 min-h-screen bg-zinc-100 dark:bg-zinc-900 border-r p-4 flex flex-col gap-3">
            <h2 className="text-lg font-bold">Departments</h2>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Open a department workspace to access the main chat agent and trainer sub-agent.
            </p>
            <ul className="flex-1">
                {departments.map((dept) => {
                    const href = `/departments/${dept.id}`;
                    const active = pathname === href;
                    return (
                        <li key={dept.id}>
                            <Link
                                className={`block w-full text-left px-3 py-2 rounded mb-2 transition-colors ${active
                                    ? "bg-blue-600 text-white"
                                    : "hover:bg-zinc-200 dark:hover:bg-zinc-800"
                                    }`}
                                href={href}
                            >
                                <div className="font-semibold">{dept.name}</div>
                                <div className="text-xs text-zinc-500 dark:text-zinc-400">{dept.description}</div>
                            </Link>
                        </li>
                    );
                })}
            </ul>
            <Link
                href="/"
                className="text-sm text-blue-600 hover:text-blue-700 underline underline-offset-2"
            >
                Back to overview
            </Link>
        </aside>
    );
}

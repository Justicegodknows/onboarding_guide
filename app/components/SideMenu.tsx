"use client";
import { useState } from "react";
import { departments, Department } from "./departments";

interface SideMenuProps {
    selected: string;
    onSelect: (id: string) => void;
}

export default function SideMenu({ selected, onSelect }: SideMenuProps) {
    return (
        <aside className="w-64 min-h-screen bg-zinc-100 dark:bg-zinc-900 border-r p-4">
            <h2 className="text-lg font-bold mb-4">Departments</h2>
            <ul>
                {departments.map((dept) => (
                    <li key={dept.id}>
                        <button
                            className={`w-full text-left px-3 py-2 rounded mb-2 transition-colors ${selected === dept.id
                                    ? "bg-blue-600 text-white"
                                    : "hover:bg-zinc-200 dark:hover:bg-zinc-800"
                                }`}
                            onClick={() => onSelect(dept.id)}
                        >
                            <div className="font-semibold">{dept.name}</div>
                            <div className="text-xs text-zinc-500 dark:text-zinc-400">{dept.description}</div>
                        </button>
                    </li>
                ))}
            </ul>
        </aside>
    );
}

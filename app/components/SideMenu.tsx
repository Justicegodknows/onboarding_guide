"use client";
import { useState } from "react";
import { departments, Department } from "./departments";
import TrainerChatBox from "./TrainerChatBox";

interface SideMenuProps {
    selected: string;
    onSelect: (id: string) => void;
}

export default function SideMenu({ selected, onSelect }: SideMenuProps) {
    return (
        <aside className="w-64 min-h-screen bg-white border-r border-gray-200 p-4 flex flex-col">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Departments</h2>
            <ul className="flex-1">
                {departments.map((dept) => (
                    <li key={dept.id}>
                        <button
                            className={`w-full text-left px-3 py-2 rounded-lg mb-2 transition-colors ${selected === dept.id
                                ? "bg-blue-600 text-white"
                                : "text-gray-700 hover:bg-blue-50 hover:text-blue-700"
                                }`}
                            onClick={() => onSelect(dept.id)}
                        >
                            <div className="font-semibold">{dept.name}</div>
                            <div className={`text-xs ${selected === dept.id ? "text-blue-100" : "text-gray-500"}`}>{dept.description}</div>
                        </button>
                    </li>
                ))}
            </ul>
            <TrainerChatBox />
        </aside>
    );
}

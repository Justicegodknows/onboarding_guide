"use client";

import { sendDepartmentChat, sendDepartmentTrainerChat } from "../api/backend";
import ChatBox from "./ChatBox";
import TrainerChatBox from "./TrainerChatBox";

interface DepartmentWorkspaceProps {
    id: string;
    name: string;
    description: string;
    info: string;
}

export default function DepartmentWorkspace({ id, name, description, info }: DepartmentWorkspaceProps) {
    return (
        <div className="w-full max-w-4xl flex flex-col gap-6 mx-auto">
            <h1 className="text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
                {name} Workspace
            </h1>
            <p className="text-lg leading-7 text-black/70 dark:text-zinc-400">{info}</p>

            <section className="p-4 rounded bg-zinc-100 dark:bg-zinc-900">
                <h2 className="text-lg font-bold mb-2">Department Overview</h2>
                <p className="text-zinc-700 dark:text-zinc-300">{description}</p>
            </section>

            <ChatBox
                title={`${name} - Main Chat Agent`}
                onSend={(question, history) => sendDepartmentChat(id, question, history)}
            />

            <div className="w-full max-w-lg mx-auto mt-2 p-4 border rounded bg-white dark:bg-zinc-900">
                <TrainerChatBox
                    title={`${name} - Trainer Sub-Agent`}
                    onSend={(question, history) => sendDepartmentTrainerChat(id, question, history)}
                />
            </div>
        </div>
    );
}

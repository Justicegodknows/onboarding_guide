import type { PropsWithChildren } from "react";

export default function CreativeLayout({ children }: PropsWithChildren) {
    return (
        <div className="min-h-screen bg-slate-50 text-slate-900">
            {children}
        </div>
    );
}

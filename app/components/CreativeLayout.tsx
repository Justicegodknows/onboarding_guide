import type { PropsWithChildren } from "react";

export default function CreativeLayout({ children }: PropsWithChildren) {
    return (
        <div className="min-h-screen bg-white text-gray-900">
            {children}
        </div>
    );
}

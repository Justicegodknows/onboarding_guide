import ChatBox from "../components/ChatBox";

export default function AgentPage() {
    return (
        <div className="min-h-screen bg-gray-50">
            <ChatBox
                title="Nemoclaw Agent"
                agentMode={true}
                fullPage={true}
            />
        </div>
    );
}

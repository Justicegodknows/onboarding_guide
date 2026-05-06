import Link from "next/link";

import { getDepartments } from "./api/backend";

export default async function Home() {
  const departments = await getDepartments();

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-black py-16 px-8 font-sans">
      <div className="w-full max-w-5xl mx-auto flex flex-col gap-8">
        <header>
          <h1 className="text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Department Workspaces
          </h1>
          <p className="text-lg leading-7 text-black/70 dark:text-zinc-400 mt-2">
            Choose a department to open its dedicated workspace. Each workspace includes
            direct access to the main chat agent and trainer sub-agent.
          </p>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {departments.map((department) => (
            <Link
              key={department.id}
              href={`/departments/${department.id}`}
              className="block rounded border bg-white dark:bg-zinc-900 p-5 hover:border-blue-400 transition-colors"
            >
              <h2 className="text-xl font-bold mb-2">{department.name}</h2>
              <p className="text-zinc-700 dark:text-zinc-300 mb-2">{department.description}</p>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">{department.info}</p>
            </Link>
          ))}
        </section>
      </div>
    </main>
          {/* --- WHO IT IS FOR --- */}
          <div className="w-full max-w-4xl mb-20 bg-zinc-100 p-8 rounded-3xl border border-zinc-200 text-left">
            <h2 className="text-2xl font-bold text-black mb-4">Who is VaultMind for?</h2>
            <p className="text-zinc-700 mb-6">
              Built for organizations that manage sensitive internal knowledge and need
              private AI workflows with access control, auditability, and secure onboarding.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                <span className="text-accent font-bold block mb-1">Operations Teams</span>
                <p className="text-sm text-zinc-600">Get consistent answers from policies, SOPs, and internal docs.</p>
              </div>
              <div className="p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                <span className="text-accent font-bold block mb-1">Compliance and IT</span>
                <p className="text-sm text-zinc-600">Keep documents local with role-based authorization and audit trails.</p>
              </div>
              <div className="p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                <span className="text-accent font-bold block mb-1">New Employee Onboarding</span>
                <p className="text-sm text-zinc-600">Help hires find internal knowledge faster through guided Q&amp;A.</p>
              </div>
            </div>
          </div>

          {/* --- HOW IT WORKS (4-STEP FLOW) --- */}
          <div className="w-full max-w-4xl mb-20">
            <h2 className="text-2xl font-bold text-black mb-8 uppercase tracking-widest opacity-80">
              How It Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
              <div className="p-6 rounded-2xl bg-card shadow-sm border border-zinc-200 text-left relative z-10">
                <div className="text-accent font-bold text-lg mb-2">01. Ingest</div>
                <p className="text-sm text-black">Upload internal documents and parse content through the ingestion pipeline.</p>
              </div>
              <div className="p-6 rounded-2xl bg-card shadow-sm border border-zinc-200 text-left relative z-10">
                <div className="text-accent font-bold text-lg mb-2">02. Vectorize</div>
                <p className="text-sm text-black">Create embeddings with the local embedding model and store them in ChromaDB.</p>
              </div>
              <div className="p-6 rounded-2xl bg-card shadow-sm border border-zinc-200 text-left relative z-10">
                <div className="text-accent font-bold text-lg mb-2">03. Retrieve</div>
                <p className="text-sm text-black">Retrieve relevant knowledge from ChromaDB with role-aware filtering.</p>
              </div>
              <div className="p-6 rounded-2xl bg-card shadow-sm border border-zinc-200 text-left relative z-10">
                <div className="text-accent font-bold text-lg mb-2">04. Generate</div>
                <p className="text-sm text-black">Generate grounded answers locally with Llama models through Ollama.</p>
              </div>
            </div>
          </div>

          {/* --- ARCHITECTURE & STACK --- */}
          <div className="w-full max-w-4xl mb-20">
            <h2 className="text-2xl font-bold text-black mb-8 uppercase tracking-widest opacity-80">
              Architecture and Tech Stack
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="p-4 bg-zinc-100 rounded-lg border-l-4 border-accent">
                <span className="font-bold text-black block">Frontend</span>
                <span className="text-xs text-zinc-600">Next.js + TypeScript + Tailwind UI for employee access</span>
              </div>
              <div className="p-4 bg-zinc-100 rounded-lg border-l-4 border-accent">
                <span className="font-bold text-black block">Backend</span>
                <span className="text-xs text-zinc-600">FastAPI APIs for auth, chat routing, and ingestion orchestration</span>
              </div>
              <div className="p-4 bg-zinc-100 rounded-lg border-l-4 border-accent">
                <span className="font-bold text-black block">Knowledge Layer</span>
                <span className="text-xs text-zinc-600">LangChain + ChromaDB + PyMuPDF + nomic-embed-text</span>
              </div>
              <div className="p-4 bg-zinc-100 rounded-lg border-l-4 border-accent">
                <span className="font-bold text-black block">Inference and Runtime</span>
                <span className="text-xs text-zinc-600">Local Llama model served by Ollama in Docker environment</span>
              </div>
            </div>
          </div>

          {/* --- DEPLOYMENT, MONITORING, ROADMAP --- */}
          <div className="w-full max-w-4xl mb-20 text-left bg-white border border-zinc-200 rounded-2xl p-6">
            <h2 className="text-2xl font-bold text-black mb-6">Deployment and Monitoring Roadmap</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-200">
                <p className="font-semibold text-black">Phase A - Foundation</p>
                <p className="text-sm text-zinc-700">Provision Docker services and validate local Llama runtime and API health.</p>
              </div>
              <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-200">
                <p className="font-semibold text-black">Phase B - Security and Access</p>
                <p className="text-sm text-zinc-700">Enable employee signup/login and enforce JWT role-based authorization.</p>
              </div>
              <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-200">
                <p className="font-semibold text-black">Phase C - Knowledge Operations</p>
                <p className="text-sm text-zinc-700">Run document upload ingestion, embedding, and ChromaDB retrieval validation.</p>
              </div>
              <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-200">
                <p className="font-semibold text-black">Phase D - Rollout and Monitoring</p>
                <p className="text-sm text-zinc-700">Track health, logs, and retrieval quality, then expand onboarding coverage.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20 w-full max-w-5xl">
            <div className="p-8 rounded-3xl bg-primary text-white shadow-xl text-left">
              <div className="text-3xl mb-4">🔒</div>
              <h3 className="text-xl font-bold mb-3 text-white">Local-First AI</h3>
              <p className="text-sm opacity-90 leading-relaxed text-white">
                Data stays inside your environment across ingestion, retrieval, and answer generation.
              </p>
            </div>
            <div className="p-8 rounded-3xl bg-primary text-white shadow-xl text-left">
              <div className="text-3xl mb-4">🧭</div>
              <h3 className="text-xl font-bold mb-3 text-white">Grounded Responses</h3>
              <p className="text-sm opacity-90 leading-relaxed text-white">
                RAG answers are based on indexed company documents and can be traced to source context.
              </p>
            </div>
            <div className="p-8 rounded-3xl bg-primary text-white shadow-xl text-left">
              <div className="text-3xl mb-4">🔑</div>
              <h3 className="text-xl font-bold mb-3 text-white">Role-Aware Access</h3>
              <p className="text-sm opacity-90 leading-relaxed text-white">
                Employee identity and role claims guide what each user can retrieve and manage.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => resetAuthState("login")}
              className="px-10 py-4 bg-primary text-white rounded-full font-bold text-lg hover:bg-opacity-90 transition-all shadow-xl"
            >
              Employee Sign In
            </button>
            <button
              onClick={() => resetAuthState("signup")}
              className="px-10 py-4 bg-white text-black border border-zinc-300 rounded-full font-bold text-lg hover:bg-zinc-100 transition-all shadow-xl"
            >
              Create Employee Account
            </button>
            <Link
              href="/docs"
              className="px-10 py-4 bg-zinc-100 text-black border border-zinc-300 rounded-full font-bold text-lg hover:bg-zinc-200 transition-all shadow-xl text-center"
            >
              User Guide
            </Link>
          </div>
        </div>
      )}

      {/* --- LOGIN FORM --- */}
      {authView === "login" && !isChatOpen && (
        <div className="flex flex-col items-center justify-center px-6 py-20 min-h-screen">
          <div className="w-full max-w-md p-8 bg-white rounded-3xl shadow-2xl border border-zinc-200">
            <div className="text-center mb-8">
              <div className="text-4xl mb-2">🔒</div>
              <h2 className="text-3xl font-bold text-black">Employee Login</h2>
              <p className="text-zinc-500">Authenticate and continue to role-based knowledge access</p>
            </div>
            <form onSubmit={handleLogin} className="space-y-6">
              <div className="text-left">
                <label className="block text-sm font-bold text-black mb-2">Corporate Email</label>
                <input
                  type="email"
                  required
                  className="w-full p-3 border rounded-xl focus:ring-2 focus:ring-accent outline-none text-black"
                  placeholder="name@company.local"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="text-left">
                <label className="block text-sm font-bold text-black mb-2">Password</label>
                <input
                  type="password"
                  required
                  className="w-full p-3 border rounded-xl focus:ring-2 focus:ring-accent outline-none text-black"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-4 bg-primary text-white rounded-xl font-bold hover:bg-opacity-90 transition-all shadow-lg"
              >
                {authLoading ? "Signing in..." : "Sign In"}
              </button>
              {authError && <p className="text-sm text-red-600 text-center">{authError}</p>}
              <button
                type="button"
                onClick={() => resetAuthState("signup")}
                className="w-full py-2 text-zinc-500 text-sm hover:text-black transition-colors"
              >
                Need an account? Sign Up
              </button>
              <button
                type="button"
                onClick={() => setAuthView(null)}
                className="w-full py-2 text-zinc-500 text-sm hover:text-black transition-colors"
              >
                Back to Home
              </button>
            </form>
          </div>
        </div>
      )}

      {/* --- SIGNUP FORM --- */}
      {authView === "signup" && !isChatOpen && (
        <div className="flex flex-col items-center justify-center px-6 py-20 min-h-screen">
          <div className="w-full max-w-md p-8 bg-white rounded-3xl shadow-2xl border border-zinc-200">
            <div className="text-center mb-8">
              <div className="text-4xl mb-2">🧾</div>
              <h2 className="text-3xl font-bold text-black">Create Employee Account</h2>
              <p className="text-zinc-500">Register employee profile for secure role-based access</p>
            </div>
            <form onSubmit={handleSignup} className="space-y-6">
              <div className="text-left">
                <label className="block text-sm font-bold text-black mb-2">Corporate Email</label>
                <input
                  type="email"
                  required
                  className="w-full p-3 border rounded-xl focus:ring-2 focus:ring-accent outline-none text-black"
                  placeholder="name@company.local"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="text-left">
                <label className="block text-sm font-bold text-black mb-2">Department</label>
                <input
                  type="text"
                  required
                  className="w-full p-3 border rounded-xl focus:ring-2 focus:ring-accent outline-none text-black"
                  placeholder="Finance, HR, IT..."
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                />
              </div>
              <div className="text-left">
                <label className="block text-sm font-bold text-black mb-2">Role</label>
                <select
                  className="w-full p-3 border rounded-xl focus:ring-2 focus:ring-accent outline-none text-black bg-white"
                  value={role}
                  onChange={(e) => setRole(e.target.value as "USER" | "ADMIN")}
                >
                  <option value="USER">USER</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>
              <div className="text-left">
                <label className="block text-sm font-bold text-black mb-2">Password</label>
                <input
                  type="password"
                  required
                  className="w-full p-3 border rounded-xl focus:ring-2 focus:ring-accent outline-none text-black"
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-4 bg-primary text-white rounded-xl font-bold hover:bg-opacity-90 transition-all shadow-lg"
              >
                {authLoading ? "Creating account..." : "Create Account"}
              </button>
              {authError && <p className="text-sm text-red-600 text-center">{authError}</p>}
              <button
                type="button"
                onClick={() => resetAuthState("login")}
                className="w-full py-2 text-zinc-500 text-sm hover:text-black transition-colors"
              >
                Already registered? Sign In
              </button>
              <button
                type="button"
                onClick={() => setAuthView(null)}
                className="w-full py-2 text-zinc-500 text-sm hover:text-black transition-colors"
              >
                Back to Home
              </button>
            </form>
          </div>
        </div>
      )}

      {/* --- CHAT INTERFACE SECTION --- */}
      {isChatOpen && (
        <div className="flex flex-col h-screen">
          <header className="p-4 bg-primary text-white flex items-center justify-between shadow-md">
            <div className="flex items-center gap-2 font-bold text-xl">
              <span className="text-accent">🔒</span> VaultMind Assistant
            </div>
            <button
              onClick={() => {
                setIsChatOpen(false);
                setAuthView(null);
              }}
              className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1 rounded-md transition-colors"
            >
              &larr; Back to Home
            </button>
          </header>
          <main className="flex-1 overflow-hidden bg-zinc-50 dark:bg-black p-4 md:p-8">
            <ChatBox />
          </main>
        </div>
      )}
    </div>
  );
}

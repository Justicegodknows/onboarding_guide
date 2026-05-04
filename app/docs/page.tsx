"use client";

import Link from "next/link";

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-background text-foreground px-6 py-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="space-y-2">
          <h1 className="text-4xl font-extrabold text-black">VaultMind User Guide</h1>
          <p className="text-zinc-700">
            Employee onboarding, role-based access, RAG upload workflow, and operations checklist.
          </p>
          <Link href="/" className="inline-block text-sm font-semibold text-accent hover:underline">
            ← Back to Landing Page
          </Link>
        </header>

        <section className="bg-white border border-zinc-200 rounded-2xl p-6 space-y-3">
          <h2 className="text-2xl font-bold text-black">1) Access and Identity</h2>
          <p className="text-zinc-700">Create employee accounts, assign department and role, then sign in.</p>
          <ul className="list-disc pl-5 text-zinc-700 space-y-1">
            <li>`USER` accounts can query authorized knowledge.</li>
            <li>`ADMIN` accounts can manage upload and knowledge operations.</li>
            <li>JWT tokens carry role and department claims for authorization.</li>
          </ul>
        </section>

        <section className="bg-white border border-zinc-200 rounded-2xl p-6 space-y-3">
          <h2 className="text-2xl font-bold text-black">2) Document Upload and RAG</h2>
          <p className="text-zinc-700">
            Upload company files, parse content, split into chunks, generate embeddings, and store in ChromaDB.
          </p>
          <ul className="list-disc pl-5 text-zinc-700 space-y-1">
            <li>Parsing: PyMuPDF.</li>
            <li>Embedding model: `nomic-embed-text` for ingestion and retrieval consistency.</li>
            <li>Vector storage: ChromaDB.</li>
            <li>Generation model: local Llama model via Ollama.</li>
          </ul>
        </section>

        <section className="bg-white border border-zinc-200 rounded-2xl p-6 space-y-3">
          <h2 className="text-2xl font-bold text-black">3) Deployment and Monitoring</h2>
          <ul className="list-disc pl-5 text-zinc-700 space-y-1">
            <li>Run backend services with Docker Compose.</li>
            <li>Check API health and model availability before user rollout.</li>
            <li>Track ingestion status, query latency, and retrieval quality.</li>
            <li>Review logs regularly for authentication and document access activity.</li>
          </ul>
        </section>

        <section className="bg-zinc-50 border border-zinc-200 rounded-2xl p-6 space-y-2">
          <h2 className="text-xl font-bold text-black">Where to put business case numbers?</h2>
          <p className="text-zinc-700">
            Keep financial and ROI details in a dedicated Business Case page or executive PDF, not on the landing page.
            The landing page should stay product-focused: what it does, who it is for, and how it works.
          </p>
        </section>
      </div>
    </main>
  );
}

"use client";

import Link from "next/link";

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-white text-gray-900 px-6 py-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="space-y-2">
          <h1 className="text-4xl font-extrabold text-gray-900">VaultMind User Guide</h1>
          <p className="text-gray-600">
            Employee onboarding, role-based access, RAG upload workflow, and operations checklist.
          </p>
          <Link href="/" className="inline-block text-sm font-semibold text-blue-600 hover:text-blue-800 hover:underline">
            ← Back to Landing Page
          </Link>
        </header>

        <section className="bg-white border border-gray-200 rounded-2xl p-6 space-y-3 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-900">1) Access and Identity</h2>
          <p className="text-gray-600">Create employee accounts, assign department and role, then sign in.</p>
          <ul className="list-disc pl-5 text-gray-600 space-y-1">
            <li>`USER` accounts can query authorized knowledge.</li>
            <li>`ADMIN` accounts can manage upload and knowledge operations.</li>
            <li>JWT tokens carry role and department claims for authorization.</li>
          </ul>
        </section>

        <section className="bg-white border border-gray-200 rounded-2xl p-6 space-y-3 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-900">2) Document Upload and RAG</h2>
          <p className="text-gray-600">
            Upload company files, parse content, split into chunks, generate embeddings, and store in ChromaDB.
          </p>
          <ul className="list-disc pl-5 text-gray-600 space-y-1">
            <li>Parsing: PyMuPDF.</li>
            <li>Embedding model: `nomic-embed-text` for ingestion and retrieval consistency.</li>
            <li>Vector storage: ChromaDB.</li>
            <li>Generation model: local Llama model via Ollama.</li>
          </ul>
        </section>

        <section className="bg-white border border-gray-200 rounded-2xl p-6 space-y-3 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-900">3) Deployment and Monitoring</h2>
          <ul className="list-disc pl-5 text-gray-600 space-y-1">
            <li>Run backend services with Docker Compose.</li>
            <li>Check API health and model availability before user rollout.</li>
            <li>Track ingestion status, query latency, and retrieval quality.</li>
            <li>Review logs regularly for authentication and document access activity.</li>
          </ul>
        </section>

        <section className="bg-blue-50 border border-blue-100 rounded-2xl p-6 space-y-2 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900">Where to put business case numbers?</h2>
          <p className="text-gray-600">
            Keep financial and ROI details in a dedicated Business Case page or executive PDF, not on the landing page.
            The landing page should stay product-focused: what it does, who it is for, and how it works.
          </p>
        </section>
      </div>
    </main>
  );
}

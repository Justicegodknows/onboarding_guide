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
  );
}

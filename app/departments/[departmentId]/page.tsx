import { getDepartment, getDepartments } from "../../api/backend";
import DepartmentMenu from "../../components/DepartmentMenu";
import DepartmentWorkspace from "../../components/DepartmentWorkspace";

interface DepartmentPageProps {
    params: Promise<{ departmentId: string }>;
}

export default async function DepartmentPage({ params }: DepartmentPageProps) {
    const { departmentId } = await params;
    const [department, allDepartments] = await Promise.all([
        getDepartment(departmentId).catch(() => null),
        getDepartments().catch(() => []),
    ]);

    if (!department) {
        return (
            <div className="min-h-screen flex items-center justify-center p-8">
                <div className="rounded border bg-white dark:bg-zinc-900 p-6 max-w-md text-center">
                    <h1 className="text-2xl font-semibold mb-2">Department Not Found</h1>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                        The requested department workspace does not exist.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen bg-zinc-50 dark:bg-black font-sans">
            <DepartmentMenu departments={allDepartments} />
            <main className="flex flex-1 flex-col py-12 px-8 bg-white dark:bg-black">
                <DepartmentWorkspace
                    id={department.id}
                    name={department.name}
                    description={department.description}
                    info={department.info}
                />
            </main>
        </div>
    );
}

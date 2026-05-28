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
            <div className="min-h-screen flex items-center justify-center p-8 bg-white">
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 max-w-md text-center">
                    <h1 className="text-2xl font-semibold text-gray-900 mb-2">Department Not Found</h1>
                    <p className="text-sm text-gray-600">
                        The requested department workspace does not exist.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen bg-white font-sans">
            <DepartmentMenu departments={allDepartments} />
            <main className="flex flex-1 flex-col py-12 px-6 md:px-8 lg:px-10 bg-white">
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

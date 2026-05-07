export interface Department {
    id: string;
    name: string;
    description: string;
    info: string;
}

export const departments: Department[] = [
    {
        id: "hr",
        name: "Human Resources",
        description: "Employee relations, payroll, and benefits.",
        info: "Handles hiring, onboarding, and employee support.",
    },
    {
        id: "it",
        name: "IT Support",
        description: "Technical support and infrastructure.",
        info: "Manages company hardware, software, and troubleshooting.",
    },
    {
        id: "finance",
        name: "Finance",
        description: "Budgeting, payroll, and expenses.",
        info: "Responsible for company finances and reporting.",
    },
    {
        id: "marketing",
        name: "Marketing",
        description: "Branding and outreach.",
        info: "Promotes the company and manages campaigns.",
    },
    {
        id: "sales",
        name: "Sales",
        description: "Customer acquisition and retention.",
        info: "Handles client relationships and sales strategy.",
    },
];

import { getDepartments } from "./api/backend";
import HomeClient from "./components/HomeClient";

export default async function Home() {
    const departments = await getDepartments().catch(() => []);

    return <HomeClient departments={departments} />;
}

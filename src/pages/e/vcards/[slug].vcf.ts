import type { APIRoute } from "astro";
import employees from "../../../data/employees.json";
import { buildVCard } from "../../../lib/employees.js";

interface Emp {
  slug: string; name: string; title: string; org: string; email: string; phone: string;
}

export function getStaticPaths() {
  return (employees as Emp[]).map((emp) => ({ params: { slug: emp.slug }, props: { emp } }));
}

export const GET: APIRoute = ({ props }) => {
  const emp = props.emp as Emp;
  return new Response(buildVCard(emp), {
    headers: { "Content-Type": "text/vcard; charset=utf-8" },
  });
};

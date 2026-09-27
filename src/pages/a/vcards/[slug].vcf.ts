import type { APIRoute } from "astro";
import employees from "../../../../tenants/alawees/employees.json";
import { buildVCard } from "../../../lib/employees.js";
import type { Employee } from "../../../lib/tenant";

export function getStaticPaths() {
  return (employees as Employee[]).map((emp) => ({ params: { slug: emp.slug }, props: { emp } }));
}

export const GET: APIRoute = ({ props }) => {
  const emp = props.emp as Employee;
  return new Response(buildVCard(emp), {
    headers: { "Content-Type": "text/vcard; charset=utf-8" },
  });
};

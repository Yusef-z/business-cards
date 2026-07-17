import type { APIRoute } from "astro";
import associations from "../../data/associations.json";

interface Assoc {
  slug: string; name: string;
  phone?: string; email?: string; website?: string;
}

const esc = (s: string) => s.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n");

export function getStaticPaths() {
  return (associations as Assoc[]).map((assoc) => ({
    params: { slug: assoc.slug },
    props: { assoc },
  }));
}

export const GET: APIRoute = ({ props }) => {
  const a = props.assoc as Assoc;
  const lines = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    `N:${esc(a.name)};;;;`,
    `FN:${esc(a.name)}`,
    `ORG:${esc(a.name)}`,
  ];
  if (a.phone) lines.push(`TEL;TYPE=WORK,VOICE:${a.phone}`);
  if (a.email) lines.push(`EMAIL;TYPE=WORK:${a.email}`);
  if (a.website) lines.push(`URL:${a.website}`);
  lines.push("END:VCARD");
  return new Response(lines.join("\r\n") + "\r\n", {
    headers: { "Content-Type": "text/vcard; charset=utf-8" },
  });
};

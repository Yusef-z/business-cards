// Pure, dependency-free helpers shared by the data generator, the card
// components, and the vCard endpoint. Framework-agnostic so both Node scripts
// and Astro/Vite can import it, and so the logic stays unit-testable.

const HONORIFIC = /^(dr|mr|mrs|ms|eng|prof)\.?\s+/i;
const KNOWN_CC = /^\+(96[24])(\d+)$/; // Iraq (964) + Jordan (962)

export function stripHonorific(name) {
  return name.replace(HONORIFIC, "").trim();
}

export function slugify(name) {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function normalizePhone(raw) {
  const d = String(raw).trim().replace(/[\s()\-.]/g, "");
  if (d.startsWith("00")) return "+" + d.slice(2);
  return d; // already "+..." or an unexpected shape — leave it
}

export function formatPhoneDisplay(e164) {
  const m = e164.match(KNOWN_CC);
  if (!m) return e164;
  const [, cc, rest] = m;
  const groups = [];
  for (let i = 0; i < rest.length; ) {
    const size = rest.length - i === 4 ? 4 : 3; // let the tail absorb a 4th digit
    groups.push(rest.slice(i, i + size));
    i += size;
  }
  return `+${cc} ${groups.join(" ")}`;
}

export function initials(name) {
  const words = stripHonorific(name).split(/\s+/).filter(Boolean);
  if (words.length === 0) return "?";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

const esc = (s) =>
  String(s).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n");

export function buildVCard({ name, title, org, phone, email }) {
  const lines = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    `N:${esc(name)};;;;`,
    `FN:${esc(name)}`,
    `ORG:${esc(org)}`,
  ];
  if (title) lines.push(`TITLE:${esc(title)}`);
  if (phone) lines.push(`TEL;TYPE=WORK,VOICE:${phone}`);
  if (email) lines.push(`EMAIL;TYPE=WORK:${email}`);
  lines.push("END:VCARD");
  return lines.join("\r\n") + "\r\n";
}

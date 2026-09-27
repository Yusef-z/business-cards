import { describe, it, expect } from "vitest";
import { parseEmployeesCsv } from "./build-employees.mjs";

const WATANIA = { org: "Al Watania Holding Group", website: "https://www.alwatania-holding.com", location: "Baghdad" };
const ALAWEES = { org: "Al Awees Private Shareholding Company", website: "https://www.alawees-global.com", location: "Iraq, Baghdad" };

const SAMPLE = `Employee Name,Position,Email Account,Phone Number,
Talib Dagher Kadhum,Projecs Engineer,T.dagher@alwatania-holding.com,00964 7732988019,
KhloodOuda Al-Ameri,HR Director,k.Al-Ameri@alwatania-holding.com,00964 7800221313,
Dr. Osama Dawud,CEO,o.Dawud@alwatania-holding.com,00962 795144133,`;

describe("parseEmployeesCsv", () => {
  const rows = parseEmployeesCsv(SAMPLE, WATANIA);
  it("parses every data row", () => expect(rows).toHaveLength(3));
  it("fixes the 'Projecs' typo", () => expect(rows[0].title).toBe("Projects Engineer"));
  it("splits the merged 'KhloodOuda' name", () => expect(rows[1].name).toBe("Khlood Ouda Al-Ameri"));
  it("slugs without the honorific", () => expect(rows[2].slug).toBe("osama-dawud"));
  it("keeps the honorific in the display name", () => expect(rows[2].name).toBe("Dr. Osama Dawud"));
  it("normalizes the phone", () => expect(rows[0].phone).toBe("+9647732988019"));
  it("sets the tenant org and null photo", () => {
    expect(rows[0].org).toBe("Al Watania Holding Group");
    expect(rows[0].website).toBe("https://www.alwatania-holding.com");
    expect(rows[0].photo).toBeNull();
  });
  it("leaves phone2 empty when the column is blank", () => expect(rows[0].phone2).toBe(""));
});

describe("parseEmployeesCsv (alawees, two phones)", () => {
  const csv = `Employee Name,Position,Email Account,Phone Number,Phone Number 2
Safaa Shghaty Alazaidy,Authorized Manager,s.shghaty@alawees-global.com,+964 785 000 9005,+964 770 870 6220`;
  const [row] = parseEmployeesCsv(csv, ALAWEES);
  it("uses the alawees tenant constants", () => {
    expect(row.org).toBe("Al Awees Private Shareholding Company");
    expect(row.website).toBe("https://www.alawees-global.com");
    expect(row.location).toBe("Iraq, Baghdad");
  });
  it("slugs the name", () => expect(row.slug).toBe("safaa-shghaty-alazaidy"));
  it("normalizes both phones", () => {
    expect(row.phone).toBe("+9647850009005");
    expect(row.phone2).toBe("+9647708706220");
  });
});

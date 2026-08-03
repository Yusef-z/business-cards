import { describe, it, expect } from "vitest";
import { parseEmployeesCsv } from "./build-employees.mjs";

const SAMPLE = `Employee Name,Position,Email Account,Phone Number,
Talib Dagher Kadhum,Projecs Engineer,T.dagher@alwatania-holding.com,00964 7732988019,
KhloodOuda Al-Ameri,HR Director,k.Al-Ameri@alwatania-holding.com,00964 7800221313,
Dr. Osama Dawud,CEO,o.Dawud@alwatania-holding.com,00962 795144133,`;

describe("parseEmployeesCsv", () => {
  const rows = parseEmployeesCsv(SAMPLE);
  it("parses every data row", () => expect(rows).toHaveLength(3));
  it("fixes the 'Projecs' typo", () => expect(rows[0].title).toBe("Projects Engineer"));
  it("splits the merged 'KhloodOuda' name", () => expect(rows[1].name).toBe("Khlood Ouda Al-Ameri"));
  it("slugs without the honorific", () => expect(rows[2].slug).toBe("osama-dawud"));
  it("keeps the honorific in the display name", () => expect(rows[2].name).toBe("Dr. Osama Dawud"));
  it("normalizes the phone", () => expect(rows[0].phone).toBe("+9647732988019"));
  it("sets the constant org and null photo", () => {
    expect(rows[0].org).toBe("Al Watania Holding Group");
    expect(rows[0].photo).toBeNull();
  });
});

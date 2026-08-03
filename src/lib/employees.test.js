import { describe, it, expect } from "vitest";
import {
  slugify, stripHonorific, normalizePhone,
  formatPhoneDisplay, initials, buildVCard,
} from "./employees.js";

describe("slugify", () => {
  it("kebab-cases a full name", () => expect(slugify("Hussein Alaa Ali")).toBe("hussein-alaa-ali"));
  it("handles hyphenated surnames", () => expect(slugify("Khlood Ouda Al-Ameri")).toBe("khlood-ouda-al-ameri"));
});

describe("stripHonorific", () => {
  it("drops a leading Dr.", () => expect(stripHonorific("Dr. Osama Dawud")).toBe("Osama Dawud"));
  it("leaves plain names", () => expect(stripHonorific("Maher Zahran")).toBe("Maher Zahran"));
});

describe("normalizePhone", () => {
  it("converts 00 prefix and strips spaces", () => expect(normalizePhone(" 00964 7717458968")).toBe("+9647717458968"));
  it("keeps an existing + number", () => expect(normalizePhone("+962795144133")).toBe("+962795144133"));
});

describe("formatPhoneDisplay", () => {
  it("groups Iraqi numbers 3-3-4", () => expect(formatPhoneDisplay("+9647717458968")).toBe("+964 771 745 8968"));
  it("groups Jordanian numbers", () => expect(formatPhoneDisplay("+962795144133")).toBe("+962 795 144 133"));
  it("returns unknown shapes unchanged", () => expect(formatPhoneDisplay("+15551234")).toBe("+15551234"));
});

describe("initials", () => {
  it("uses the first two words", () => expect(initials("Hussein Alaa Ali")).toBe("HA"));
  it("drops the honorific first", () => expect(initials("Dr. Osama Dawud")).toBe("OD"));
});

describe("buildVCard", () => {
  const v = buildVCard({
    name: "Hussein Alaa Ali", title: "IT PMO – Group Level",
    org: "Al Watania Holding Group", phone: "+9647717458968", email: "h.alaa@x.com",
    website: "https://www.alwatania-holding.com", location: "Baghdad, Baghdad Governorate Iraq",
  });
  it("has the full name", () => expect(v).toContain("FN:Hussein Alaa Ali"));
  it("has the title", () => expect(v).toContain("TITLE:IT PMO – Group Level"));
  it("has a work phone", () => expect(v).toContain("TEL;TYPE=WORK,VOICE:+9647717458968"));
  it("has a work email", () => expect(v).toContain("EMAIL;TYPE=WORK:h.alaa@x.com"));
  it("has the website URL", () => expect(v).toContain("URL:https://www.alwatania-holding.com"));
  it("has the work address", () => expect(v).toContain("ADR;TYPE=WORK:;;Baghdad\\, Baghdad Governorate Iraq;;;;"));
  it("uses CRLF and ends with END", () => expect(v.endsWith("END:VCARD\r\n")).toBe(true));
});

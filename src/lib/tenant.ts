// Shape of tenants/<id>/tenant.json. A tenant is data + identity; the card
// look comes from src/designs/<tenant.design>/.
export interface Tenant {
  id: string;
  design: string;
  prefix: string;          // URL prefix, e.g. "/e" → /e/<slug>, /e, /e/vcards/<slug>.vcf
  org: string;
  lockup?: string[];       // text lines under the header logo (omit when the logo image carries them)
  website: string;
  location: string;
  assets: string;          // public folder: logo.png, logo-white.png, banner-bg.png, og/
  team: string;            // public folder for cropped headshots
  directoryLogo: string;
  ring?: string;           // avatar frame PNG; omitted → CSS gradient ring
  artTop?: number;         // banner-bg.png is the whole card artwork (header + bottom
                           // halves); this fraction of its height is the header part.
                           // Omitted → banner-bg.png covers the header only and the
                           // bottom section is the CSS gradient.
  logoHeight: number;      // header logo height in px on the 430px card
  qrLogo: string;
  qrOut: string;
  colors: { name: string; title: string; placeholder: string; page: string; theme: string };
}

export interface Employee {
  slug: string; name: string; title: string; org: string;
  email: string; phone: string; phone2: string; website: string; location: string;
  photo: string | null;
}

# Digital Business Cards — نتاج

**Register:** brand

## What this is

A static site of digital business cards for 22 Saudi industrial-sector associations
(جمعيات) organized under the Ministry of Industry & Mineral Resources' "نتاج" (Nataj)
initiative. Each association has a card at a readable slug (e.g. `/wim`). A visitor
lands on one card — the card *is* the product; the visitor's impression is the thing
being made.

## Audience & context

Someone who scanned a printed QR code or tapped a shared link — an association member,
a partner, a journalist, a government counterpart. They open it on a phone, in daylight,
to get one thing: a way to reach or save the association. The card must read as
**official and credible** first, memorable second. These are government-affiliated
bodies; a cheap or generic card undermines their standing.

## Voice (three physical-object words)

Official · precise · quietly premium — like a metal credential card, not a flyer.

## Brand identity (already committed — preserve)

- **Color:** the Nataj deck's deep indigo-purple. Body `#2e2350`, gradient partner
  `#3a2d63`, action accent `#5b3fbf`. Committed strategy: purple carries the surface;
  white is the detail zone. Any second accent stays a hairline, used once.
- **Type:** IBM Plex Sans Arabic (deliberately kept — it is one of the best-drawn Arabic
  sans faces and reads as credible/official; identity-preservation over novelty).
- **Logos:** each association's official icon + bilingual-name lockup, white artwork on
  the deck purple, cropped from the source deck. The lockup carries the name.

## Content per card

Logo lockup, a "save contact" (vCard) primary action, and the association's real
contact data — phone, email, website shown as icon + value; LinkedIn / X as icon-only.
Only fields that exist render (no empty rows). Arabic, RTL, mobile-first.

## Non-negotiables

- Arabic RTL on every page; contact values (phone/email/URL) render LTR in place.
- Static output, no runtime JS required to view a card (one inline `onerror` logo
  fallback is the only script).
- Slugs are immutable (printed in QR codes).
- Accessible: ≥4.5:1 body contrast, focus-visible states, reduced-motion honored.

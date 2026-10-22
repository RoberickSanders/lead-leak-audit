# Market teardown method (speed-to-lead)

How to size up 10 local businesses in one vertical (e.g. med spas in one metro) in about an hour, and pick the 3 best-fit prospects for a speed-to-lead offer. Every claim in the table must be sourced or marked **unknown**; nothing is submitted and no one is contacted during research.

## 1. Build the list (10)
- Pull the top-rated businesses in the area from public directories and map listings.
- Record rating and review count with the source and date. Ranges are fine when sources disagree.

## 2. Check each site (read-only)
For each site, fetch the page and look for:
| Signal | How to detect |
|---|---|
| Self-booking | Booking platform scripts/links (Boulevard, Zenoti, Vagaro, Calendly, etc.) |
| Lead capture | `<form>` fields, popup scripts, chat widgets (Intercom, Podium, LeadConnector, Tidio...) |
| Ads running | Meta Pixel / Google Ads tags on the page; ad library when accessible |
| Offer | Specials, memberships, entry-price services on the page |
| After-hours gap | Posted hours vs. phone/form-only CTAs |
Run `audit.py` for the measurable mobile checks (phone position, tap-to-call, CTA position, form length, chat, load time).

## 3. Fill the teardown table
| # | Business | Area | Rating (reviews) | Ads / offer | Booking | Lead capture | Speed-to-lead gaps |
|---|---|---|---|---|---|---|---|
| 1 | Sample Glow Med Spa | Exampleville | 4.9 (900+) | unknown; VIP memberships | phone-led "schedule a consult" | unknown | Consult/phone CTA, no instant booking |
| 2 | Demo Aesthetics | Exampleville | 5.0 (170) | Meta Pixel installed | none found; "call or text to schedule" | form + popup | No instant booking; auto-reply unknown |
| 3 | Placeholder Skin Studio | North Example | 4.9 (240) | promos page | full online booking | chat widget | Low: already instant |

## 4. Analyze
- **Why leaders win:** review volume, physician-led trust, memberships, real-time self-booking, long hours.
- **Common gaps:** consult-request forms with no visible instant reply, call/text-only scheduling, booking deposits, limited hours, no chat/AI responder.

## 5. Pick the top 3
Best fit = **high rating, mid volume, ads already running, but leads routed through a form or phone.** Write a one-line pitch per prospect that names the specific gap you observed, e.g.:
> "Your ad clicks land on a call-or-text CTA. Let's turn them into booked consults within 60 seconds, 24/7."

## 6. Method notes to always include
- Which tools were used and which couldn't be (e.g. ad library needed a login, so ads = unknown).
- Data dates and sources.
- "Nothing was submitted and no one was contacted."

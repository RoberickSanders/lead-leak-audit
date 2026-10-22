# Lead Leak Audit: Sample Comfort HVAC

- **Trade:** HVAC
- **URL audited:** http://127.0.0.1:8765/
- **Size hint (public):** ~200 reviews (fictional)
- **Score:** 38/100
- **Audit date:** 2026-01-15

## Findings (mobile, 390x844)
| Check | Result |
|---|---|
| First visible phone number | screen 3 |
| First tap-to-call (tel:) link | screen none found |
| Phone in header | no |
| First booking/quote button or form | screen 3 ("Request service") |
| Form on page | yes, 8 fields, screen 3 |
| Chat/text widget | none detected |
| Page load (full load event) | 0.02s |
| Page length | 3.0 screens |

Desktop (1366x768): phone on screen 3, booking/quote on screen 3, load 0.02s.

## Top fixable leaks
1. On a phone, the number doesn't show up until screen 3. Most people leave before scrolling that far.
2. The phone number can't be tapped to call on mobile, so callers have to copy it by hand.
3. The first booking/quote button or form doesn't appear until screen 3.

## Screenshot
Full-page mobile: `screenshots/sample-comfort-mobile.png`

## Opener (DRAFT, not sent)
> Hi, I ran a quick mobile check on your hvac page (http://127.0.0.1:8765/) and noticed one thing that's likely costing you calls: on a phone, the number doesn't show up until screen 3. Most people leave before scrolling that far. Overall it scored 38/100, and the fix is small, so I'm happy to send you the full audit. I also help local service companies text back every missed call and web lead within seconds, if that's ever useful.

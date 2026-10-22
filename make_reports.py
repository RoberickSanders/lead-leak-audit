#!/usr/bin/env python3
"""Turn raw audit JSON into one markdown report per business + a ranked summary.csv.
   python make_reports.py --dir examples --region "Exampleville" --date 2026-01-15
Expects <dir>/targets.tsv (slug, company, trade, url, size hint) and <dir>/raw/<slug>.json from audit.py.
Openers are DRAFTS for a human to review; this script never sends anything."""
import argparse, csv, json, os

ap = argparse.ArgumentParser(); ap.add_argument('--dir', default='.'); ap.add_argument('--region', default='your area')
ap.add_argument('--date', required=True); a = ap.parse_args(); B = a.dir
os.makedirs(f'{B}/reports', exist_ok=True); rows = []
fx = {True: 'yes', False: 'no'}
for line in open(f'{B}/targets.tsv'):
    n, c, t, u, h = line.rstrip('\n').split('\t'); p = f'{B}/raw/{n}.json'
    if not os.path.exists(p): continue
    d = json.load(open(p))
    if 'error' in d: print('SKIP', n, d['error']); continue
    m, k = d['mobile'], d['desktop']
    leaks = d['top_leaks'] or ["No major leaks found; the main remaining gap is what happens after the lead comes in (how fast someone texts or calls back)."]
    first = leaks[0].rstrip('.')
    if d['top_leaks']:
        opener = (f"Hi, I ran a quick mobile check on your {t.lower()} page ({u}) and noticed one thing that's likely costing you calls: "
                  f"{first[0].lower() + first[1:]}. Overall it scored {d['score']}/100, and the fix is small, so I'm happy to send you the full audit. "
                  f"I also help local service companies text back every missed call and web lead within seconds, if that's ever useful.")
    else:
        opener = (f"Hi, I ran a quick mobile check on your {t.lower()} page ({u}) and it's one of the cleanest I've seen in {a.region}, scoring {d['score']}/100. "
                  f"The one gap I can't see from the outside is how fast new web leads and missed calls get a response. "
                  f"I'd be glad to test your response time for free.")
    md = f"""# Lead Leak Audit: {c}

- **Trade:** {t}
- **URL audited:** {u}
- **Size hint (public):** {h}
- **Score:** {d['score']}/100
- **Audit date:** {a.date}

## Findings (mobile, 390x844)
| Check | Result |
|---|---|
| First visible phone number | screen {m['phone_screen'] or 'not found'} |
| First tap-to-call (tel:) link | screen {m['click_to_call_screen'] or 'none found'} |
| Phone in header | {fx[m['phone_in_header']]} |
| First booking/quote button or form | screen {m['cta_or_form_screen'] or 'none found'} {('("' + m['first_cta_text'][0] + '")') if m['first_cta_text'] else ''} |
| Form on page | {fx[m['form_present']]}{f", {m['form_fields']} fields, screen {m['form_screen']}" if m['form_present'] else ''} |
| Chat/text widget | {', '.join(m['chat_signals']) or 'none detected'} |
| Page load (full load event) | {m['load_s']}s |
| Page length | {m['page_screens']} screens |

Desktop (1366x768): phone on screen {k.get('phone_screen') or 'not found'}, booking/quote on screen {k.get('cta_or_form_screen') or 'not found'}, load {k.get('load_s')}s.

## Top fixable leaks
""" + '\n'.join(f"{i + 1}. {l}" for i, l in enumerate(leaks)) + f"""

## Screenshot
Full-page mobile: `{d['screenshot']}`

## Opener (DRAFT, not sent)
> {opener}
"""
    open(f'{B}/reports/{n}.md', 'w').write(md)
    rows.append(dict(company=c, trade=t, url=u, score=d['score'], severity=100 - d['score'], phone_screen=m['phone_screen'],
                     tap_to_call_screen=m['click_to_call_screen'], cta_screen=m['cta_or_form_screen'], form_fields=m['form_fields'],
                     chat=';'.join(m['chat_signals']), phone_in_header=m['phone_in_header'], load_s=m['load_s'],
                     biggest_leak=leaks[0], report=f'reports/{n}.md'))
rows.sort(key=lambda r: -r['severity'])
if rows:
    with open(f'{B}/reports/summary.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['rank'] + list(rows[0])); w.writeheader()
        for i, r in enumerate(rows): w.writerow({'rank': i + 1, **r})
for i, r in enumerate(rows): print(i + 1, r['company'], r['score'], '|', r['biggest_leak'])

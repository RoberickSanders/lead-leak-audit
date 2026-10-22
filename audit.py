#!/usr/bin/env python3
"""Lead Leak Audit: measures how fast a visitor can call/book on a landing page.
Usage: python audit.py URL [--name slug] [--out dir]
Read-only: never clicks, submits forms, or calls anything."""
import sys, json, time, re, argparse, os
from playwright.sync_api import sync_playwright

JS = r"""
() => {
 const vh = window.innerHeight, sy = window.scrollY;
 const vis = e => { const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
   return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none' && parseFloat(s.opacity)>0.05; };
 const top = e => e.getBoundingClientRect().top + sy;
 const fixed = e => { for(let n=e;n&&n!==document.body;n=n.parentElement){const p=getComputedStyle(n).position; if(p==='fixed'||p==='sticky') return true;} return false; };
 const phoneRe = /(\+?1[\s.-]?)?\(?\b[2-9]\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/;
 let tel = [...document.querySelectorAll('a[href^="tel:"]')].filter(vis);
 let telTop = tel.length ? Math.min(...tel.map(e=>fixed(e)?0:top(e))) : null;
 // visible text phone
 let txtTop = null, walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
 while(walker.nextNode()){ const t=walker.currentNode; if(phoneRe.test(t.textContent) && t.parentElement && vis(t.parentElement)){
   const y = fixed(t.parentElement)?0:top(t.parentElement); if(txtTop===null||y<txtTop) txtTop=y; } }
 const ctaRe = /\b(book|schedule|get (a |your )?(free )?(quote|estimate)|request (service|a quote|estimate|appointment)|free (estimate|quote|inspection)|appointment|get started)/i;
 let ctas = [...document.querySelectorAll('a,button,input[type=submit]')].filter(e=>vis(e) && ctaRe.test((e.innerText||e.value||e.getAttribute('aria-label')||'').trim()));
 let ctaTop = ctas.length ? Math.min(...ctas.map(e=>fixed(e)?0:top(e))) : null;
 let forms = [...document.querySelectorAll('form')].filter(vis).map(f=>({top: fixed(f)?0:top(f),
   fields:[...f.querySelectorAll('input,select,textarea')].filter(i=>!['hidden','submit','button'].includes(i.type)&&vis(i)).length})).filter(f=>f.fields>0);
 // iframes forms (embedded schedulers)
 let ifr = [...document.querySelectorAll('iframe')].filter(vis).map(f=>f.src||'');
  const chatSigs = {'Intercom':'widget.intercom.io','Drift':'js.driftt.com','Tawk':'embed.tawk.to','LiveChat':'livechatinc.com','Podium':'podium.com','Birdeye':'birdeye.com','HubSpot chat':'usemessages.com','Zendesk':'zdassets.com','Crisp':'client.crisp.chat','Tidio':'code.tidio.co','LeadConnector/GHL chat':'leadconnectorhq.com','Smartsupp':'smartsupp','Kenect':'kenect','Broadly':'broadly.com','NiceJob':'nicejob','Signpost':'signpost','LivePerson':'lpsnmedia','Olark':'olark.com','Facebook chat':'connect.facebook.net/en_us/sdk/xfbml.customerchat','Scorpion chat':'scorpion.co','Hatch':'usehatchapp','Chatra':'chatra.io','Jivo':'jivosite','Freshchat':'freshchat','Userlike':'userlike','Housecall Pro':'housecallpro.com','ServiceTitan scheduler':'scheduler.servicetitan','Calendly':'calendly.com'};
 const srcs = [...document.querySelectorAll('script[src],iframe[src],link[href]')].map(e=>(e.src||e.href||'').toLowerCase()).join(' ') + ' ' + [...document.querySelectorAll('script:not([src])')].map(e=>e.textContent.slice(0,20000).toLowerCase()).join(' ');
 const found = Object.entries(chatSigs).filter(([k,v])=>srcs.includes(v)).map(([k])=>k);
 const chat = found.filter(k=>!['Housecall Pro','ServiceTitan scheduler','Calendly'].includes(k));
 const schedulers = found.filter(k=>['Housecall Pro','ServiceTitan scheduler','Calendly'].includes(k));
 const header = document.querySelector('header') || [...document.querySelectorAll('div,nav')].find(e=>vis(e)&&top(e)<150&&e.getBoundingClientRect().height>40);
 let phoneInHeader=false; if(header){ phoneInHeader = !!header.querySelector('a[href^="tel:"]') || phoneRe.test(header.innerText||''); }
 const sched = schedulers;
 return {vh, pageHeight: document.documentElement.scrollHeight, telCount: tel.length, telTop, txtTop, ctaTop,
   ctaText: ctas.slice(0,3).map(e=>(e.innerText||e.value||'').trim().slice(0,40)), forms, chat, phoneInHeader, onlineSchedulerHint: sched,
   iframes: ifr.slice(0,10), title: document.title};
}
"""

def screen(y, vh): return None if y is None else int(y // vh) + 1

def measure(pw, url, mobile, shot=None):
    b = pw.chromium.launch(headless=True)
    kw = dict(viewport={'width':390,'height':844}, device_scale_factor=2, is_mobile=True, has_touch=True,
              user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1') if mobile \
         else dict(viewport={'width':1366,'height':768})
    ctx = b.new_context(**kw); p = ctx.new_page()
    t0 = time.time(); err=None
    try:
        p.goto(url, wait_until='domcontentloaded', timeout=45000); dcl = time.time()-t0
        try: p.wait_for_load_state('load', timeout=30000)
        except Exception: pass
        load = time.time()-t0
        for _ in range(8):  # wait out bot-check interstitials (no bypass)
            if re.search(r'checking your browser|just a moment|attention required', p.title() or '', re.I): p.wait_for_timeout(2000)
            else: break
        p.wait_for_timeout(3000)  # let chat widgets / lazy JS load
        # scroll to trigger lazy content, then back
        h = p.evaluate('document.documentElement.scrollHeight')
        for y in range(0, min(h, 40000), 800): p.evaluate(f'window.scrollTo(0,{y})'); p.wait_for_timeout(60)
        p.evaluate('window.scrollTo(0,0)'); p.wait_for_timeout(800)
        d = p.evaluate(JS); d.update(domContentLoaded_s=round(dcl,2), load_s=round(load,2), finalUrl=p.url)
        if shot:
            try: p.screenshot(path=shot, full_page=True, timeout=60000)
            except Exception as e: d['screenshotError']=str(e)[:200]
    except Exception as e:
        err=str(e)[:300]; d={'error':err}
    b.close(); return d

def summarize(d):
    vh=d['vh']; tops=[x for x in (d['telTop'],d['txtTop']) if x is not None]
    forms=d['forms']; ff=min(forms,key=lambda f:f['top']) if forms else None
    book=[x for x in (d['ctaTop'], ff['top'] if ff else None) if x is not None]
    return {'phone_screen': screen(min(tops),vh) if tops else None,
            'click_to_call_screen': screen(d['telTop'],vh), 'click_to_call': d['telCount']>0,
            'cta_or_form_screen': screen(min(book),vh) if book else None, 'first_cta_text': d['ctaText'][:1],
            'form_present': bool(forms), 'form_fields': ff['fields'] if ff else 0, 'form_screen': screen(ff['top'],vh) if ff else None,
            'chat_widget': bool(d['chat']), 'chat_signals': d['chat'], 'phone_in_header': d['phoneInHeader'],
            'load_s': d['load_s'], 'page_screens': round(d['pageHeight']/vh,1)}

def score(m, dk):
    s=100; leaks=[]
    def leak(pts, txt): nonlocal s; s-=pts; leaks.append((pts,txt))
    ps=m['phone_screen']
    if ps is None: leak(30,"Mobile visitors can't find a phone number anywhere on the page.")
    elif ps>1: leak(min(30,8+3*ps), f"On a phone, the number doesn't show up until screen {ps}. Most people leave before scrolling that far.")
    if not m['click_to_call']: leak(15,"The phone number can't be tapped to call on mobile, so callers have to copy it by hand.")
    elif (m['click_to_call_screen'] or 99)>1 and (ps or 99)<=1: leak(5,f"The number is on the first screen but the tap-to-call link only appears on screen {m['click_to_call_screen']}.")
    if not m['phone_in_header']: leak(8,"The phone number isn't in the header, where people look first.")
    cs=m['cta_or_form_screen']
    if cs is None: leak(15,"There's no clear 'Book' or 'Get a Quote' button, so people who won't call have no next step.")
    elif cs>1: leak(min(15,3+2*cs), f"The first booking/quote button or form doesn't appear until screen {cs}.")
    if m['form_present'] and m['form_fields']>6: leak(6,f"The quote form asks for {m['form_fields']} fields; every extra field loses leads.")
    if not m['chat_widget']: leak(7,"There's no chat or text widget, so after-hours visitors can't reach anyone instantly.")
    if m['load_s']>6: leak(min(15,int(m['load_s'])), f"The page takes {m['load_s']:.1f}s to fully load on mobile; many visitors bounce after 3s.")
    elif m['load_s']>3: leak(4,f"The page takes {m['load_s']:.1f}s to load on mobile.")
    if dk and dk.get('phone_screen') not in (1,None) and False: pass
    leaks.sort(key=lambda x:-x[0])
    return max(0,s), [t for _,t in leaks[:3]]

def audit(url, name=None, out='.'):
    name = name or re.sub(r'\W+','-',re.sub(r'^https?://(www\.)?','',url)).strip('-')[:50]
    os.makedirs(os.path.join(out,'screenshots'), exist_ok=True)
    shot=os.path.join(out,'screenshots',f'{name}-mobile.png')
    with sync_playwright() as pw:
        mr=measure(pw,url,True,shot); dr=measure(pw,url,False)
    if 'error' in mr: return {'url':url,'error':mr['error']}
    if re.search(r'clickcease=block|checking your browser|just a moment|access denied',(mr['finalUrl']+' '+mr['title']),re.I):
        return {'url':url,'error':'blocked by site bot-protection; not scored','final_url':mr['finalUrl'],'title':mr['title']}
    m=summarize(mr); dk=summarize(dr) if 'error' not in dr else {'error':dr['error']}
    sc,leaks=score(m,dk)
    return {'url':url,'final_url':mr['finalUrl'],'title':mr['title'],'mobile':m,'desktop':dk,'score':sc,'top_leaks':leaks,
            'screenshot':os.path.relpath(shot,out),'raw_mobile':mr}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('--name'); ap.add_argument('--out',default='.')
    a=ap.parse_args(); print(json.dumps(audit(a.url,a.name,a.out),indent=2))

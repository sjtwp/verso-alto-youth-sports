#!/usr/bin/env python3
"""Static site builder for Verso Alto Youth Sports.
Every page is written to <route>/index.html so URLs look like  domain.com/sports/soccer/
All internal links are written as relative paths, so the site works both on
GitHub Pages (sjtwp.github.io/verso-alto-youth-sports/) and on the real domain."""
import os, re, json, html, shutil, datetime, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SINGLE = '--single' in sys.argv   # one index.html with #hash routes (use until the domain is connected)
OUT = ARGS[0] if ARGS else os.path.join(ROOT, 'dist')
SITE = 'https://www.versoaltoyouthsports.com'   # canonical domain (used by separate-pages mode)
PREVIEW_URL = 'https://sjtwp.github.io/verso-alto-youth-sports'  # where the one-file site lives until the domain is connected
FORM = 'https://docs.google.com/forms/d/1PZcpAY_OP1VVB4GeXCgl2Py-XU9SOIxdt931PGv9zgM/viewform'
sys.path.insert(0, SRC)
from cities import REGIONS
from articles1 import ARTICLES as A1
from articles2 import ARTICLES as A2
ARTICLES = sorted(A1 + A2, key=lambda a: a['date'], reverse=True)
CITIES = [dict(c, region=rid, region_name=rname) for rid, rname, _, cs in REGIONS for c in cs]
CITY_SLUGS = {re.sub(r'[^a-z0-9]+', '-', c['name'].lower()).strip('-') for c in CITIES}

def rd(n): return open(os.path.join(SRC, n), encoding='utf-8').read()
def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

ROUTES = {
 'home': '/', 'sports': '/sports/', 'soccer': '/sports/soccer/', 'baseball': '/sports/baseball/',
 'basketball': '/sports/basketball/', 'football': '/sports/football/', 'about': '/about/',
 'service-area': '/service-area/', 'blog': '/blog/', 'faq': '/faq/', 'policies': '/policies/',
 'privacy': '/policies/privacy/', 'refund': '/policies/refund/', 'waiver': '/policies/waiver/',
 'concussion': '/policies/concussion/', 'child-protection': '/policies/child-protection/',
 'support': '/support/', 'contact': '/contact/',
}
POL = json.loads(rd('policies.json'))
STRIPE = dict(
 once='https://donate.stripe.com/9B69ATgpV8Vx0FYeTD4AU00',
 friends='https://donate.stripe.com/14A5kD0qX0p188q4eZ4AU01',
 family='https://buy.stripe.com/5kQ5kD6PlfjV2O69zj4AU02',
 partner='https://buy.stripe.com/14A5kD7Tpc7Jagy9zj4AU03')

# ---------------------------------------------------------------- helpers
def rel(frm, to):
    """relative URL from page dir `frm` to site path `to` (may include ?query / #hash)."""
    m = re.match(r'([^?#]*)(.*)', to); path, tail = m.group(1), m.group(2)
    r = os.path.relpath(path or '/', frm)
    r = './' if r == '.' else r + '/'
    if path.endswith('.xml') or path.endswith('.txt') or path.endswith('.css') or path.endswith('.js'):
        r = r.rstrip('/')
    return r + tail

def city_links(h):
    return re.sub(r'@/service-area/#([a-z0-9-]+)', lambda m: f'@/service-area/{m.group(1)}/' if m.group(1) in CITY_SLUGS else m.group(0), h)

def resolve(htmltext, frm):
    htmltext = city_links(htmltext)
    return re.sub(r'(href|src)="@(/[^"]*)"', lambda m: f'{m.group(1)}="{rel(frm, m.group(2))}"', htmltext)

def conv_hash_links(h):
    """convert old single-page  <a href="#key" data-link [data-topic=X]>  to  @/route/"""
    def fix(m):
        tag = m.group(0)
        if 'data-link' not in tag: return tag
        key = re.search(r'href="#([a-z-]+)"', tag)
        topic = re.search(r'data-topic="([^"]+)"', tag)
        if key:
            dest = ROUTES[key.group(1)]
            if topic: dest += '?topic=' + topic.group(1)
            tag = tag.replace(key.group(0), f'href="@{dest}"')
        tag = re.sub(r'\s*data-link', '', tag); tag = re.sub(r'\s*data-topic="[^"]*"', '', tag)
        return tag
    return re.sub(r'<a\b[^>]*>', fix, h)

def sec(name): return conv_hash_links(rd(f'sec_{name}.html'))
def esc(s): return html.escape(s, quote=True)
def fmt_date(d): return datetime.date.fromisoformat(d).strftime('%B %-d, %Y')
ARROW = '<svg><use href="#arrow"/></svg>'
CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>'

SPORTS = [
 dict(key='soccer', name='Soccer', icon='ball', status='Spring 2027', live=True, desc='Co-ed recreational soccer for ages 3–8 in the East Valley. Six weeks of Saturday-morning fun. No tryouts.'),
 dict(key='baseball', name='Baseball', icon='baseball', status='Coming soon', desc='Hitting, throwing, catching, and running the bases — with faith and fun at the core.'),
 dict(key='basketball', name='Basketball', icon='basketball', status='Coming soon', desc='Dribbling, passing, shooting, and teamwork on the court. Details to be announced.'),
 dict(key='football', name='Football', icon='football', status='Coming soon', desc='Throwing, catching, running routes, and playing as a team. Details to be announced.'),
]
def sport_cards():
    return ''.join(f'''<a class="sport {s['key']} reveal" style="transition-delay:{i*.1:.1f}s" href="@{ROUTES[s['key']]}">
    <svg class="art" viewBox="0 0 100 100" aria-hidden="true"><use href="#{s['icon']}"/></svg>
    <span class="status {'live' if s.get('live') else ''}">{'● ' if s.get('live') else ''}{s['status']}</span>
    <h3>{s['name']}</h3><p>{s['desc']}</p>
    <span class="go">{'See the details' if s.get('live') else 'Learn more'} {ARROW}</span></a>''' for i, s in enumerate(SPORTS))

TAG_ICON = {'News': 'logo', 'Faith': 'logo', 'Safety': 'ball', 'Soccer': 'ball', 'Families': 'ball', 'Sports': 'football', 'Community': 'basketball'}
def post_card(a, i=0):
    ic = TAG_ICON.get(a['tag'], 'ball')
    vb = '0 0 302 216' if ic == 'logo' else '0 0 100 100'
    return f'''<a class="post-card reveal" style="transition-delay:{(i%3)*.08:.2f}s" data-tag="{a['tag']}" href="@/blog/{a['slug']}/">
  <div class="post-art t-{a['tag']}"><svg class="big" viewBox="{vb}" aria-hidden="true"><use href="#{ic}"/></svg><span class="tagpill">{a['tag']}</span></div>
  <div class="post-body"><time datetime="{a['date']}">{fmt_date(a['date'])}</time><h3>{esc(a['title'])}</h3><p>{esc(a['desc'])}</p><span class="more">Read article →</span></div></a>'''

def phero(eyebrow, title_html, lead, crumbs=None, extra='', bg=None, orb='var(--gold)'):
    c = ''
    if crumbs:
        parts = []
        for label, href in crumbs:
            parts.append(f'<a href="@{href}">{label}</a>' if href else f'<span>{label}</span>')
        c = '<nav class="crumbs" aria-label="Breadcrumb">' + '<span class="sep">/</span>'.join(parts) + '</nav>'
    style = f' style="background:{bg}"' if bg else ''
    return f'''<section class="phero"{style}>
    <div class="orb" style="width:400px;height:400px;background:{orb};right:-100px;top:60px"></div>
    <div class="wrap" style="position:relative">{c}
      <span class="eyebrow">{eyebrow}</span>
      <h1 class="display">{title_html}</h1>
      {f'<p>{lead}</p>' if lead else ''}{extra}
    </div>
  </section>'''

# ---------------------------------------------------------------- chrome
def nav(section, current):
    def t(key, label):
        return f'<a href="@{ROUTES[key]}" data-tab class="{"active" if section == key else ""}">{label}</a>'
    def dd(key, label, items):
        return f'<div class="dd">{t(key, label)}<div class="dd-menu">{items}</div></div>'
    sport_items = ''.join(f'<a href="@{ROUTES[s["key"]]}"><svg><use href="#{s["icon"]}"/></svg><span>{s["name"]}<small class="{"live" if s.get("live") else ""}">{s["status"]}</small></span></a>' for s in SPORTS) + f'<hr/><a class="plain" href="@/sports/">All sports →</a>'
    about_items = f'<a class="plain" href="@/about/">About us</a><a class="plain" href="@/service-area/">Service area</a><a class="plain" href="@/blog/">Blog</a>'
    faq_items = f'<a class="plain" href="@/faq/">FAQ</a><a class="plain" href="@/policies/">Policies &amp; Forms</a><a class="plain" href="@/policies/privacy/">Privacy Policy</a><a class="plain" href="@/policies/refund/">Refund Policy</a>'
    sup_items = f'<a class="plain" href="@/support/#give-once">One-time gift</a><a class="plain" href="@/support/#monthly">Monthly giving</a><a class="plain" href="@/support/#sponsors">Sponsors</a><a class="plain" href="@/support/#other-ways">Other ways to help</a>'
    desktop = f'''<nav class="tabs" id="tabs" aria-label="Main"><span class="pill"></span>
      {t('home','Home')}{dd('sports','Sports',sport_items)}{dd('about','About',about_items)}{t('blog','Blog')}{dd('faq','FAQ',faq_items)}{dd('support','Support',sup_items)}{t('contact','Contact')}
    </nav>'''
    def mi(key, label):
        return f'<div class="mm-item"><a href="@{ROUTES[key]}" class="{"active" if section == key else ""}">{label}</a></div>'
    def mg(key, label, links):
        sub = ''.join(f'<a href="@{href}" class="{"active" if href == current else ""}">{inner}</a>' for href, inner in links)
        cur = ' current' if section == key else ''
        return f'''<div class="mm-group{cur}"><div class="mm-row"><a href="@{ROUTES[key]}">{label}</a><button class="mm-toggle" aria-expanded="false" aria-label="Show {label} pages">{CHEV}</button></div>
      <div class="mm-sub"><div>{sub}</div></div></div>'''
    sports_links = [('/sports/', '<span>All sports</span>')] + [(ROUTES[s['key']], f'<svg><use href="#{s["icon"]}"/></svg><span>{s["name"]}</span><small class="{"live" if s.get("live") else ""}">{s["status"]}</small>') for s in SPORTS]
    mobile = f'''<nav id="mobileMenu" aria-label="Mobile">
  {mi('home','Home')}
  {mg('sports','Sports',sports_links)}
  {mg('about','About',[('/about/','About us'),('/service-area/','Service area'),('/blog/','Blog')])}
  {mi('blog','Blog')}
  {mg('faq','FAQ',[('/faq/','FAQ'),('/policies/','Policies &amp; Forms'),('/policies/privacy/','Privacy Policy'),('/policies/refund/','Refund Policy')])}
  {mg('support','Support',[('/support/','Ways to give'),('/support/#give-once','One-time gift'),('/support/#monthly','Monthly giving'),('/support/#sponsors','Sponsors')])}
  {mi('contact','Contact')}
  <a class="mm-cta interest" href="{FORM}" target="_blank" rel="noopener">Join the Interest List →</a>
</nav>'''
    return desktop, mobile

def footer():
    cities = ['Gilbert', 'Mesa', 'Chandler', 'Queen Creek', 'Tempe', 'Scottsdale']
    clinks = ''.join(f'<li><a href="@/service-area/#{slug(c)}">{c}</a></li>' for c in cities)
    return f'''<footer>
  <svg class="fmtn" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true"><path fill="#0b1b3a" d="M0 120V70l160-50 140 40 180-60 160 70 200-60 160 50 180-40 260 60v40z"/></svg>
  <div class="fbody">
    <div class="wrap fgrid">
      <div>
        <a href="@/" class="brand fbrand" aria-label="Verso Alto Youth Sports — home"><svg viewBox="0 0 1660 1640"><use href="#logostack"/></svg></a>
        <p style="color:var(--muted);margin-top:1.2rem;max-width:360px">A Catholic, nonprofit youth sports league serving families in Gilbert, Mesa, Chandler, Queen Creek and across Arizona's East Valley. Faith · Community · Sports. To the Heights!</p>
      </div>
      <div><h4>Explore</h4><ul><li><a href="@/">Home</a></li><li><a href="@/about/">About</a></li><li><a href="@/blog/">Blog</a></li><li><a href="@/faq/">FAQ</a></li><li><a href="@/support/">Support</a></li><li><a href="@/contact/">Contact</a></li></ul></div>
      <div><h4>Sports</h4><ul><li><a href="@/sports/soccer/">Youth Soccer</a></li><li><a href="@/sports/baseball/">Baseball (coming soon)</a></li><li><a href="@/sports/basketball/">Basketball (coming soon)</a></li><li><a href="@/sports/football/">Football (coming soon)</a></li><li><a class="interest" href="{FORM}" target="_blank" rel="noopener">Interest Form</a></li></ul></div>
      <div><h4>Serving</h4><ul>{clinks}<li><a href="@/service-area/">All Maricopa County cities →</a></li></ul></div>
      <div><h4>Families</h4><ul><li><a href="@/policies/">Policies &amp; Forms</a></li><li><a href="@/policies/privacy/">Privacy Policy</a></li><li><a href="@/policies/refund/">Refund Policy</a></li><li><a href="mailto:Shostutler@versoaltoyouthsports.com">Email us</a></li><li><a href="tel:+14804930639">(480) 493-0639</a></li></ul></div>
    </div>
    <div class="wrap"><div class="fbig">Verso l'Alto</div>
      <div class="fbottom"><span>© <span id="yr"></span> Verso Alto Youth Sports, Inc. · Arizona 501(c)(3) nonprofit · East Valley, AZ</span><a href="@/policies/privacy/">Privacy Policy</a></div>
    </div>
  </div>
</footer>'''

ORG_LD = {
 "@context": "https://schema.org", "@type": "SportsOrganization", "name": "Verso Alto Youth Sports, Inc.",
 "alternateName": "Verso Alto Youth Sports", "url": SITE + "/", "email": "shostutler@versoaltoyouthsports.com",
 "telephone": "+1-480-493-0639", "sport": ["Soccer", "Baseball", "Basketball", "Football"],
 "description": "Catholic, nonprofit youth sports league for kids in Arizona's East Valley — Gilbert, Mesa, Chandler, Queen Creek and beyond.",
 "address": {"@type": "PostalAddress", "addressLocality": "Gilbert", "addressRegion": "AZ", "addressCountry": "US"},
 "areaServed": [{"@type": "City", "name": c['name'] + ", AZ"} for c in CITIES] + [{"@type": "AdministrativeArea", "name": "Maricopa County, Arizona"}],
 "nonprofitStatus": "Nonprofit501c3",
}

PAGES = []
WEBSITE_LD = {"@context": "https://schema.org", "@type": "WebSite", "name": "Verso Alto Youth Sports", "alternateName": "Verso Alto", "inLanguage": "en-US"}
def page(path, title, desc, body, section, ld=None, home=False):
    PAGES.append(dict(path=path, title=title, desc=desc, body=body, section=section, ld=ld, home=home))

def render(p):
    path = p['path']
    desktop, mobile = nav(p['section'], path)
    full_title = p['title'] if p['home'] else f"{p['title']} | Verso Alto Youth Sports"
    lds = [ORG_LD] + ([p['ld']] if p['ld'] else [])
    ld_html = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in lds)
    redirect = ''
    if p['home']:
        m = {k: v for k, v in ROUTES.items() if k != 'home'}
        redirect = '<script>(function(){var m=' + json.dumps({k: rel('/', v) for k, v in m.items()}) + ';var h=location.hash.slice(1);if(m[h])location.replace(m[h]);})();</script>'
    doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(p['desc'])}" />
<link rel="canonical" href="{SITE}{path}" />
<meta property="og:type" content="{'article' if path.startswith('/blog/') and path != '/blog/' else 'website'}" />
<meta property="og:site_name" content="Verso Alto Youth Sports" />
<meta property="og:title" content="{esc(full_title)}" />
<meta property="og:description" content="{esc(p['desc'])}" />
<meta property="og:url" content="{SITE}{path}" />
<meta name="twitter:card" content="summary" />
<meta name="geo.region" content="US-AZ" /><meta name="geo.placename" content="Gilbert, Arizona" />
<meta name="theme-color" content="#06102a" />
{redirect}
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@300;400;500;600;700;800&family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet" />
{rd('favicon.html').strip()}
<link rel="stylesheet" href="@/assets/site.css" />
{ld_html}
</head>
<body>
{rd('defs.html')}
<div id="progress"></div>
<canvas id="confetti" aria-hidden="true"></canvas>
<div id="wipe" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
<div class="toast" id="toast" role="status"></div>
<header id="hdr">
  <div class="wrap nav">
    <a href="@/" class="brand" aria-label="Verso Alto Youth Sports — home"><svg viewBox="0 0 4450 1085"><use href="#logofull"/></svg></a>
    {desktop}
    <a class="cta-mini interest" href="{FORM}" target="_blank" rel="noopener">Interest Form →</a>
    <button class="burger" id="burger" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>
{mobile}
<main>
{p['body']}
</main>
{footer()}
<script src="@/assets/site.js"></script>
</body>
</html>'''
    return resolve(doc, path)

# ---------------------------------------------------------------- pages
INTEREST_BTN = lambda cls='btn btn-gold', label='Join the Interest List': f'<a class="{cls} interest" href="{FORM}" target="_blank" rel="noopener">{label} {ARROW}</a>'

# HOME
home = sec('home').replace('<div class="sports-grid" data-sportcards></div>', f'<div class="sports-grid">{sport_cards()}</div>')
home = home.replace('<p>A Catholic youth sports program built to help foster growth in faith, build community, and strive for greatness.</p>',
 '<p>A Catholic youth sports program built to help foster growth in faith, build community, and strive for greatness — right here in Arizona\'s East Valley.</p>', 1)
east = [c['name'] for c in CITIES if c['region'] == 'east-valley']
strip = ''.join(f'<a class="chip" href="@/service-area/#{slug(c)}">{c}</a>' for c in east) + '<a class="chip" href="@/service-area/">All Maricopa County cities →</a>'
latest = ''.join(post_card(a, i) for i, a in enumerate(ARTICLES[:3]))
home_extra = f'''
  <section class="sec" style="padding-top:0">
    <div class="wrap">
      <div class="sec-head center reveal">
        <span class="eyebrow" style="justify-content:center">Serving the East Valley</span>
        <h2 class="display">Close to <span class="grad">home</span></h2>
        <p>Saturday-morning youth soccer for families in Gilbert, Mesa, Chandler, Queen Creek, Tempe and neighboring Arizona communities.</p>
      </div>
      <div class="city-strip reveal">{strip}</div>
    </div>
  </section>
  <section class="sec" style="padding-top:0">
    <div class="wrap">
      <div class="sec-head reveal"><span class="eyebrow">From the blog</span><h2 class="display">Tips for Arizona <span class="grad">sports families</span></h2><p>Heat safety, ESA how-tos, faith at home, and everything you need for game day.</p></div>
      <div class="posts">{latest}</div>
      <p class="note reveal"><a href="@/blog/" style="color:var(--gold);font-weight:800">See all articles →</a></p>
    </div>
  </section>
'''
home = home.replace('  <section class="quote">', home_extra + '  <section class="quote">', 1)
page('/', 'Verso Alto Youth Sports | Catholic Youth Soccer & Sports in Gilbert, Mesa & the East Valley AZ',
     'Verso Alto Youth Sports is a Catholic, nonprofit youth sports league in Arizona\'s East Valley. Co-ed soccer for ages 3–8 in Spring 2027 for Gilbert, Mesa, Chandler & Queen Creek families. ESA accepted.',
     home, 'home', home=True)

# SPORTS
sp = sec('sports').replace('<div class="sports-grid" data-sportcards></div>', f'<div class="sports-grid">{sport_cards()}</div>')
sp = sp.replace('<span class="eyebrow">Sports</span>', '<nav class="crumbs"><a href="@/">Home</a><span class="sep">/</span><span>Sports</span></nav>\n      <span class="eyebrow">Sports</span>')
page('/sports/', 'Youth Sports Programs in the East Valley, AZ', 'Explore Verso Alto Youth Sports programs: co-ed youth soccer in Spring 2027 plus baseball, basketball and football coming soon for East Valley, Arizona families.', sp, 'sports')

for key, title, desc in [
 ('soccer', 'Youth Soccer for Ages 3–8 in Gilbert, Mesa & the East Valley', 'Co-ed recreational youth soccer for ages 3–8. Six-week Spring 2027 season on Saturday mornings in Arizona\'s East Valley. No tryouts, ESA accepted.'),
 ('baseball', 'Youth Baseball (Coming Soon) — East Valley, AZ', 'Youth baseball is coming to Verso Alto Youth Sports in Arizona\'s East Valley. Faith-centered, affordable, and fun. Join the interest list.'),
 ('basketball', 'Youth Basketball (Coming Soon) — East Valley, AZ', 'Youth basketball is coming to Verso Alto Youth Sports in Arizona\'s East Valley. Faith-centered, affordable, and fun. Join the interest list.'),
 ('football', 'Youth Football (Coming Soon) — East Valley, AZ', 'Youth football is coming to Verso Alto Youth Sports in Arizona\'s East Valley. Faith-centered, affordable, and fun. Join the interest list.')]:
    b = sec(key)
    b = re.sub(r'<a href="@/sports/" class="back">← All sports</a><br/>', f'<nav class="crumbs"><a href="@/">Home</a><span class="sep">/</span><a href="@/sports/">Sports</a><span class="sep">/</span><span>{key.title()}</span></nav>', b)
    related = [a for a in ARTICLES if key in a['body'] or (key == 'soccer' and a['tag'] == 'Soccer')][:3]
    if key != 'soccer': related = [a for a in ARTICLES if a['slug'] in ('benefits-of-multi-sport-kids', 'why-we-dont-hold-tryouts', 'building-character-through-youth-sports')]
    b += f'''
  <section class="sec" style="padding-top:0">
    <div class="wrap">
      <div class="sec-head reveal"><span class="eyebrow">Read more</span><h2 class="display">Helpful <span class="grad">articles</span></h2></div>
      <div class="posts">{''.join(post_card(a, i) for i, a in enumerate(related))}</div>
      <p class="note reveal">Serving families in <a href="@/service-area/#gilbert" style="color:var(--gold);font-weight:700">Gilbert</a>, <a href="@/service-area/#mesa" style="color:var(--gold);font-weight:700">Mesa</a>, <a href="@/service-area/#chandler" style="color:var(--gold);font-weight:700">Chandler</a>, <a href="@/service-area/#queen-creek" style="color:var(--gold);font-weight:700">Queen Creek</a> and the <a href="@/service-area/" style="color:var(--gold);font-weight:700">greater East Valley</a>.</p>
    </div>
  </section>'''
    page(ROUTES[key], title, desc, b, 'sports')

# ABOUT
ab = sec('about')
ab = ab.replace('<span class="eyebrow">About us</span>', '<nav class="crumbs"><a href="@/">Home</a><span class="sep">/</span><span>About</span></nav>\n      <span class="eyebrow">About us</span>')
ab = ab.replace('<p style="color:var(--muted);margin-top:1rem">We pursue excellence in sport, faith, character, and service. Children and families of all faiths are welcome.</p>',
 '<p style="color:var(--muted);margin-top:1rem">We pursue excellence in sport, faith, character, and service. Children and families of all faiths are welcome.</p>\n        <p style="color:var(--muted);margin-top:1rem">Based in Gilbert and serving families across Arizona\'s East Valley — including <a href="@/service-area/#mesa" style="color:var(--gold);font-weight:700">Mesa</a>, <a href="@/service-area/#chandler" style="color:var(--gold);font-weight:700">Chandler</a>, <a href="@/service-area/#queen-creek" style="color:var(--gold);font-weight:700">Queen Creek</a> and <a href="@/service-area/#tempe" style="color:var(--gold);font-weight:700">Tempe</a> — we\'re starting with <a href="@/sports/soccer/" style="color:var(--gold);font-weight:700">co-ed youth soccer</a> and growing into an all-sport league. Read our story on the <a href="@/blog/" style="color:var(--gold);font-weight:700">blog</a>.</p>')
page('/about/', 'About Us — Catholic Youth Sports in Arizona', 'Verso Alto Youth Sports, Inc. is an Arizona 501(c)(3) nonprofit providing affordable, Christ-centered youth sports for East Valley families. Inspired by St. Pier Giorgio Frassati.', ab, 'about')

# FAQ
fq = sec('faq')
fq = fq.replace('<span class="eyebrow">FAQ</span>', '<nav class="crumbs"><a href="@/">Home</a><span class="sep">/</span><span>FAQ</span></nav>\n      <span class="eyebrow">FAQ</span>')
extra_faq = '''
        <div class="faq reveal"><button><span>What areas do you serve?</span><i class="pm"></i></button><div class="ans"><div><p>Our first season will be played in the East Valley, and we welcome families from Gilbert, Mesa, Chandler, Queen Creek, Tempe, Scottsdale, Phoenix and every city and town in Maricopa County. See our service area page for details on each city.</p></div></div></div>
        <div class="faq reveal"><button><span>How can I support Verso Alto Youth Sports?</span><i class="pm"></i></button><div class="ans"><div><p>You can make a one-time gift, become a monthly supporter, or reach out about coaching and partnerships. Visit our Support page for all the ways to give.</p></div></div></div>
      </div>'''
fq = fq.replace('\n      </div>\n      <p class="noresults"', extra_faq + '\n      <p class="noresults"', 1)
fq += '''
  <section class="sec" style="padding-top:0"><div class="wrap" style="max-width:880px"><p class="note reveal">More answers: <a href="@/service-area/" style="color:var(--gold);font-weight:700">Service area</a> · <a href="@/support/" style="color:var(--gold);font-weight:700">Ways to support</a> · <a href="@/policies/" style="color:var(--gold);font-weight:700">Policies &amp; Forms</a> · <a href="@/blog/using-arizona-esa-funds-for-youth-sports/" style="color:var(--gold);font-weight:700">Using Arizona ESA funds</a></p></div></section>'''
FAQ_LD = None
qs = re.findall(r'<button><span>(.*?)</span>.*?<p>(.*?)</p>', fq, re.S)
FAQ_LD = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": html.unescape(q), "acceptedAnswer": {"@type": "Answer", "text": html.unescape(re.sub('<[^>]+>', '', a))}} for q, a in qs]}
page('/faq/', 'FAQ — Youth Sports Questions from East Valley Families', 'Answers about cost, Arizona ESA funds, season dates, locations and more for Verso Alto Youth Sports in Gilbert, Mesa, Chandler and the East Valley.', fq, 'faq', ld=FAQ_LD)

# CONTACT
ct = sec('contact')
ct = ct.replace('<span class="eyebrow">Contact</span>', '<nav class="crumbs"><a href="@/">Home</a><span class="sep">/</span><span>Contact</span></nav>\n      <span class="eyebrow">Contact</span>')
ct = ct.replace('<option>Giving</option>', '<option>Giving</option><option>Sponsorship</option>')
page('/contact/', 'Contact Us', 'Contact Verso Alto Youth Sports in Gilbert, AZ about Spring 2027 youth soccer, coaching, sponsorships or partnerships. Email or call (480) 493-0639.', ct, 'contact')

# POLICIES
pol_list = ''.join(f'''<a class="pol reveal" style="transition-delay:{i*.07:.2f}s" href="@{ROUTES[k]}"><span class="ic"><svg><use href="#doc"/></svg></span>
  <span><b>{esc(v['title'])}</b><span class="d">{esc(v['d'])}</span></span><span class="arr">→</span></a>''' for i, (k, v) in enumerate(POL.items()))
pl = sec('policies').replace('<div class="pol-list" id="polList"></div>', f'<div class="pol-list">{pol_list}</div>')
pl = pl.replace('<span class="eyebrow">Policies &amp; Forms</span>', '<nav class="crumbs"><a href="@/">Home</a><span class="sep">/</span><span>Policies &amp; Forms</span></nav>\n      <span class="eyebrow">Policies &amp; Forms</span>', 1)
page('/policies/', 'Policies & Forms', 'Privacy, refund, participation waiver, concussion and child protection policies for Verso Alto Youth Sports families in Arizona.', pl, 'faq')
for k, v in POL.items():
    body = conv_hash_links(rd(f'policy_{k}.html'))
    b = phero('Policies &amp; Forms', f'<span style="font-size:clamp(2.4rem,6.5vw,5.6rem)">{esc(v["title"])}</span>', None,
              crumbs=[('Home', '/'), ('Policies &amp; Forms', '/policies/'), (esc(v['title']), None)], orb='var(--sky)')
    b += f'''
  <section class="sec" style="padding-top:60px">
    <div class="wrap doc">
      <a href="@/policies/" class="back">← All policies &amp; forms</a>
      {body}
    </div>
  </section>'''
    page(ROUTES[k], v['title'], f"{v['title']} for Verso Alto Youth Sports, Inc., an Arizona Catholic youth sports nonprofit. {v['d']}", b, 'faq')

# SUPPORT
sup = phero('Support', '<span>Support our</span><br/><span class="grad" style="animation-delay:.12s">mission</span>',
  'Your generosity helps us provide affordable, faith-centered youth sports programs where children can grow in friendship, character, and sportsmanship — for families across Gilbert, Mesa, Chandler and Arizona\'s East Valley.',
  crumbs=[('Home', '/'), ('Support', None)])
def tier(name, amt, link, blurb, feature=False):
    return f'''<div class="tier reveal{' feature' if feature else ''}">
      <h3>{name}</h3><div class="amt">${amt}<small> / month</small></div><p>{blurb}</p>
      <a class="btn btn-gold give" href="{link}" target="_blank" rel="noopener">Give Monthly {ARROW}</a></div>'''
sup += f'''
  <section class="sec" style="padding-top:60px" id="give-once">
    <div class="wrap">
      <div class="give-once reveal zoom">
        <div class="sunburst"></div>
        <div style="position:relative"><span class="eyebrow" style="color:var(--ink)">One-time gift</span><h2 class="display">Make a one-time donation</h2><p>Every gift helps support our programs and the families we serve.</p></div>
        <div style="position:relative;display:flex;flex-direction:column;gap:.8rem;align-items:flex-start">
          <a class="btn btn-dark give" href="{STRIPE['once']}" target="_blank" rel="noopener">Give Once {ARROW}</a>
          <small style="font-weight:600">Secure checkout through Stripe</small>
        </div>
      </div>
    </div>
  </section>
  <section class="sec" style="padding-top:0" id="monthly">
    <div class="wrap">
      <div class="sec-head center reveal"><span class="eyebrow" style="justify-content:center">Monthly giving</span><h2 class="display">Become a monthly <span class="grad">supporter</span></h2><p>Recurring gifts give us steady support to keep registration affordable for every East Valley family.</p></div>
      <div class="tiers">
        {tier('Friends of Verso Alto', 10, STRIPE['friends'], 'A simple way to stand with our players and families every month.')}
        {tier('Family Supporter', 25, STRIPE['family'], 'Helps cover equipment, field rentals, and more for local kids.', feature=True)}
        {tier('Mission Partner', 50, STRIPE['partner'], 'Makes a lasting impact on faith-centered youth sports in Arizona.')}
      </div>
    </div>
  </section>
  <section class="sec" style="padding-top:0" id="sponsors">
    <div class="wrap">
      <div class="sponsor reveal">
        <div>
          <span class="eyebrow">Sponsors</span>
          <h2 class="display" style="font-size:clamp(2.4rem,5vw,4rem);margin:.8rem 0 1rem">Local business <span class="grad">sponsors</span></h2>
          <p class="lead">Partner with Verso Alto Youth Sports to support kids and families in Gilbert, Mesa, Chandler, Queen Creek and across the East Valley — and show your community what your business stands for.</p>
        </div>
        <div>
          <ul class="checks" style="margin-top:0">
            <li>Support affordable, faith-centered youth sports in Arizona</li>
            <li>Connect with local East Valley families</li>
            <li>Sponsorship packages are being finalized</li>
          </ul>
          <div class="btnrow">
            <span class="btn btn-pending" aria-disabled="true">⏳ Sponsorships coming soon</span>
            <a class="btn btn-ghost" href="@/contact/?topic=Sponsorship">Ask about sponsoring</a>
          </div>
        </div>
      </div>
    </div>
  </section>
  <section class="sec" style="padding-top:0" id="other-ways">
    <div class="wrap">
      <div class="sec-head reveal"><span class="eyebrow">Other ways to help</span><h2 class="display">Every hand lifts us <span class="grad">higher</span></h2></div>
      <div class="mini-ways">
        <div class="way reveal"><span class="em">🙏</span><h3>Pray</h3><p>Lift up our players, families, and coaches. Prayer is the foundation of everything we do.</p><a class="link" href="@/about/">Our mission →</a></div>
        <div class="way reveal" style="transition-delay:.08s"><span class="em">📣</span><h3>Coach</h3><p>Share your love of the game and help young athletes grow in skill and character.</p><a class="link" href="@/contact/?topic=Coaching">I want to coach →</a></div>
        <div class="way reveal" style="transition-delay:.16s"><span class="em">🤝</span><h3>Partner</h3><p>Parishes, schools, and local organizations — let's build something great together.</p><a class="link" href="@/contact/?topic=Partnering">Become a partner →</a></div>
      </div>
      <p class="note reveal">Verso Alto Youth Sports, Inc. is an Arizona nonprofit corporation and a 501(c)(3) tax-exempt organization. Donations are tax-deductible to the extent allowed by law. Read our <a href="@/blog/why-coach-youth-sports/" style="color:var(--gold);font-weight:700">guide to coaching</a> or our <a href="@/blog/welcome-to-verso-alto-youth-sports/" style="color:var(--gold);font-weight:700">welcome post</a>.</p>
    </div>
  </section>'''
page('/support/', 'Support Our Mission — Donate to Arizona Youth Sports', 'Donate to Verso Alto Youth Sports, an Arizona 501(c)(3) Catholic youth sports nonprofit. Give once or monthly to keep East Valley youth sports affordable.', sup, 'support')

# SERVICE AREA (Maricopa County) + one page per city
def city_card(c, i=0):
    sl = slug(c['name'])
    return f"""<a class="city reveal{' home' if c.get('home') else ''}" style="transition-delay:{(i%3)*.06:.2f}s" href="@/service-area/{sl}/"><h3>{esc(c['name'])}, AZ</h3><p>{esc(c['tag'])}</p><span class="go">Youth sports in {esc(c['name'])} →</span></a>"""
jump = ''.join(f'<a class="chip" href="#{rid}">{esc(rname)}</a>' for rid, rname, _, _ in REGIONS)
regions_html = ''
for rid, rname, sub, cs in REGIONS:
    cards = ''.join(city_card(dict(c, region=rid), i) for i, c in enumerate(cs))
    regions_html += f"""<section class="region" id="{rid}"><div class="region-head reveal"><h2 class="display">{esc(rname)}</h2><small>{esc(sub)} · {len(cs)} {'city' if len(cs)==1 else 'cities & towns'}</small></div><div class="cities">{cards}</div></section>"""
sa = phero('Service area', '<span>Serving</span> <span class="grad" style="animation-delay:.1s">Maricopa County</span>',
  f'Verso Alto Youth Sports serves families in all {len(CITIES)} cities and towns of Maricopa County, Arizona — starting with Saturday-morning youth soccer in the East Valley.',
  crumbs=[('Home', '/'), ('Service area', None)], orb='var(--grass)')
sa += f"""
  <section class="sec" style="padding-top:60px">
    <div class="wrap">
      <div class="split reveal" style="align-items:start">
        <div>
          <span class="eyebrow">Where we play</span>
          <h2 class="display h2">East Valley <span class="grad">home field</span></h2>
          <p class="lead">Spring 2027 <a href="@/sports/soccer/" style="color:var(--gold);font-weight:700">co-ed youth soccer</a> for ages 3–8 will be played on Saturday mornings at fields in the East Valley (location to be announced). Families in <a href="@/service-area/gilbert/" style="color:var(--gold);font-weight:700">Gilbert</a>, <a href="@/service-area/mesa/" style="color:var(--gold);font-weight:700">Mesa</a>, <a href="@/service-area/chandler/" style="color:var(--gold);font-weight:700">Chandler</a>, <a href="@/service-area/queen-creek/" style="color:var(--gold);font-weight:700">Queen Creek</a> and <a href="@/service-area/tempe/" style="color:var(--gold);font-weight:700">Tempe</a> are just minutes away.</p>
        </div>
        <div class="panel">
          <p style="color:var(--muted)">Live elsewhere in Maricopa County? You're welcome to join us now, and as we grow into <a href="@/sports/" style="color:var(--gold);font-weight:700">baseball, basketball, and football</a> we hope to bring programs closer to every part of the Valley. <a class="interest" href="{FORM}" target="_blank" rel="noopener" style="color:var(--gold);font-weight:700">Join the interest list</a> and tell us where you are.</p>
        </div>
      </div>
      <div class="chips reveal" style="margin-top:2.4rem">{jump}</div>
      {regions_html}
    </div>
  </section>"""
SA_LD = {"@context": "https://schema.org", "@type": "ItemList", "name": "Verso Alto Youth Sports service area — Maricopa County, AZ",
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f"{c['name']}, AZ"} for i, c in enumerate(CITIES)]}
page('/service-area/', 'Service Area — Youth Sports Across Maricopa County, AZ',
     f"Verso Alto Youth Sports serves all {len(CITIES)} cities and towns in Maricopa County, AZ — Gilbert, Mesa, Chandler, Queen Creek, Tempe, Phoenix, Scottsdale, Glendale, Peoria and more.",
     sa, 'about', ld=SA_LD)

ART_POOL = ['spring-2027-soccer-season-preview', 'using-arizona-esa-funds-for-youth-sports', 'arizona-heat-safety-for-youth-sports',
            'best-age-to-start-soccer', 'why-we-dont-hold-tryouts', 'what-to-pack-for-saturday-soccer', 'recreational-vs-club-soccer-phoenix',
            'benefits-of-multi-sport-kids', 'sun-safety-for-kids-in-arizona', 'what-verso-l-alto-means']
ABY = {a['slug']: a for a in ARTICLES}
for ci, c in enumerate(CITIES):
    name, sl = c['name'], slug(c['name'])
    near = ''.join(f'<a class="chip" href="@/service-area/{slug(n)}/">{esc(n)}, AZ</a>' for n in c['nearby'])
    picks = [ABY[ART_POOL[(ci + k) % len(ART_POOL)]] for k in (0, 3, 6)]
    where = ("just minutes from our planned East Valley fields" if c.get('home') else
             "a drive away from our East Valley fields — and we hope to bring programs closer as we grow")
    body = phero(f'Youth sports in {esc(name)}, AZ', f'<span>{esc(name)}</span>', esc(c['tag']),
                 crumbs=[('Home', '/'), ('Service area', '/service-area/'), (esc(name), None)], orb='var(--grass)' if c.get('home') else 'var(--gold)',
                 extra=f'<span class="soon-badge{" live" if c.get("home") else ""}">{"● East Valley home field" if c.get("home") else "Maricopa County · " + esc(c["region_name"])}</span>')
    body += f"""
  <section class="sec" style="padding-top:60px">
    <div class="wrap split" style="align-items:start">
      <div class="reveal left">
        <span class="eyebrow">About {esc(name)}</span>
        <h2 class="display h2">Families in <span class="grad">{esc(name)}</span></h2>
        <p class="lead">{esc(c['about'])}</p>
        <h3 class="city-sub">Verso Alto Youth Sports in {esc(name)}</h3>
        <p style="color:#d4dcf0">{esc(c['fit'])}</p>
        <div class="btnrow">{INTEREST_BTN()}<a class="btn btn-ghost" href="@/sports/soccer/">Youth soccer details</a></div>
      </div>
      <div class="panel reveal right">
        <span class="eyebrow">At a glance</span>
        <ul class="facts-list">
          <li><b>City</b><span>{esc(name)}, Arizona</span></li>
          <li><b>County</b><span>Maricopa County</span></li>
          <li><b>Area</b><span>{esc(c['region_name'])}</span></li>
          <li><b>Now forming</b><span><a href="@/sports/soccer/">Co-ed soccer, ages 3–8</a> · Spring 2027</span></li>
          <li><b>Coming soon</b><span><a href="@/sports/baseball/">Baseball</a>, <a href="@/sports/basketball/">basketball</a>, <a href="@/sports/football/">football</a></span></li>
          <li><b>Tryouts</b><span>None — every child plays</span></li>
          <li><b>Payment</b><span>Affordable · <a href="@/blog/using-arizona-esa-funds-for-youth-sports/">Arizona ESA accepted</a></span></li>
        </ul>
      </div>
    </div>
  </section>
  <section class="sec" style="padding-top:0">
    <div class="wrap" style="max-width:900px">
      <div class="sec-head reveal"><span class="eyebrow">{esc(name)} family FAQ</span><h2 class="display" style="font-size:clamp(2rem,4.5vw,3.2rem)">Questions from <span class="grad">{esc(name)}</span> parents</h2></div>
      <div class="qa reveal">
        <h3>Where will {esc(name)} kids play?</h3>
        <p>Our first season is played on Saturday mornings at fields in the East Valley (exact location to be announced). For {esc(name)} families, that's {where}.</p>
        <h3>Can {esc(name)} families use Arizona ESA funds?</h3>
        <p>Yes. Verso Alto Youth Sports is an approved Arizona ESA vendor. Choose ESA at registration and you'll receive an invoice for ClassWallet. <a href="@/blog/using-arizona-esa-funds-for-youth-sports/">Here's how it works.</a></p>
        <h3>Do we need to be Catholic to join?</h3>
        <p>No. Our programs are rooted in the Catholic faith, and families of all faiths in {esc(name)} and across Maricopa County are welcome. <a href="@/faq/">See the full FAQ.</a></p>
      </div>
      <div class="sec-head reveal" style="margin-top:3rem;margin-bottom:1.2rem"><span class="eyebrow">Nearby</span></div>
      <div class="chips reveal">{near}<a class="chip" href="@/service-area/">All Maricopa County cities →</a></div>
    </div>
  </section>
  <section class="sec" style="padding-top:0">
    <div class="wrap">
      <div class="sec-head reveal"><span class="eyebrow">For {esc(name)} sports families</span><h2 class="display" style="font-size:clamp(2rem,4.5vw,3.2rem)">Helpful <span class="grad">articles</span></h2></div>
      <div class="posts">{''.join(post_card(a, i) for i, a in enumerate(picks))}</div>
    </div>
  </section>"""
    ld = {"@context": "https://schema.org", "@type": "Service", "name": f"Youth sports in {name}, AZ",
          "serviceType": "Youth sports league", "provider": {"@type": "SportsOrganization", "name": "Verso Alto Youth Sports"},
          "areaServed": {"@type": "City", "name": f"{name}, AZ", "containedInPlace": {"@type": "AdministrativeArea", "name": "Maricopa County, Arizona"}},
          "description": c['fit']}
    page(f'/service-area/{sl}/', f'Youth Sports in {name}, AZ — Catholic Youth Soccer',
         f"Faith-centered, affordable youth soccer for {name}, AZ families with kids ages 3–8. No tryouts, Arizona ESA accepted. Baseball, basketball & football coming soon.",
         body, 'about', ld=ld)

# BLOG INDEX
tags = ['All'] + sorted({a['tag'] for a in ARTICLES})
chips = ''.join(f'<button class="chip{" on" if t == "All" else ""}" data-filter="{t}">{t}</button>' for t in tags)
bl = phero('Blog', '<span>The</span> <span class="grad" style="animation-delay:.1s">sideline</span>',
  'Tips, stories, and guides for Arizona youth sports families — heat safety, Arizona ESA, faith at home, game-day checklists, and news from Verso Alto.',
  crumbs=[('Home', '/'), ('Blog', None)], orb='var(--sun)')
bl += f'''
  <section class="sec" style="padding-top:60px">
    <div class="wrap">
      <div class="chips reveal" style="margin-bottom:2rem">{chips}</div>
      <div class="posts">{''.join(post_card(a, i) for i, a in enumerate(ARTICLES))}</div>
    </div>
  </section>'''
BLOG_LD = {"@context": "https://schema.org", "@type": "Blog", "name": "Verso Alto Youth Sports Blog", "url": SITE + "/blog/",
           "blogPost": [{"@type": "BlogPosting", "headline": a['title'], "datePublished": a['date'], "url": f"{SITE}/blog/{a['slug']}/"} for a in ARTICLES]}
page('/blog/', 'Blog — Tips for Arizona Youth Sports Families', 'Articles for East Valley and Arizona youth sports families: heat safety, Arizona ESA funds, soccer tips, faith at home, and Verso Alto news.', bl, 'blog', ld=BLOG_LD)

# ARTICLES
for a in ARTICLES:
    words = len(re.sub('<[^>]+>', ' ', a['body']).split()); mins = max(2, round(words / 220))
    idx = ARTICLES.index(a)
    same = [x for x in ARTICLES if x is not a and x['tag'] == a['tag']]
    others = [x for x in ARTICLES if x is not a and x not in same]
    rel3 = (same + others)[:3]
    nb = ''
    newer = ARTICLES[idx - 1] if idx > 0 else None
    older = ARTICLES[idx + 1] if idx + 1 < len(ARTICLES) else None
    b = phero('Blog', f'<span style="font-size:clamp(2.2rem,5.6vw,4.6rem);line-height:1">{esc(a["title"])}</span>', None,
              crumbs=[('Home', '/'), ('Blog', '/blog/'), (esc(a['tag']), None)], orb='var(--sun)',
              extra=f'<div class="post-meta"><span class="tagpill t-{a["tag"]}">{a["tag"]}</span><time datetime="{a["date"]}">{fmt_date(a["date"])}</time><span>· {mins} min read</span><span>· By Verso Alto Youth Sports</span></div>')
    b += f'''
  <section class="sec" style="padding-top:60px">
    <div class="wrap">
      <article class="prose">{a['body']}</article>
      <div class="local-links reveal">Serving youth sports families in <a href="@/service-area/#gilbert">Gilbert</a>, <a href="@/service-area/#mesa">Mesa</a>, <a href="@/service-area/#chandler">Chandler</a>, <a href="@/service-area/#queen-creek">Queen Creek</a>, <a href="@/service-area/#tempe">Tempe</a> and <a href="@/service-area/">across Maricopa County</a>. Explore <a href="@/sports/soccer/">youth soccer</a>, read our <a href="@/faq/">FAQ</a>, or <a href="@/support/">support our mission</a>.</div>
      <div class="post-cta reveal"><div><h3>Spring 2027 soccer</h3><p style="font-weight:600">Be the first to know when registration opens.</p></div>{INTEREST_BTN('btn')}</div>
      <div style="max-width:760px;margin:2rem auto 0;display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap">
        {f'<a class="back" style="margin:0" href="@/blog/{older["slug"]}/">← {esc(older["title"][:48])}{"…" if len(older["title"])>48 else ""}</a>' if older else '<span></span>'}
        {f'<a class="back" style="margin:0" href="@/blog/{newer["slug"]}/">{esc(newer["title"][:48])}{"…" if len(newer["title"])>48 else ""} →</a>' if newer else ''}
      </div>
      <div class="related"><div class="sec-head reveal"><span class="eyebrow">Keep reading</span><h2 class="display" style="font-size:clamp(2rem,4.5vw,3.2rem)">Related <span class="grad">articles</span></h2></div>
      <div class="posts">{''.join(post_card(x, i) for i, x in enumerate(rel3))}</div></div>
    </div>
  </section>'''
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": a['title'], "description": a['desc'],
          "datePublished": a['date'], "dateModified": a['date'], "author": {"@type": "Organization", "name": "Verso Alto Youth Sports"},
          "publisher": {"@type": "Organization", "name": "Verso Alto Youth Sports"}, "mainEntityOfPage": f"{SITE}/blog/{a['slug']}/",
          "keywords": f"{a['tag']}, youth sports, Arizona, East Valley, Gilbert, Mesa, Chandler, Catholic youth sports"}
    page(f"/blog/{a['slug']}/", a['title'], a['desc'], b, 'blog', ld=ld)

# ---------------------------------------------------------------- single-file mode
def route_of(path):
    r = path.strip('/')
    return r or 'home'

def resolve_single(h):
    h = city_links(h)
    def fix(m):
        attr, target = m.group(1), m.group(2)
        if target.startswith('/assets/'):
            return m.group(0)
        mm = re.match(r'([^?#]*)(\?[^#]*)?(#.*)?', target)
        r = route_of(mm.group(1)); q = mm.group(2) or ''; frag = (mm.group(3) or '')[1:]
        return f'{attr}="#{r}{"/" + frag if frag else ""}{q}"'
    return re.sub(r'(href|src)="@(/[^"]*)"', fix, h)

ROUTER = r"""
{
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const ALIAS={soccer:'sports/soccer',baseball:'sports/baseball',basketball:'sports/basketball',football:'sports/football',privacy:'policies/privacy',refund:'policies/refund',waiver:'policies/waiver',concussion:'policies/concussion','child-protection':'policies/child-protection'};
const pages=$$('.page'), routes=pages.map(p=>p.dataset.route), wipe=$('#wipe');
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
let current=null;
function parse(){
  let h=decodeURIComponent(location.hash.slice(1)), q='';
  const qi=h.indexOf('?'); if(qi>=0){q=h.slice(qi+1); h=h.slice(0,qi)}
  h=h.replace(/^\/+|\/+$/g,''); if(ALIAS[h]) h=ALIAS[h]; if(!h) h='home';
  let r=h, sub='';
  while(r && !routes.includes(r)){const i=r.lastIndexOf('/'); sub=r.slice(i+1)+(sub?'/'+sub:''); r=i>0?r.slice(0,i):''}
  if(!r){ if(document.getElementById(h)){r=current||'home'; sub=h} else {r='home'; sub=''} }
  return {r, sub, q};
}
function show(){
  const {r, sub, q}=parse(), pg=pages[routes.indexOf(r)];
  document.body.classList.remove('menu-open');
  pages.forEach(p=>p.classList.toggle('active', p===pg));
  const sec=pg.dataset.section;
  $$('#tabs [data-tab]').forEach(a=>a.classList.toggle('active', a.getAttribute('href').slice(1)===sec));
  $$('#mobileMenu .mm-item > a').forEach(a=>a.classList.toggle('active', a.getAttribute('href').slice(1)===sec));
  $$('#mobileMenu .mm-group').forEach(g=>g.classList.toggle('current', $('.mm-row > a',g).getAttribute('href').slice(1)===sec));
  $$('#mobileMenu .mm-sub a').forEach(a=>a.classList.toggle('active', a.getAttribute('href').slice(1)===r));
  document.title=pg.dataset.title;
  const md=$('meta[name=description]'); if(md) md.setAttribute('content', pg.dataset.desc);
  if(r==='contact' && q){const t=new URLSearchParams(q).get('topic'), s=$('#ft'); if(t&&s) [...s.options].forEach(o=>{if(o.text===t) s.value=o.text})}
  window.VA_setPill && window.VA_setPill();
  const el=sub && document.getElementById(sub);
  if(el){ setTimeout(()=>el.scrollIntoView({behavior: current===r?'smooth':'auto', block:'start'}), 30) } else if(current!==r){ window.scrollTo(0,0) }
  current=r; dispatchEvent(new Event('scroll'));
}
function go(){
  const {r}=parse();
  if(current===null || r===current || reduce || !wipe){ show(); return }
  wipe.className='in'; setTimeout(()=>{show(); wipe.className='out'; setTimeout(()=>wipe.className='',700)},520);
}
addEventListener('hashchange', go);
show();
}
"""

def build_single(out_dir):
    desktop, mobile = nav(None, None)
    pages_html = ''
    for p in PAGES:
        full_title = p['title'] if p['home'] else f"{p['title']} | Verso Alto Youth Sports"
        pages_html += f'<div class="page" data-route="{route_of(p["path"])}" data-section="{p["section"]}" data-title="{esc(full_title)}" data-desc="{esc(p["desc"])}">\n{p["body"]}\n</div>\n'
    home = PAGES[0]
    css = rd('site.css'); js = rd('site.js')
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(home['title'])}</title>
<meta name="description" content="{esc(home['desc'])}" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta property="og:image" content="{PREVIEW_URL}/og-image.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{PREVIEW_URL}/og-image.png" />
<meta property="og:type" content="website" /><meta property="og:site_name" content="Verso Alto Youth Sports" />
<meta property="og:title" content="{esc(home['title'])}" /><meta property="og:description" content="{esc(home['desc'])}" />
<meta name="geo.region" content="US-AZ" /><meta name="geo.placename" content="Gilbert, Arizona" />
<meta name="theme-color" content="#06102a" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@300;400;500;600;700;800&family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet" />
{rd('favicon.html').strip()}
<style>
{css}
</style>
{"".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in [ORG_LD, WEBSITE_LD] + [p["ld"] for p in PAGES if p["ld"]])}
</head>
<body>
{rd('defs.html')}
<div id="progress"></div>
<canvas id="confetti" aria-hidden="true"></canvas>
<div id="wipe" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
<div class="toast" id="toast" role="status"></div>
<header id="hdr">
  <div class="wrap nav">
    <a href="@/" class="brand" aria-label="Verso Alto Youth Sports — home"><svg viewBox="0 0 4450 1085"><use href="#logofull"/></svg></a>
    {desktop}
    <a class="cta-mini interest" href="{FORM}" target="_blank" rel="noopener">Interest Form →</a>
    <button class="burger" id="burger" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>
{mobile}
<main>
{pages_html}
</main>
{footer()}
<script>
{js}
</script>
<script>
{ROUTER}
</script>
</body>
</html>"""
    doc = resolve_single(doc)
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(doc)
    return doc

# ---------------------------------------------------------------- write
if os.path.exists(OUT):
    for n in os.listdir(OUT):
        if n in ('.git', '_build'): continue
        p = os.path.join(OUT, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
if SINGLE:
    build_single(OUT)
else:
  os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
  shutil.copy(os.path.join(SRC, 'site.css'), os.path.join(OUT, 'assets', 'site.css'))
  shutil.copy(os.path.join(SRC, 'site.js'), os.path.join(OUT, 'assets', 'site.js'))
  for p in PAGES:
      d = os.path.join(OUT, p['path'].strip('/'))
      os.makedirs(d, exist_ok=True)
      open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(render(p))
  today = datetime.date.today().isoformat()
  sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
      f'  <url><loc>{SITE}{p["path"]}</loc><lastmod>{next((a["date"] for a in ARTICLES if p["path"] == "/blog/"+a["slug"]+"/"), today)}</lastmod></url>\n' for p in PAGES) + '</urlset>\n'
  open(os.path.join(OUT, 'sitemap.xml'), 'w').write(sm)
open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nDisallow: /_build/\n' + ('' if SINGLE else f'Sitemap: {SITE}/sitemap.xml\n'))
open(os.path.join(OUT, '.nojekyll'), 'w').write('')
if os.path.exists(os.path.join(SRC, 'og-image.png')): shutil.copy(os.path.join(SRC, 'og-image.png'), os.path.join(OUT, 'og-image.png'))
nf = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>Page not found | Verso Alto Youth Sports</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;text-align:center;font-family:Inter,system-ui,sans-serif;background:linear-gradient(180deg,#0b1b3a,#050d22);color:#fbf6ea;padding:24px}h1{font-size:clamp(3rem,12vw,7rem);margin:0;color:#f2b632;font-family:Anton,Impact,sans-serif}a{display:inline-block;margin-top:24px;padding:14px 26px;border-radius:999px;background:linear-gradient(135deg,#f2b632,#ff8a3d);color:#0b1430;font-weight:800;text-decoration:none}</style></head>
<body><div><h1>404</h1><p>We couldn't find that page — but the heights are still waiting.</p><a id="home" href="/">Back to home</a></div>
<script>var b=location.pathname.indexOf('/verso-alto-youth-sports/')===0?'/verso-alto-youth-sports/':'/';document.getElementById('home').href=b;/*SINGLE*/</script></body></html>'''
if SINGLE:
    nf = nf.replace('/*SINGLE*/', "var r=location.pathname.slice(b.length).replace(/\\/+$/,'');if(r&&r.indexOf('.')<0)location.replace(b+'#'+r+location.hash.replace('#','/'));")
else:
    nf = nf.replace('/*SINGLE*/', '')
open(os.path.join(OUT, '404.html'), 'w').write(nf)
open(os.path.join(OUT, 'README.md'), 'w').write('''# Verso Alto Youth Sports — Website

Static multi-page site. Every page lives in its own folder (e.g. `sports/soccer/index.html`) so URLs read like `versoaltoyouthsports.com/sports/soccer/`.

Built from the `_build/` folder.\n\n- One-file mode (current, until the domain is connected): `python3 _build/build.py . --single` → everything in `index.html` with `#` links\n- Separate-pages mode (for the real domain): `python3 _build/build.py .` → clean URLs like `/sports/soccer/`\n\nRun it — edit sources there (pages, articles, cities, CSS, JS) and rebuild.
''')
print(f'built {len(PAGES)} pages -> {OUT}' + (' (single index.html)' if SINGLE else ''))

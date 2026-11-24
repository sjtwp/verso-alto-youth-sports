import os,re,sys,urllib.parse
D=sys.argv[1]; bad=[]; n=0
ids={}
def page_ids(f):
    if f not in ids: ids[f]=set(re.findall(r'\bid="([^"]+)"',open(f).read()))
    return ids[f]
for root,_,files in os.walk(D):
    for fn in files:
        if not fn.endswith('.html'): continue
        f=os.path.join(root,fn); s=open(f).read()
        for h in re.findall(r'<a\b[^>]*\bhref="([^"]+)"',s)+re.findall(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"',s)+re.findall(r'<script[^>]*src="([^"]+)"',s):
            if re.match(r'(https?:|mailto:|tel:|data:)',h): continue
            n+=1
            u=urllib.parse.urlsplit(h); path=u.path
            if fn=='404.html': continue
            tgt=os.path.normpath(os.path.join(root,path)) if path else f
            if os.path.isdir(tgt): tgt=os.path.join(tgt,'index.html')
            if not os.path.exists(tgt): bad.append((f,h,'missing')); continue
            if u.fragment and tgt.endswith('.html') and u.fragment not in page_ids(tgt): bad.append((f,h,'no-anchor'))
print('links checked',n,'bad',len(bad))
for b in bad[:30]: print(b)

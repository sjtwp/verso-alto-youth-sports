{
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const yr=$('#yr'); if(yr) yr.textContent=new Date().getFullYear();

/* ---------- desktop tab pill ---------- */
function setPill(){
  const tabs=$('#tabs'); if(!tabs) return;
  const a=$('#tabs [data-tab].active'), pill=$('#tabs .pill');
  if(!a){pill.style.width=0;return}
  const t=tabs.getBoundingClientRect(), r=a.getBoundingClientRect();
  pill.style.left=(r.left-t.left)+'px'; pill.style.width=r.width+'px';
}
setPill(); addEventListener('resize',setPill); document.fonts&&document.fonts.ready.then(setPill);

/* ---------- mobile menu + accordions ---------- */
const burger=$('#burger');
if(burger) burger.addEventListener('click',()=>{
  const open=document.body.classList.toggle('menu-open');
  burger.setAttribute('aria-expanded',open);
});
$$('#mobileMenu .mm-toggle').forEach(btn=>btn.addEventListener('click',()=>{
  const g=btn.closest('.mm-group'), open=!g.classList.contains('open');
  $$('#mobileMenu .mm-group.open').forEach(x=>{if(x!==g){x.classList.remove('open');$('.mm-toggle',x).setAttribute('aria-expanded','false')}});
  g.classList.toggle('open',open); btn.setAttribute('aria-expanded',open);
}));
/* open the group for the current section by default */
const cur=$('#mobileMenu .mm-group.current'); if(cur){cur.classList.add('open');$('.mm-toggle',cur).setAttribute('aria-expanded','true')}
addEventListener('keydown',e=>{if(e.key==='Escape')document.body.classList.remove('menu-open')});

/* ---------- page transition (wipe) ---------- */
const wipe=$('#wipe');
if(wipe && !reduce){
  wipe.className='out'; setTimeout(()=>wipe.className='',700);
  document.addEventListener('click',e=>{
    const a=e.target.closest('a'); if(!a||e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey) return;
    if(a.target==='_blank'||a.hasAttribute('download')) return;
    const u=new URL(a.href,location.href);
    if(u.origin!==location.origin||!/^https?:/.test(u.protocol)) return;
    if(u.pathname===location.pathname&&u.hash) return; /* same-page anchor */
    e.preventDefault(); document.body.classList.remove('menu-open');
    wipe.className='in'; setTimeout(()=>location.href=a.href,520);
  });
  addEventListener('pageshow',ev=>{if(ev.persisted)wipe.className=''});
}

/* ---------- scroll: header, progress, hero parallax ---------- */
const hdr=$('#hdr'), prog=$('#progress'), hero=$('#hero');
let mx=0;
function parallax(){
  if(!hero||reduce) return; const y=scrollY; if(y>innerHeight*1.1) return;
  $$('.mtn[data-depth]',hero).forEach(l=>{l.style.transform=`translate3d(${-mx*(+l.dataset.mx)}px,${y*(+l.dataset.depth)}px,0)`});
  const sun=$('[data-sun]',hero); if(sun) sun.style.transform=`translateX(-50%) translateY(${-y*.35}px) scale(${1+y/1800})`;
  const hc=$('#heroContent'); if(hc){hc.style.transform=`translate3d(0,${y*.4}px,0)`; hc.style.opacity=Math.max(0,1-y/(innerHeight*.75))}
}
function onScroll(){
  const y=scrollY, h=document.documentElement.scrollHeight-innerHeight;
  if(prog) prog.style.width=(h>0?y/h*100:0)+'%';
  if(hdr) hdr.classList.toggle('scrolled',y>40);
  parallax();
}
let ticking=false; addEventListener('scroll',()=>{if(!ticking){ticking=true;requestAnimationFrame(()=>{onScroll();ticking=false})}},{passive:true});
addEventListener('mousemove',e=>{mx=e.clientX/innerWidth-.5; parallax()});
onScroll();

/* ---------- reveals ---------- */
const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}}),{threshold:0,rootMargin:'0px 0px -8% 0px'});
$$('.reveal').forEach(el=>io.observe(el));

/* ---------- tilt cards ---------- */
document.addEventListener('mousemove',e=>{
  const card=e.target.closest('.tilt'); $$('.tilt').forEach(c=>{if(c!==card)c.style.transform=''});
  if(!card||reduce) return;
  const r=card.getBoundingClientRect(), x=(e.clientX-r.left)/r.width, y=(e.clientY-r.top)/r.height;
  card.style.transform=`rotateY(${(x-.5)*10}deg) rotateX(${(.5-y)*10}deg) translateY(-6px)`;
  card.style.setProperty('--mx',x*100+'%'); card.style.setProperty('--my',y*100+'%');
});

/* ---------- soccer field animation ---------- */
const field=$('#field');
if(field){
  const ball=document.createElement('div'); ball.className='fball'; ball.innerHTML='<svg viewBox="0 0 100 100"><use href="#ball"/></svg>'; field.append(ball);
  const players=[...Array(6)].map((_,i)=>{const p=document.createElement('div'); p.className='player '+(i<3?'home':'away'); field.append(p); return p});
  const play=()=>{const bx=8+Math.random()*80, by=12+Math.random()*70; ball.style.left=bx+'%'; ball.style.top=by+'%';
    players.forEach((p,i)=>{const near=i%3===0; p.style.left=(near?bx+(Math.random()*10-5):10+Math.random()*78)+'%'; p.style.top=(near?by+(Math.random()*10-5):10+Math.random()*75)+'%'})};
  play(); setInterval(play,1500);
}

/* ---------- FAQ ---------- */
$$('.faq button').forEach(b=>b.addEventListener('click',()=>{const f=b.parentElement, open=!f.classList.contains('open'); $$('.faq').forEach(x=>x.classList.remove('open')); if(open) f.classList.add('open')}));
const fs=$('#faqSearch');
if(fs){
  $$('.faq').forEach(f=>{f.dataset.q=$('button span',f).textContent; f.dataset.a=$('.ans p',f).textContent});
  const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'), h=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
  fs.addEventListener('input',()=>{
    const v=fs.value.trim().toLowerCase(); let shown=0;
    $$('.faq').forEach(f=>{const hit=!v||(f.dataset.q+' '+f.dataset.a).toLowerCase().includes(v);
      f.style.display=hit?'':'none'; if(hit)shown++;
      const hl=t=>v?h(t).replace(new RegExp('('+esc(h(v))+')','ig'),'<mark>$1</mark>'):h(t);
      $('button span',f).innerHTML=hl(f.dataset.q); $('.ans p',f).innerHTML=hl(f.dataset.a);
      f.classList.toggle('open',!!v&&hit&&shown===1)});
    $('#noRes').style.display=shown?'none':'block';
  });
}

/* ---------- blog filter ---------- */
const chips=$$('.chip[data-filter]');
chips.forEach(c=>c.addEventListener('click',()=>{
  chips.forEach(x=>x.classList.toggle('on',x===c)); const t=c.dataset.filter;
  $$('.post-card').forEach(p=>p.style.display=(t==='All'||p.dataset.tag===t)?'':'none');
}));

/* ---------- contact form -> mailto ---------- */
const cform=$('#cform');
if(cform){
  const topic=new URLSearchParams(location.search).get('topic'), sel=$('#ft');
  if(topic) [...sel.options].forEach(o=>{if(o.text===topic) sel.value=o.text});
  cform.addEventListener('submit',e=>{
    e.preventDefault();
    const subj=`[${sel.value}] Message from ${$('#fn').value}`;
    const body=`${$('#fm').value}\n\n— ${$('#fn').value} (${$('#fe').value})`;
    location.href=`mailto:Shostutler@versoaltoyouthsports.com?subject=${encodeURIComponent(subj)}&body=${encodeURIComponent(body)}`;
    burst(innerWidth/2,innerHeight*.6); toast('Opening your email app… Verso l\'alto!');
  });
}

/* ---------- confetti on interest / give clicks ---------- */
const cv=$('#confetti'), cx=cv.getContext('2d'); let parts=[];
const sizeC=()=>{cv.width=innerWidth;cv.height=innerHeight}; sizeC(); addEventListener('resize',sizeC);
function burst(x,y){ if(reduce) return; const cols=['#f2b632','#ff8a3d','#ffffff','#4a86ff','#2fbf71']; const fresh=!parts.length;
  for(let i=0;i<120;i++){const a=Math.random()*6.28, s=Math.random()*12+4; parts.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-6,r:Math.random()*6+3,c:cols[i%5],rot:Math.random()*6,vr:Math.random()*.3-.15,life:110})}
  if(fresh) loop();
}
function loop(){cx.clearRect(0,0,cv.width,cv.height);
  parts.forEach(p=>{p.vy+=.35;p.vx*=.98;p.x+=p.vx;p.y+=p.vy;p.rot+=p.vr;p.life--; cx.save();cx.translate(p.x,p.y);cx.rotate(p.rot);cx.globalAlpha=Math.max(0,p.life/110);cx.fillStyle=p.c;cx.fillRect(-p.r/2,-p.r/4,p.r,p.r/2);cx.restore()});
  parts=parts.filter(p=>p.life>0); if(parts.length) requestAnimationFrame(loop); else cx.clearRect(0,0,cv.width,cv.height)}
document.addEventListener('click',e=>{const a=e.target.closest('.interest,.give'); if(a){const r=a.getBoundingClientRect(); burst(r.left+r.width/2,r.top+r.height/2)}});
function toast(t){const el=$('#toast'); el.textContent=t; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),3200)}

/* ---------- inner-page mountain edge ---------- */
$$('.phero').forEach(ph=>ph.insertAdjacentHTML('beforeend','<svg class="pmtn" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true"><path fill="#ffffff" opacity=".07" d="M0 120V60l180-50 160 50 200-55 180 60 220-50 180 45 160-35 160 40v115z"/><path fill="#050d22" d="M0 120V85l140-35 170 40 190-45 160 45 210-40 170 35 200-30 200 40v65z"/></svg>'));
}

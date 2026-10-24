"""Descobre matérias possivelmente relevantes; NÃO extrai percentuais nem aprova pesquisas."""
import datetime, email.utils, json, os, pathlib, urllib.parse, urllib.request, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'pendentes.json'
QUERY='("pesquisa" OR "levantamento") "Lula" "Flávio Bolsonaro" "segundo turno"'
RSS='https://news.google.com/rss/search?q='+urllib.parse.quote(QUERY)+'&hl=pt-BR&gl=BR&ceid=BR:pt-419'
CUTOFF=datetime.datetime(2026,10,26,3,0,tzinfo=datetime.timezone.utc)
now=datetime.datetime.now(datetime.timezone.utc)
if now>=CUTOFF:
    print('Encerrada a descoberta de pesquisas pré-eleitorais após 25/10/2026.');raise SystemExit(0)
existing={'updated':'','items':[]}
if OUT.exists(): existing=json.loads(OUT.read_text(encoding='utf-8'))
known={p['url'] for p in existing.get('items',[])}
req=urllib.request.Request(RSS,headers={'User-Agent':'CybertronEleitoral/1.0 (+GitHub Pages; pesquisa jornalística)'})
with urllib.request.urlopen(req,timeout=25) as res: raw=res.read(2_000_000)
root=ET.fromstring(raw)
added=0
for item in root.findall('./channel/item'):
    title=item.findtext('title','').strip();url=item.findtext('link','').strip();published=item.findtext('pubDate','')
    if not url.startswith('https://') or url in known: continue
    try: dt=email.utils.parsedate_to_datetime(published).astimezone(datetime.timezone.utc)
    except (TypeError,ValueError): continue
    if dt<datetime.datetime(2026,10,1,tzinfo=datetime.timezone.utc) or dt>=CUTOFF: continue
    if not all(t in title.casefold() for t in ('lula','bolsonaro')): continue
    existing['items'].append({'title':title,'url':url,'published_at':dt.date().isoformat(),'status':'aguardando_conferencia'})
    known.add(url);added+=1
existing['items']=sorted(existing['items'],key=lambda x:x['published_at'],reverse=True)[:250]
# Somente altera o arquivo quando há descoberta nova: evita commits a cada hora.
if added:
    existing['updated']=now.date().isoformat()
    OUT.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Novas publicações candidatas:',added,'(não são pesquisas confirmadas)')

import json,datetime,re,sys
from urllib.parse import urlparse
p=json.load(open('pesquisas.json',encoding='utf-8'))
assert datetime.date.fromisoformat(p['updated'])
assert isinstance(p['polls'],list) and p['polls']
seen=set()
for x in p['polls']:
    for k in ('institute','date','registration','source'): assert isinstance(x[k],str) and x[k]
    datetime.date.fromisoformat(x['date'])
    assert re.fullmatch(r'BR-\d{5}/2026',x['registration'])
    assert urlparse(x['source']).scheme=='https'
    assert (x['institute'],x['date']) not in seen
    seen.add((x['institute'],x['date']))
    for k in ('l','f','lt','ft'):
        assert isinstance(x[k],(int,float)) and 0<=x[k]<=100
    assert abs(x['l']+x['f']-100)<0.2
    assert x['lt']+x['ft']<=100.1
    assert 0<x['margin']<10
print('Estrutura válida:',len(p['polls']),'pesquisas. Verificação de fontes requer conferência editorial.')

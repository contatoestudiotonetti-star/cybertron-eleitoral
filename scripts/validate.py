import json, datetime, re, sys
from pathlib import Path
from urllib.parse import urlparse

def validate(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    assert isinstance(data,dict) and isinstance(data.get('polls'),list)
    datetime.date.fromisoformat(data['updated'])
    seen=set()
    for p in data['polls']:
        for k in ('institute','date','registration','source','collected_from','collected_to','published_at','sample'):
            assert p.get(k), f'Campo ausente: {k}'
        for k in ('date','collected_from','collected_to','published_at'):
            datetime.date.fromisoformat(p[k])
        assert p['collected_from']<=p['collected_to']<=p['published_at']
        assert re.fullmatch(r'BR-\d{5}/2026',p['registration']),p['registration']
        u=urlparse(p['source']); assert u.scheme=='https' and u.hostname
        assert isinstance(p['sample'],int) and p['sample']>=100
        assert isinstance(p['margin'],(int,float)) and 0<p['margin']<10
        for k in ('l','f'):
            assert isinstance(p.get(k),(int,float)) and 0<=p[k]<=100
        assert abs(p['l']+p['f']-100)<=0.21, 'Votos válidos não somam 100%'
        if p.get('lt') is not None or p.get('ft') is not None:
            assert all(isinstance(p.get(k),(int,float)) and 0<=p[k]<=100 for k in ('lt','ft'))
            assert p['lt']+p['ft']<=100.2
        assert p.get('verified') is True, 'Pesquisa sem aprovação editorial'
        key=(p['registration'],p['collected_from'],p['collected_to'])
        assert key not in seen, 'Registro duplicado'
        seen.add(key)
    print(f'Validação estrutural: {len(data["polls"])} registros aprovados. Conferência editorial exige verificação humana.')
if __name__=='__main__':
    try: validate(sys.argv[1] if len(sys.argv)>1 else 'pesquisas.json')
    except (AssertionError,ValueError,KeyError,TypeError) as exc:
        print('VALIDAÇÃO FALHOU:',exc,file=sys.stderr);sys.exit(1)

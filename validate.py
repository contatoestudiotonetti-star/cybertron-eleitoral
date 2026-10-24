"""Cybertron v4: validação estrutural + evidências editoriais. Não autentica TSE remotamente."""
import datetime as dt
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

REQUIRED = ("institute","registration","source","collected_from","collected_to","published_at","sample")
EVIDENCE = ("report_url","tse_url","reviewer","reviewed_at")
CHECKS = ("tse_checked","report_checked","national_checked","duplicate_checked")

def valid_https(value):
    if not isinstance(value,str): return False
    u=urlparse(value)
    return u.scheme=="https" and bool(u.hostname) and not u.username and not u.password

def validate(path="pesquisas.json", strict=False):
    data=json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    assert isinstance(data,dict) and isinstance(data.get("polls"),list), "Estrutura inválida"
    dt.date.fromisoformat(data["updated"])
    seen=set()
    legacy=0
    for i,p in enumerate(data["polls"],1):
        def check(condition,message):
            if not condition: raise ValueError(f"Pesquisa {i} ({p.get('institute','?')}): {message}")
        for k in REQUIRED: check(p.get(k) is not None and p.get(k)!="",f"Falta {k}")
        for k in ("collected_from","collected_to","published_at"):
            dt.date.fromisoformat(p[k])
        check(p["collected_from"]<=p["collected_to"]<=p["published_at"],"Datas inconsistentes")
        check(bool(re.fullmatch(r"BR-\d{5}/2026",p["registration"])),"Registro TSE com formato inválido")
        check(valid_https(p["source"]),"Fonte jornalística deve ser HTTPS")
        check(type(p["sample"]) is int and p["sample"]>=100,"Amostra inválida")
        check(type(p.get("margin")) in (float,int) and 0<p["margin"]<10,"Margem inválida")
        check(p.get("scope")=="nacional","Abrangência não nacional")
        check(p.get("verified") is True,"Registro não aprovado")
        for k in ("l","f"):
            check(type(p.get(k)) in (int,float) and 0<=p[k]<=100,f"Percentual {k} inválido")
        check(abs(p["l"]+p["f"]-100)<=0.25,"Votos válidos não somam 100%")
        if p.get("lt") is not None or p.get("ft") is not None:
            check(all(type(p.get(k)) in (int,float) and 0<=p[k]<=100 for k in ("lt","ft")),"Votos totais incompletos")
            check(p["lt"]+p["ft"]<=100.25,"Votos totais excedem 100%")
        key=(p["registration"],p["collected_from"],p["collected_to"])
        check(key not in seen,"Registro duplicado")
        seen.add(key)
        # A marcação 'verified' herdada não equivale a evidência auditável.
        e=p.get("editorial")
        if e is None:
            legacy+=1
            if strict: check(False,"Sem documentação editorial")
            print(f"AVISO: pesquisa {i} é legado sem documentação editorial; não apresentar como verificada.",file=sys.stderr)
            continue
        check(isinstance(e,dict),"Campo editorial inválido")
        for k in EVIDENCE: check(bool(e.get(k)),f"Evidência ausente: editorial.{k}")
        for k in ("report_url","tse_url"): check(valid_https(e[k]),f"URL de evidência inválida: {k}")
        dt.date.fromisoformat(e["reviewed_at"])
        check(e["reviewed_at"]>=p["published_at"],"Revisão anterior à divulgação")
        check(isinstance(e.get("checks"),dict),"Checklist editorial ausente")
        for k in CHECKS: check(e["checks"].get(k) is True,f"Checklist pendente: {k}")
    print(f"OK: {len(data['polls'])} pesquisas estruturadas; {legacy} sem evidência editorial auditável.")
    return legacy

if __name__=="__main__":
    try: validate(sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith("--") else "pesquisas.json",strict="--strict" in sys.argv)
    except (AssertionError,ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print("VALIDAÇÃO FALHOU:",exc,file=sys.stderr);sys.exit(1)

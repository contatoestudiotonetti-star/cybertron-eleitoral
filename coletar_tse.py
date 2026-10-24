"""Coleta exclusivamente o EA20 nacional oficial do TSE, sem projeções."""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'apuracao_tse.json'
URL='https://resultados.tse.jus.br/oficial/ele2026/6258/dados/br/br-c0001-e006258-u.json'
UTC=dt.timezone.utc

def number(x):
    if isinstance(x,bool): raise ValueError('booleano em campo numérico')
    if isinstance(x,(int,float)): return int(x)
    if not isinstance(x,str) or not x.isdecimal(): raise ValueError('número TSE inválido')
    return int(x)

def percent(x):
    if isinstance(x,bool): raise ValueError('percentual inválido')
    if isinstance(x,(int,float)): v=float(x)
    elif isinstance(x,str): v=float(x.replace(',','.'))
    else: raise ValueError('percentual inválido')
    if not 0<=v<=100: raise ValueError('percentual fora da faixa')
    return v

def parse(d):
    if not isinstance(d,dict) or str(d.get('ele'))!='6258' or str(d.get('t'))!='2' or d.get('tpabr')!='br':
        raise ValueError('Arquivo não é da eleição presidencial nacional de 2º turno 2026')
    cargos=d.get('carg') or []
    cargos=[c for c in cargos if str(c.get('cd'))=='1']
    if len(cargos)!=1: raise ValueError('Cargo presidencial ausente ou duplicado')
    cand=[]
    for group in cargos[0].get('agr',[]):
        for party in group.get('par',[]):
            for c in party.get('cand',[]):
                if str(c.get('n')) in ('13','22'):
                    cand.append({'number':str(c['n']),'name':str(c.get('nmu') or c.get('nm') or ''),'votes':number(c.get('vap','0')),'percent':percent(c.get('pvap','0'))})
    if len(cand)!=2 or {c['number'] for c in cand}!={'13','22'}:raise ValueError('Candidaturas não identificadas com segurança')
    sections=d.get('s') or {};votes=d.get('v') or {}
    st=number(sections.get('st','0'));total=number(sections.get('ts','0'));valid=number(votes.get('vv','0'))
    if total<=0 or st>total or st<0 or valid<0:raise ValueError('Totalização inconsistente')
    if valid and sum(c['votes'] for c in cand)>valid:raise ValueError('Votos de candidatos excedem votos válidos')
    if valid and abs(sum(c['percent'] for c in cand)-100)>0.25:raise ValueError('Percentuais não fecham 100%')
    # EA20: os campos vb e vn representam, respectivamente, votos em branco e nulos.
    # Se ausentes, registrar null, nunca zero presumido.
    blank_raw=votes.get('vb')
    null_raw=votes.get('vn')
    blank_votes=number(blank_raw) if blank_raw is not None else None
    null_votes=number(null_raw) if null_raw is not None else None
    if blank_votes is not None and blank_votes<0: raise ValueError('Votos brancos negativos')
    if null_votes is not None and null_votes<0: raise ValueError('Votos nulos negativos')
    now=dt.datetime.now(UTC)
    has_votes=valid>0 and st>0
    # Impede dados de testes anteriores ao dia oficial de votação.
    if now.date()<dt.date(2026,10,25):has_votes=False
    finished=str(d.get('tf','n')).lower()=='s' or (st==total and has_votes)
    return {'source':'TSE','source_url':URL,'election':6258,'round':2,'office':'presidente',
        'status':('concluido' if finished else 'apurando') if has_votes else 'aguardando',
        'fetched_at':now.isoformat().replace('+00:00','Z'),
        'tse_updated_at':(str(d.get('dt') or d.get('dg') or '')+' '+str(d.get('ht') or d.get('hg') or '')).strip(),
        'sections_count':st if has_votes else 0,'sections_total':total,
        'sections_percent':percent(sections.get('pst','0')) if has_votes else 0,
        'valid_votes':valid if has_votes else 0,
        'blank_votes':blank_votes if has_votes else None,
        'null_votes':null_votes if has_votes else None,
        'candidates':cand if has_votes else []}

def main():
    req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 (Cybertron Eleitoral; official data mirror)','Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=25) as resp:
            if resp.status!=200:raise RuntimeError(f'HTTP {resp.status}')
            raw=resp.read(3_000_000)
        result=parse(json.loads(raw.decode('utf-8')))
    except (urllib.error.URLError,TimeoutError,ValueError,KeyError,TypeError,json.JSONDecodeError,RuntimeError) as exc:
        print('Falha na coleta oficial; arquivo anterior preservado:',exc)
        return
    # Nunca substituir uma apuração válida por arquivo oficial temporariamente zerado.
    if OUT.exists():
        try:
            old=json.loads(OUT.read_text(encoding='utf-8'))
            if old.get('status') in ('apurando','concluido') and result['status']=='aguardando':
                print('TSE retornou base sem votos; última apuração preservada.');return
            if old.get('status') in ('apurando','concluido') and result['valid_votes']<old.get('valid_votes',0):
                print('Possível regressão de votos; última apuração preservada.');return
        except (ValueError,TypeError):pass
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Status TSE:',result['status'],'votos válidos:',result['valid_votes'])

if __name__=='__main__':main()

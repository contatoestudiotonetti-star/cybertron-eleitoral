"""Monitora manchetes potencialmente relevantes. NÃO aprova resultados eleitorais."""
import datetime as dt
import email.utils
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "pendentes.json"
END = dt.datetime(2026, 10, 26, 3, 0, tzinfo=dt.timezone.utc)
NOW = dt.datetime.now(dt.timezone.utc)
if NOW >= END:
    print("Monitoramento pré-eleitoral encerrado. Histórico preservado.")
    raise SystemExit(0)

queries = [
    '"pesquisa" "Lula" "Flávio Bolsonaro" "segundo turno"',
    '"levantamento" "Lula" "Flávio Bolsonaro" "presidencial"'
]
existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"updated": "", "items": []}
items = existing.get("items", [])
known = {x["url"] for x in items if x.get("url")}
new = 0
for query in queries:
    rss = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    req = urllib.request.Request(rss, headers={"User-Agent": "Mozilla/5.0 (Cybertron research monitor)"})
    with urllib.request.urlopen(req, timeout=25) as response:
        root = ET.fromstring(response.read(2_000_000))
    for entry in root.findall("./channel/item"):
        title = (entry.findtext("title") or "").strip()
        url = (entry.findtext("link") or "").strip()
        raw_date = entry.findtext("pubDate") or ""
        try:
            published = email.utils.parsedate_to_datetime(raw_date).astimezone(dt.timezone.utc)
        except (TypeError, ValueError):
            continue
        if not url.startswith("https://") or url in known or not (dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc) <= published < END):
            continue
        t = title.casefold()
        if not ("lula" in t and "bolsonaro" in t):
            continue
        # Descartar menções claramente não relacionadas a pesquisas nacionais.
        excluded = ("debate", "checamos", "ao vivo", "distrito federal", " no df", "em são paulo", "em minas gerais", "em pernambuco", "em brasília")
        if any(word in t for word in excluded):
            continue
        if not any(word in t for word in ("pesquisa", "levantamento", "votos válidos", "intenção de voto")):
            continue
        items.append({
            "title": title,
            "url": url,
            "published_at": published.date().isoformat(),
            "status": "aguardando_conferencia",
            "scope": "nacional_a_confirmar"
        })
        known.add(url)
        new += 1

items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
existing["items"] = items[:300]
if new:
    existing["updated"] = NOW.date().isoformat()
    OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Novas matérias candidatas: {new}; pendências totais: {len(existing['items'])}. Nenhum percentual foi aprovado automaticamente.")

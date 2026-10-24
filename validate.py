"""Validação estrutural de pesquisas aprovadas; não substitui verificação editorial."""
import datetime as dt
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

def check(path="pesquisas.json"):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    assert isinstance(data, dict) and isinstance(data.get("polls"), list), "Formato de base inválido"
    dt.date.fromisoformat(data["updated"])
    seen = set()
    for p in data["polls"]:
        for k in ("institute", "registration", "source", "collected_from", "collected_to", "published_at", "sample"):
            assert p.get(k) is not None and p.get(k) != "", f"Campo obrigatório: {k}"
        for k in ("collected_from", "collected_to", "published_at"):
            dt.date.fromisoformat(p[k])
        assert p["collected_from"] <= p["collected_to"] <= p["published_at"], "Datas inconsistentes"
        assert re.fullmatch(r"BR-\d{5}/2026", p["registration"]), "Registro TSE fora do padrão"
        parsed = urlparse(p["source"])
        assert parsed.scheme == "https" and parsed.hostname, "Fonte deve ser URL HTTPS"
        assert isinstance(p["sample"], int) and not isinstance(p["sample"], bool) and p["sample"] >= 100
        assert isinstance(p.get("margin"), (int, float)) and 0 < p["margin"] < 10
        assert p.get("verified") is True, "Registro não aprovado editorialmente"
        assert p.get("scope") == "nacional", "Apenas pesquisas nacionais"
        for k in ("l", "f"):
            assert isinstance(p.get(k), (int, float)) and 0 <= p[k] <= 100, f"Percentual inválido: {k}"
        assert abs(p["l"] + p["f"] - 100) <= 0.25, "Votos válidos não somam 100%"
        if p.get("lt") is not None or p.get("ft") is not None:
            assert all(isinstance(p.get(k), (int, float)) and 0 <= p[k] <= 100 for k in ("lt", "ft"))
            assert p["lt"] + p["ft"] <= 100.25, "Votos totais excedem 100%"
        key = (p["registration"], p["collected_from"], p["collected_to"])
        assert key not in seen, "Pesquisa duplicada"
        seen.add(key)
    print(f"Base válida estruturalmente: {len(data['polls'])} pesquisas. Veracidade das fontes depende de revisão humana.")

if __name__ == "__main__":
    try:
        check(sys.argv[1] if len(sys.argv) > 1 else "pesquisas.json")
    except (AssertionError, ValueError, KeyError, TypeError, OSError) as e:
        print("ERRO DE VALIDAÇÃO:", e, file=sys.stderr)
        sys.exit(1)

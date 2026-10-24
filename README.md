# Cybertron Eleitoral 2026 — monitoramento com revisão

## O que faz

- O site é publicado pelo **GitHub Pages / Deploy from a branch / main / (root)**.
- `monitorar.yml` roda aproximadamente a cada hora (o GitHub Actions pode atrasar execuções).
- `scripts/discover.py` procura **notícias candidatas** em um feed público e grava novos links em `pendentes.json`.
- **Nenhum percentual é extraído ou aprovado automaticamente.** Uma notícia pode ser duplicada, incompleta ou imprecisa.
- `scripts/validate.py` bloqueia estrutura incorreta ou registros sem `verified: true`.
- O monitoramento de notícias pré-eleitorais encerra em **26/10/2026 03:00 UTC (00:00 de Brasília)**. Esse corte corresponde à meia-noite de Brasília.
- O painel carrega `pesquisas.json`; se estiver vazio, informa que não há pesquisas aprovadas.

## Como aprovar uma pesquisa

1. Examine `pendentes.json`, a matéria, o relatório do instituto e o registro no PesqEle/TSE.
2. Confirme **votos válidos e totais separadamente**, instituto, amostra, margem de erro, data de coleta, data de publicação e registro.
3. Adicione manualmente a pesquisa a `pesquisas.json`, com campos `institute`, `date`, `collected_from`, `collected_to`, `published_at`, `sample` (inteiro), `margin`, `registration`, `source`, `l`, `f`, `lt`, `ft`, `verified: true`.
4. Atualize `updated` e execute `python scripts/validate.py` antes do commit.
5. O GitHub Pages publica automaticamente o arquivo alterado na branch `main`.

## Limitações e segurança

A verificação automática é **estrutural**, não uma certificação da fonte. O RSS identifica matérias, não fornece resultados oficiais nem comprova o registro no TSE. Se o RSS falhar, o job falha sem alterar dados. O histórico de pesquisas não deve ser apresentado como apuração. Os registros anteriores do pacote original não foram transferidos para a base aprovada porque ainda precisam de conferência.

O GitHub Actions agendado pode ter atrasos e exige que Actions esteja habilitado no repositório. A permissão `contents: write` deve ser permitida em Settings → Actions → General → Workflow permissions. O GitHub Pages permanece configurado para **Deploy from a branch**.

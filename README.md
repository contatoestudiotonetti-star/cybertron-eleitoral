# Cybertron Eleitoral

## Publicação
1. Crie um repositório GitHub e envie estes arquivos para a branch `main`.
2. Em Settings > Pages, escolha GitHub Actions como origem.
3. O workflow valida `pesquisas.json` e publica a página após cada push e a cada hora.
4. O dashboard consulta `pesquisas.json` a cada hora enquanto estiver aberto.

**Atenção:** o workflow verifica e republica os dados existentes; ele NÃO busca automaticamente pesquisas novas. Atualize `pesquisas.json` apenas depois de conferir resultado, período, amostra, margem, registro TSE e URL da publicação original. A validação automática confere a estrutura e consistência aritmética, não a veracidade editorial. Nunca apresente pesquisa como apuração oficial.

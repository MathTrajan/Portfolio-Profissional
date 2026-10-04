# Logos das tecnologias

SVGs do catálogo [Simple Icons](https://github.com/simple-icons/simple-icons),
licenciados em **CC0 1.0 Universal** (domínio público).

Usados por `tools/gerar-capas.py`, que extrai o atributo `d` do único `<path>`
de cada arquivo e redesenha o glifo dentro da pill de tecnologia.

Cinco deles (`powerbi`, `microsoftsqlserver`, `microsoftexcel`, `css3`,
`powershell`) vêm da versão 9 do catálogo: foram removidos das versões
seguintes por política de marca, não por estarem incorretos.

Para acrescentar um logo novo:

```bash
curl -o tools/icones/<slug>.svg \
  https://cdn.jsdelivr.net/npm/simple-icons@13/icons/<slug>.svg
```

Depois registre a cor da marca em `CORES_LOGO`, dentro do gerador. Marca de hex
muito escuro precisa de um tom claro, senão o logo some no fundo `#0f1629`.

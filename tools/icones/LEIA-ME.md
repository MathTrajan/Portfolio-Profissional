# Logos das tecnologias

SVGs do catálogo [Simple Icons](https://github.com/simple-icons/simple-icons),
licenciados em **CC0 1.0 Universal** (domínio público).

Usados por `tools/gerar-capas.py`, que extrai o atributo `d` do único `<path>`
de cada arquivo e redesenha o glifo dentro da pill de tecnologia.

Cinco deles (`powerbi`, `microsoftsqlserver`, `microsoftexcel`, `css3`,
`powershell`) vêm da versão 9 do catálogo: foram removidos das versões
seguintes por política de marca, não por estarem incorretos.

Só ficam aqui os logos que alguma capa realmente desenha. O gerador corta a
stack em `MAX_TECNOLOGIAS` e descarta o que não couber nas duas linhas, então
logo baixado "por garantia" vira arquivo versionado sem consumidor.

Para acrescentar um logo novo:

```bash
curl -o tools/icones/<slug>.svg \
  https://cdn.jsdelivr.net/npm/simple-icons@13/icons/<slug>.svg
```

Depois registre a cor em `CORES_LOGO`, dentro do gerador, e rode
`python3 tools/gerar-capas.py --check` para confirmar que o logo é usado.

⚠️ **Não use a hex oficial da marca.** O valor de `CORES_LOGO` é um tom afinado
a olho para ficar legível sobre o fundo `#0f1629` das capas, e várias entradas
fogem bastante da cor real: PostgreSQL, Python, CSS3 e Maven foram clareadas,
e as marcas de hex quase preto (Express, JWT, Next.js, JSON) viraram cinza
claro porque desapareciam. Não dá para calcular isso automaticamente: o SVG do
Simple Icons traz só `<title>` e `<path>`, sem a cor da marca.

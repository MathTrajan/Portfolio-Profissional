#!/usr/bin/env python3
"""
Gera as capas SVG dos cards de projeto do portfolio.

O site e single-file e nao tem build: este script NAO roda no deploy. Ele existe
para que as capas possam ser regeradas quando mudar a stack ou a cor de um
projeto, sem precisar redesenhar nada a mao.

Uso:
    python3 tools/gerar-capas.py           # escreve os .svg na raiz
    python3 tools/gerar-capas.py --check   # nao escreve; falha se algo divergir

O --check e o que vale como verificacao: ele refaz as capas em memoria, compara
com o que esta em disco e confere que todo rotulo desenhado existe como
tech-pill no index.html. Sai 1 em qualquer divergencia.

Os logos vem do catalogo Simple Icons, em tools/icones/. Tecnologia sem logo
no catalogo (DAX, Power Query, UI/UX, POO) cai num glifo hexagonal neutro,
para a pill manter a mesma altura e o mesmo alinhamento.
"""

import re
import sys
from functools import lru_cache
from html import escape as escapar
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
ICONES = AQUI / "icones"

# Proporcao 2:1, proxima do card renderizado (355x180). O viewBox e pequeno de
# proposito: o card reduz a capa a 355px de largura, entao cada unidade daqui
# vale ~0,355px na tela. Com viewBox de 1200 o texto das pills caia para 7px e
# ficava ilegivel; em 1000 as fontes abaixo chegam legiveis ao card.
# A margem de 80 absorve o scale(1.1) do hover, que corta ~4,5% de cada lado.
LARGURA, ALTURA = 1000, 500
MARGEM_X = 80

# A capa mostra so as tecnologias principais, e no maximo em duas linhas: o card
# ja repete a stack completa em tech-pill logo abaixo da imagem. O que nao
# couber nas duas linhas e descartado -- capa com densidade desigual entre
# cards vizinhos fica pior do que capa com menos pills.
MAX_TECNOLOGIAS = 5
MAX_LINHAS = 2

# Geometria da pill. Estes quatro numeros sao usados tanto para MEDIR a largura
# quanto para DESENHAR o texto dentro dela; separa-los em dois lugares ja
# desalinhou o texto uma vez.
PILL_ALTURA = 76
PILL_RECUO_TEXTO = 74   # do inicio da pill ate o inicio do texto (cabe o logo)
PILL_FOLGA_DIR = 30
PILL_PASSO_CHAR = 19    # largura estimada por caractere, com textLength
PILL_GAP = 16

# Marca d'agua: o logo da tecnologia principal, grande e discreto.
MARCA_ESCALA = 10.8
MARCA_LADO = 24 * MARCA_ESCALA  # icones Simple Icons sao 24x24
MARCA_FOLGA_DIR = 40

FUNDO = "#0f1629"
SUBTITULO = "#8fa3c8"
MUTED = "#4a5a78"
TEXTO_PILL = "#d9e4f7"

# ATENCAO: estes valores espelham o bloco :root do index.html. SVG carregado por
# <img> vive num documento isolado e NAO enxerga var(--blue), entao a copia e
# estrutural, nao descuido. Mexeu na paleta do site? Rode este script de novo.
PALETA_FUNDO_CARD = "#131928"   # --bg-card
PALETA_AZUL = "#4f8ef7"         # --blue
PALETA_ROXO = "#7c3aed"         # --purple

# Tom de cada logo sobre o fundo #0f1629, afinado a olho -- nao e a hex oficial
# da marca. Varias foram clareadas (PostgreSQL, Python, CSS3, Maven) e as de hex
# quase preto (Express, JWT, Next.js, JSON) foram substituidas por um cinza
# claro, senao desapareciam. Nao da para calcular isso: o SVG do Simple Icons
# traz so <title> e <path>, sem a cor da marca.
CORES_LOGO = {
    "react": "#61DAFB", "typescript": "#3178C6", "nodedotjs": "#5FA04E",
    "express": "#E8EDF5", "sqlite": "#2FA3DE", "tailwindcss": "#06B6D4",
    "springboot": "#6DB33F", "openjdk": "#E76F00", "flyway": "#E04A48",
    "postgresql": "#5B82E8", "docker": "#2496ED", "nextdotjs": "#E8EDF5",
    "prisma": "#7E8CF0", "powerbi": "#F2C811", "microsoftsqlserver": "#E05A58",
    "microsoftexcel": "#3DA06B", "html5": "#E34F26", "css3": "#4A9BE0",
    "javascript": "#F7DF1E", "powershell": "#5391FE", "googledrive": "#4285F4",
    "python": "#5BA2D8", "pandas": "#C9B6F0", "streamlit": "#FF4B4B",
    "apachemaven": "#E0566E", "json": "#C3CCDB",
}

# (arquivo, acento, [(rotulo, slug_do_logo)])
#
# O rotulo TEM de bater com a tech-pill do mesmo card no index.html -- os dois
# aparecem na tela a poucos centimetros um do outro, e o --check cobra isso.
# A primeira tecnologia da lista vira a marca d'agua. slug None = sem logo no
# catalogo Simple Icons.
PROJETOS = [
    ("WR Engenharia.svg", PALETA_AZUL, [
        ("React 18", "react"), ("TypeScript", "typescript"),
        ("Node.js", "nodedotjs"), ("Express", "express"), ("SQLite", "sqlite"),
    ]),
    ("Jarvis Chat AI.svg", "#10b981", [
        ("Node.js", "nodedotjs"), ("Express", "express"),
        ("Groq API", None), ("PostgreSQL", "postgresql"), ("SQLite", "sqlite"),
    ]),
    ("Syntra.svg", "#f59e0b", [
        ("Spring Boot 3.3", "springboot"), ("Java 21", "openjdk"),
        ("PostgreSQL", "postgresql"), ("Flyway", "flyway"),
        ("Docker", "docker"),
    ]),
    ("Norma.svg", PALETA_ROXO, [
        ("Next.js 16", "nextdotjs"), ("TypeScript", "typescript"),
        ("Prisma", "prisma"), ("PostgreSQL", "postgresql"),
        ("Tailwind v4", "tailwindcss"),
    ]),
    ("Dashboard Estratégico Power BI.svg", "#eab308", [
        ("Power BI", "powerbi"), ("SQL Server", "microsoftsqlserver"),
        ("Excel", "microsoftexcel"), ("DAX", None),
    ]),
    ("E-commerce Pró Colchões.svg", "#ef4444", [
        ("HTML5", "html5"), ("CSS3", "css3"),
        ("JavaScript", "javascript"), ("UI/UX", None),
    ]),
    ("Automação de Fluxos Operacionais.svg", "#2dd4bf", [
        ("PowerShell", "powershell"), ("SQL Server", "microsoftsqlserver"),
        ("Excel COM", "microsoftexcel"), ("Google Drive API", "googledrive"),
    ]),
    ("Análise Top 100 Amazon Books.svg", "#a78bfa", [
        ("Python", "python"), ("Pandas", "pandas"), ("Streamlit", "streamlit"),
    ]),
    ("Arquitetura de Backend em Java.svg", "#f87171", [
        ("Java", "openjdk"), ("POO", None),
        ("JSON", "json"), ("Maven", "apachemaven"),
    ]),
]

# Hexagono usado quando a tecnologia nao tem logo no catalogo, desenhado na
# mesma caixa 24x24 dos icones do Simple Icons para alinhar igual.
GLIFO_NEUTRO = ("M12 2.3 20.4 7v10L12 21.7 3.6 17V7L12 2.3Zm0 2.4L5.7 8.2v7.6"
                "L12 19.3l6.3-3.5V8.2L12 4.7Zm0 3.4a3.9 3.9 0 1 1 0 7.8 3.9 "
                "3.9 0 0 1 0-7.8Z")

FONTE = ("Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',"
         "Roboto,Helvetica,Arial,sans-serif")


@lru_cache(maxsize=None)
def carregar_path(slug):
    """
    Extrai o atributo d do unico <path> de um icone Simple Icons.

    Em cache porque icones/ e tabela de consulta imutavel durante a execucao:
    PostgreSQL aparece em 3 capas e a marca d'agua relê o logo que a primeira
    pill ja leu.
    """
    if slug is None:
        return GLIFO_NEUTRO
    conteudo = (ICONES / f"{slug}.svg").read_text(encoding="utf-8")
    achado = re.search(r'\sd="([^"]+)"', conteudo)
    if not achado:
        raise ValueError(f"icone sem atributo d: {slug}.svg")
    return achado.group(1)


def largura_pill(rotulo):
    """
    Largura fixa da pill. O texto e desenhado com textLength, entao a medida
    nao depende da fonte que o navegador conseguir resolver: sem Inter
    instalada o glifo e outro, mas o alinhamento das pills continua o mesmo.
    """
    return PILL_RECUO_TEXTO + len(rotulo) * PILL_PASSO_CHAR + PILL_FOLGA_DIR


def distribuir(techs, largura_util):
    """
    Quebra as pills em ate MAX_LINHAS linhas. O que nao couber e descartado:
    quem precisa da stack inteira le as tech-pill do card, logo abaixo.
    """
    linhas, atual, usado = [], [], 0
    for tech in techs:
        passo = largura_pill(tech[0]) + PILL_GAP
        if atual and usado + passo > largura_util:
            if len(linhas) == MAX_LINHAS - 1:
                return linhas + [atual]  # fecharia uma linha a mais: para aqui
            linhas.append(atual)
            atual, usado = [], 0
        atual.append(tech)
        usado += passo
    return linhas + [atual] if atual else linhas


def selecionar(techs):
    """As tecnologias que realmente cabem na capa, ja quebradas em linhas."""
    return distribuir(techs[:MAX_TECNOLOGIAS], LARGURA - MARGEM_X * 2)


def montar(acento, techs):
    uid = re.sub(r"\W+", "", Path(techs[0][0]).stem)
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{LARGURA}" '
        f'height="{ALTURA}" viewBox="0 0 {LARGURA} {ALTURA}" role="img" '
        f'aria-label="Tecnologias: '
        f'{escapar(", ".join(r for r, _ in techs))}">',
        "<defs>",
        f'<linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{acento}" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="{PALETA_ROXO}" stop-opacity=".08"/>'
        f"</linearGradient>",
        f'<linearGradient id="b{uid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{acento}"/>'
        f'<stop offset="1" stop-color="{PALETA_ROXO}"/></linearGradient>',
        f'<radialGradient id="h{uid}" cx=".18" cy=".12" r=".9">'
        f'<stop offset="0" stop-color="{acento}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{acento}" stop-opacity="0"/>'
        f"</radialGradient>",
        f'<pattern id="p{uid}" width="34" height="34" '
        f'patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.4" fill="{PALETA_AZUL}" '
        f'fill-opacity=".14"/></pattern>',
        "</defs>",
        f'<rect width="{LARGURA}" height="{ALTURA}" fill="{FUNDO}"/>',
    ]
    for camada in (f"p{uid}", f"g{uid}", f"h{uid}"):
        partes.append(
            f'<rect width="{LARGURA}" height="{ALTURA}" fill="url(#{camada})"/>'
        )
    partes.append(f'<rect width="{LARGURA}" height="7" fill="url(#b{uid})"/>')

    # Marca d'agua no lugar onde ficava o titulo. A capa nao traz nome nem tipo
    # do projeto de proposito: o card ja imprime os dois em HTML logo abaixo.
    principal = next((s for _, s in techs if s), None)
    if principal:
        partes.append(
            f'<g transform="translate({LARGURA - MARCA_LADO - MARCA_FOLGA_DIR:.0f},'
            f'{(ALTURA - MARCA_LADO) / 2:.0f}) scale({MARCA_ESCALA})" '
            f'fill="{acento}" fill-opacity=".10">'
            f'<path d="{carregar_path(principal)}"/></g>'
        )

    linhas = selecionar(techs)
    espaco = PILL_ALTURA + 18
    topo = (ALTURA - (len(linhas) * espaco - 18)) // 2
    for indice, linha in enumerate(linhas):
        y = topo + indice * espaco
        x = MARGEM_X
        for rotulo, slug in linha:
            partes.extend(desenhar_pill(x, y, rotulo, slug, acento))
            x += largura_pill(rotulo) + PILL_GAP

    partes.append(
        f'<text x="{LARGURA - MARGEM_X}" y="{ALTURA - 42}" '
        f'font-family="{FONTE}" font-size="30" font-weight="700" '
        f'fill="{MUTED}" text-anchor="end">&lt;/&gt;</text>'
    )
    partes.append("</svg>")
    return "\n".join(partes)


def desenhar_pill(x, y, rotulo, slug, acento):
    """Fundo, logo e texto de uma pill de tecnologia."""
    largura = largura_pill(rotulo)
    return [
        f'<rect x="{x}" y="{y}" width="{largura}" height="{PILL_ALTURA}" '
        f'rx="{PILL_ALTURA // 2}" fill="{PALETA_FUNDO_CARD}" '
        f'fill-opacity=".94" stroke="{acento}" stroke-opacity=".34"/>',
        # Icones Simple Icons sao 24x24; escala 1.6 leva a ~38px, que e a
        # altura otica certa dentro de uma pill de 76px.
        f'<g transform="translate({x + 24},{y + 19}) scale(1.6)" '
        f'fill="{CORES_LOGO.get(slug, SUBTITULO)}">'
        f'<path d="{carregar_path(slug)}"/></g>',
        f'<text x="{x + PILL_RECUO_TEXTO}" y="{y + 50}" '
        f'font-family="{FONTE}" font-size="34" font-weight="600" '
        f'fill="{TEXTO_PILL}" '
        f'textLength="{largura - PILL_RECUO_TEXTO - PILL_FOLGA_DIR}" '
        f'lengthAdjust="spacingAndGlyphs">{escapar(rotulo)}</text>',
    ]


def pills_do_html():
    """Rotulos das tech-pill do index.html, para o --check cruzar."""
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    return {p.strip() for p in re.findall(r'tech-pill">([^<]+)<', html)}


def main():
    checar = "--check" in sys.argv
    do_html = pills_do_html() if checar else set()
    problemas = []

    for nome, acento, techs in PROJETOS:
        svg = montar(acento, techs)
        dados = svg.encode("utf-8")
        destino = RAIZ / nome
        # O que foi REALMENTE desenhado, nao o que foi declarado: o que nao
        # couber nas duas linhas e descartado por distribuir().
        desenhadas = [r for linha in selecionar(techs) for r, _ in linha]
        descartadas = len(techs) - len(desenhadas)
        resumo = (f"{nome}: {len(dados):,} bytes, {len(desenhadas)} pills"
                  + (f" ({descartadas} nao couberam)" if descartadas else ""))
        print(resumo)

        if not checar:
            destino.write_text(svg, encoding="utf-8")
            continue
        if not destino.exists():
            problemas.append(f"{nome}: nao existe em disco")
        elif destino.read_text(encoding="utf-8") != svg:
            problemas.append(f"{nome}: disco difere do gerado, rode sem --check")
        for rotulo in desenhadas:
            if rotulo not in do_html:
                problemas.append(
                    f"{nome}: pill '{rotulo}' nao existe como tech-pill "
                    f"no index.html"
                )

    if problemas:
        print("\nDIVERGENCIAS:", file=sys.stderr)
        for problema in problemas:
            print(f"  - {problema}", file=sys.stderr)
        sys.exit(1)
    if checar:
        print("\nok: capas em dia e rotulos batendo com o index.html")


if __name__ == "__main__":
    main()

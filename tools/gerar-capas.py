#!/usr/bin/env python3
"""
Gera as capas SVG dos cards de projeto do portfolio.

O site e single-file e nao tem build: este script NAO roda no deploy. Ele existe
para que as capas possam ser regeradas quando mudar o nome, a descricao ou a
stack de um projeto, sem precisar redesenhar nada a mao.

Uso:
    python3 tools/gerar-capas.py          # escreve os .svg na raiz do projeto
    python3 tools/gerar-capas.py --check  # so valida, nao escreve

Os logos vem do catalogo Simple Icons, baixados uma vez para tools/icones/.
Tecnologia sem logo no catalogo (Groq, DAX, Power Query, UI/UX, POO) cai num
glifo hexagonal neutro, para a pill continuar com a mesma altura e alinhamento.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ICONES = Path(__file__).resolve().parent / "icones"

# Proporcao 2:1, proxima do card renderizado (355x180). O viewBox e pequeno de
# proposito: o card reduz a capa a 355px de largura, entao cada unidade daqui
# vale ~0,355px na tela. Com viewBox de 1200 o texto das pills caia para 7px e
# ficava ilegivel; em 1000 as fontes abaixo chegam legiveis ao card.
# A margem de 80px absorve o scale(1.1) do hover, que corta ~4,5% de cada lado.
LARGURA, ALTURA = 1000, 500
MARGEM_X, SAFE_TOPO = 80, 40

# A capa mostra so as tecnologias principais: o card ja repete a stack completa
# em tech-pill logo abaixo da imagem, e passar disso espreme o texto.
MAX_TECNOLOGIAS = 5

FUNDO = "#0f1629"
TITULO = "#f0f4ff"
SUBTITULO = "#8fa3c8"
MUTED = "#4a5a78"

# Cor de cada logo. Marcas de hex muito escuro (Express, JWT, Next.js, Prisma,
# Pandas, JSON) recebem um tom claro, senao somem no fundo #0f1629.
CORES_LOGO = {
    "react": "#61DAFB", "typescript": "#3178C6", "nodedotjs": "#5FA04E",
    "express": "#E8EDF5", "sqlite": "#2FA3DE", "tailwindcss": "#06B6D4",
    "jsonwebtokens": "#E8EDF5", "vite": "#8A7FFF", "springboot": "#6DB33F",
    "openjdk": "#E76F00", "hibernate": "#B9A26B", "flyway": "#E04A48",
    "postgresql": "#5B82E8", "thymeleaf": "#4CAF50", "docker": "#2496ED",
    "nextdotjs": "#E8EDF5", "prisma": "#7E8CF0", "framer": "#3D7BFF",
    "powerbi": "#F2C811", "microsoftsqlserver": "#E05A58",
    "microsoftexcel": "#3DA06B", "html5": "#E34F26", "css3": "#4A9BE0",
    "javascript": "#F7DF1E", "powershell": "#5391FE", "googledrive": "#4285F4",
    "python": "#5BA2D8", "pandas": "#C9B6F0", "streamlit": "#FF4B4B",
    "apachemaven": "#E0566E", "json": "#C3CCDB",
}

# (eyebrow, titulo, subtitulo, acento, [(rotulo, slug_do_logo)])
# slug None = sem logo no catalogo Simple Icons.
PROJETOS = [
    ("WR Engenharia.svg", "Full Stack · Sistema de Gestão",
     "WR Engenharia", "Gestão de Obras", "#4f8ef7", [
         ("React 18", "react"), ("TypeScript", "typescript"),
         ("Node.js", "nodedotjs"), ("Express", "express"),
         ("SQLite", "sqlite"), ("Tailwind", "tailwindcss"),
         ("JWT", "jsonwebtokens"), ("Vite", "vite"),
     ]),
    ("Jarvis Chat AI.svg", "IA & Observabilidade",
     "Jarvis", "Agente de Observabilidade", "#10b981", [
         ("Node.js", "nodedotjs"), ("Express", "express"),
         ("Groq LLaMA", None), ("PostgreSQL", "postgresql"),
         ("SQLite", "sqlite"), ("Vercel", "vercel"),
     ]),
    ("Syntra.svg", "Full Stack · CRM B2B",
     "Syntra", "CRM de Leads", "#f59e0b", [
         ("Spring Boot", "springboot"), ("Java 21", "openjdk"),
         ("PostgreSQL", "postgresql"), ("Flyway", "flyway"),
         ("Docker", "docker"), ("JPA", "hibernate"),
         ("Thymeleaf", "thymeleaf"),
     ]),
    ("Norma.svg", "Full Stack & SaaS",
     "Norma", "Sistema de Gestão Jurídica", "#7c3aed", [
         ("Next.js 16", "nextdotjs"), ("TypeScript", "typescript"),
         ("Prisma", "prisma"), ("PostgreSQL", "postgresql"),
         ("Tailwind", "tailwindcss"), ("Framer Motion", "framer"),
     ]),
    ("Dashboard Estratégico Power BI.svg", "Business Intelligence",
     "Dashboard Estratégico", "Painéis gerenciais e KPIs", "#eab308", [
         ("Power BI", "powerbi"), ("SQL Server", "microsoftsqlserver"),
         ("Excel", "microsoftexcel"), ("DAX", None),
     ]),
    ("E-commerce Pró Colchões.svg", "Frontend & B2B Platform",
     "Pró Colchões", "Portal e catálogo B2B", "#ef4444", [
         ("HTML5", "html5"), ("CSS3", "css3"),
         ("JavaScript", "javascript"), ("UI/UX", None),
     ]),
    ("Automação de Fluxos Operacionais.svg", "Automação & API",
     "Automação de Fluxos", "ETL no ERP Protheus", "#2dd4bf", [
         ("PowerShell", "powershell"), ("SQL Server", "microsoftsqlserver"),
         ("Excel COM", "microsoftexcel"), ("Google Drive", "googledrive"),
         ("Power Query", None),
     ]),
    ("Análise Top 100 Amazon Books.svg", "Data Science & Python",
     "Top 100 Amazon Books", "Análise exploratória e dashboard", "#a78bfa", [
         ("Python", "python"), ("Pandas", "pandas"), ("Streamlit", "streamlit"),
     ]),
    ("Arquitetura de Backend em Java.svg", "Estudo · Backend & POO",
     "Fundamentos em Java", "Orientação a objetos e Maven", "#f87171", [
         ("Java", "openjdk"), ("Maven", "apachemaven"),
         ("JSON", "json"), ("POO", None),
     ]),
]

# Hexagono usado quando a tecnologia nao tem logo no catalogo, desenhado na
# mesma caixa 24x24 dos icones do Simple Icons para alinhar igual.
GLIFO_NEUTRO = ("M12 2.3 20.4 7v10L12 21.7 3.6 17V7L12 2.3Zm0 2.4L5.7 8.2v7.6"
                "L12 19.3l6.3-3.5V8.2L12 4.7Zm0 3.4a3.9 3.9 0 1 1 0 7.8 3.9 "
                "3.9 0 0 1 0-7.8Z")

ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}


def escapar(texto):
    for bruto, entidade in ESCAPES.items():
        texto = texto.replace(bruto, entidade)
    return texto


def carregar_path(slug):
    """Extrai o atributo d do unico <path> de um icone Simple Icons."""
    if slug is None:
        return GLIFO_NEUTRO
    arquivo = ICONES / f"{slug}.svg"
    if not arquivo.exists():
        raise FileNotFoundError(f"logo ausente: {arquivo}")
    achado = re.search(r'\sd="([^"]+)"', arquivo.read_text(encoding="utf-8"))
    if not achado:
        raise ValueError(f"sem atributo d: {arquivo}")
    return achado.group(1)


def largura_pill(rotulo):
    """
    Largura fixa da pill. O texto e desenhado com textLength, entao a medida
    nao depende da fonte que o navegador conseguir resolver: sem Inter
    instalada o glifo e outro, mas o alinhamento das pills continua o mesmo.
    """
    return 74 + len(rotulo) * 19 + 30


def distribuir(techs, largura_util):
    """Quebra as pills em linhas que caibam na largura util."""
    linhas, atual, usado = [], [], 0
    for tech in techs:
        passo = largura_pill(tech[0]) + 14
        if atual and usado + passo > largura_util:
            linhas.append(atual)
            atual, usado = [], 0
        atual.append(tech)
        usado += passo
        if len(linhas) == 2:  # nao cabe uma terceira linha em 500 de altura
            break
    if atual:
        linhas.append(atual)
    return linhas


def montar(eyebrow, titulo, subtitulo, acento, techs):
    uid = re.sub(r"\W+", "", titulo) or "capa"
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{LARGURA}" height="{ALTURA}" '
        f'viewBox="0 0 {LARGURA} {ALTURA}" role="img" '
        f'aria-label="{escapar(titulo)}: {escapar(subtitulo)}">',
        "<defs>",
        f'<linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{acento}" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="#7c3aed" stop-opacity=".08"/>'
        f"</linearGradient>",
        f'<linearGradient id="b{uid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{acento}"/>'
        f'<stop offset="1" stop-color="#7c3aed"/></linearGradient>',
        f'<radialGradient id="h{uid}" cx=".18" cy=".12" r=".9">'
        f'<stop offset="0" stop-color="{acento}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{acento}" stop-opacity="0"/>'
        f"</radialGradient>",
        f'<pattern id="p{uid}" width="34" height="34" '
        f'patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.4" fill="#4f8ef7" fill-opacity=".14"/>'
        f"</pattern>",
        "</defs>",
        f'<rect width="{LARGURA}" height="{ALTURA}" fill="{FUNDO}"/>',
        f'<rect width="{LARGURA}" height="{ALTURA}" fill="url(#p{uid})"/>',
        f'<rect width="{LARGURA}" height="{ALTURA}" fill="url(#g{uid})"/>',
        f'<rect width="{LARGURA}" height="{ALTURA}" fill="url(#h{uid})"/>',
        f'<rect width="{LARGURA}" height="7" fill="url(#b{uid})"/>',
    ]

    fonte = ("Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',"
             "Roboto,Helvetica,Arial,sans-serif")
    texto = f'font-family="{fonte}"'

    # Marca d'agua: o logo da tecnologia principal, grande e discreto. Fica no
    # lugar do titulo, que foi removido de proposito -- o card ja imprime nome,
    # tipo e descricao em HTML logo abaixo da capa, e repetir aqui duplicava o
    # mesmo texto duas vezes na mesma altura da tela.
    principal = next((s for _, s in techs if s), None)
    if principal:
        partes.append(
            f'<g transform="translate({LARGURA - 300},{ALTURA // 2 - 130}) '
            f'scale(10.8)" fill="{acento}" fill-opacity=".10">'
            f'<path d="{carregar_path(principal)}"/></g>'
        )

    linhas = distribuir(techs[:MAX_TECNOLOGIAS], LARGURA - MARGEM_X * 2)
    altura_pill = 76
    espaco = altura_pill + 18
    # Bloco de pills centralizado na vertical, com 1 ou 2 linhas.
    topo = (ALTURA - (len(linhas) * espaco - 18)) // 2
    for indice, linha in enumerate(linhas):
        y = topo + indice * espaco
        x = MARGEM_X
        for rotulo, slug in linha:
            largura = largura_pill(rotulo)
            cor = CORES_LOGO.get(slug, SUBTITULO) if slug else SUBTITULO
            partes.append(
                f'<rect x="{x}" y="{y}" width="{largura}" '
                f'height="{altura_pill}" rx="{altura_pill // 2}" '
                f'fill="#131928" fill-opacity=".94" stroke="{acento}" '
                f'stroke-opacity=".34"/>'
            )
            # Icones Simple Icons sao 24x24; escala 1.6 leva a ~38px, que e a
            # altura otica certa dentro de uma pill de 76px.
            partes.append(
                f'<g transform="translate({x + 24},{y + 19}) scale(1.6)" '
                f'fill="{cor}"><path d="{carregar_path(slug)}"/></g>'
            )
            partes.append(
                f'<text x="{x + 74}" y="{y + 50}" {texto} font-size="34" '
                f'font-weight="600" fill="#d9e4f7" '
                f'textLength="{largura - 74 - 30}" '
                f'lengthAdjust="spacingAndGlyphs">{escapar(rotulo)}</text>'
            )
            x += largura + 16

    partes.append(
        f'<text x="{LARGURA - MARGEM_X}" y="{ALTURA - 42}" {texto} '
        f'font-size="30" font-weight="700" fill="{MUTED}" '
        f'text-anchor="end">&lt;/&gt;</text>'
    )
    partes.append("</svg>")
    return "\n".join(partes)


def main():
    checar = "--check" in sys.argv
    for nome, eyebrow, titulo, subtitulo, acento, techs in PROJETOS:
        svg = montar(eyebrow, titulo, subtitulo, acento, techs)
        if checar:
            print(f"{nome}: {len(svg)} bytes, {len(techs)} tecnologias")
            continue
        destino = RAIZ / nome
        destino.write_text(svg, encoding="utf-8")
        print(f"{destino.name}: {len(svg.encode('utf-8')):,} bytes")


if __name__ == "__main__":
    main()

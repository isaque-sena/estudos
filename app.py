import streamlit as st
import sqlite3
import os
import math
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Tracker — Isaque Sena",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Banco ─────────────────────────────────────────────────────────────────
DB_PATH = "progresso.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progresso (
            id TEXT PRIMARY KEY,
            area TEXT, secao TEXT, topico TEXT,
            concluido INTEGER DEFAULT 0,
            atualizado_em TEXT
        )
    """)
    # Tabela de revisão espaçada (SM-2)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS revisao (
            id TEXT PRIMARY KEY,
            materia TEXT,
            topico TEXT,
            proxima_revisao TEXT,
            intervalo INTEGER DEFAULT 1,
            facilidade REAL DEFAULT 2.5,
            repeticoes INTEGER DEFAULT 0,
            ultima_nota INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def load_progress():
    conn = get_conn()
    rows = conn.execute("SELECT id, concluido FROM progresso").fetchall()
    conn.close()
    return {r[0]: bool(r[1]) for r in rows}

def save_topic(key, area, secao, topico, concluido):
    conn = get_conn()
    conn.execute("""
        INSERT INTO progresso (id,area,secao,topico,concluido,atualizado_em)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            concluido=excluded.concluido,
            atualizado_em=excluded.atualizado_em
    """, (key, area, secao, topico, int(concluido), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def reset_progress():
    conn = get_conn()
    conn.execute("DELETE FROM progresso")
    conn.execute("DELETE FROM revisao")
    conn.commit()
    conn.close()

def export_csv():
    conn = get_conn()
    rows = conn.execute(
        "SELECT area,secao,topico,concluido,atualizado_em FROM progresso ORDER BY area,secao"
    ).fetchall()
    conn.close()
    lines = ["area,secao,topico,concluido,atualizado_em"]
    for r in rows:
        lines.append(f'"{r[0]}","{r[1]}","{r[2]}","{"Sim" if r[3] else "Nao"}","{r[4] or ""}"')
    return "\n".join(lines)

# ── SM-2 Algorithm ────────────────────────────────────────────────────────
def sm2_update(intervalo, facilidade, repeticoes, nota):
    """
    nota: 0=Nao lembro, 1=Dificil, 2=Medio, 3=Facil
    Mapeia para qualidade SM-2: 0→1, 1→2, 2→4, 3→5
    """
    qualidade = [1, 2, 4, 5][nota]

    if qualidade < 3:
        repeticoes = 0
        intervalo = 1
    else:
        if repeticoes == 0:
            intervalo = 1
        elif repeticoes == 1:
            intervalo = 6
        else:
            intervalo = math.ceil(intervalo * facilidade)
        repeticoes += 1

    facilidade = max(1.3, facilidade + 0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
    proxima = (date.today() + timedelta(days=intervalo)).isoformat()
    return intervalo, facilidade, repeticoes, proxima

def get_revisao_data():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM revisao").fetchall()
    conn.close()
    data = {}
    for r in rows:
        data[r[0]] = {
            "materia": r[1], "topico": r[2],
            "proxima_revisao": r[3], "intervalo": r[4],
            "facilidade": r[5], "repeticoes": r[6], "ultima_nota": r[7]
        }
    return data

def save_revisao(key, materia, topico, intervalo, facilidade, repeticoes, proxima, nota):
    conn = get_conn()
    conn.execute("""
        INSERT INTO revisao (id,materia,topico,proxima_revisao,intervalo,facilidade,repeticoes,ultima_nota)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            proxima_revisao=excluded.proxima_revisao,
            intervalo=excluded.intervalo,
            facilidade=excluded.facilidade,
            repeticoes=excluded.repeticoes,
            ultima_nota=excluded.ultima_nota
    """, (key, materia, topico, proxima, intervalo, facilidade, repeticoes, nota))
    conn.commit()
    conn.close()

def get_due_today(revisao_data):
    hoje = date.today().isoformat()
    return {k: v for k, v in revisao_data.items()
            if v["proxima_revisao"] <= hoje}

def adicionar_revisao(key, materia, topico):
    """Adiciona tópico na fila de revisão quando marcado como concluído"""
    conn = get_conn()
    existing = conn.execute("SELECT id FROM revisao WHERE id=?", (key,)).fetchone()
    if not existing:
        proxima = date.today().isoformat()
        conn.execute("""
            INSERT INTO revisao (id,materia,topico,proxima_revisao,intervalo,facilidade,repeticoes,ultima_nota)
            VALUES (?,?,?,?,1,2.5,0,0)
        """, (key, materia, topico, proxima))
        conn.commit()
    conn.close()

# ── Currículo ─────────────────────────────────────────────────────────────
PROG = {
    "Python": {
        "icon": "🐍", "color": "#2e7d32",
        "sections": {
            "Projeto 1 — Analisador de Gastos": [
                "pandas — leitura de CSV",
                "pandas — groupby e agrupamento",
                "pandas — filtros e selecao",
                "matplotlib — grafico de barras",
                "matplotlib — grafico de pizza",
                "f-strings e formatacao de numeros",
                "tratamento de erros basico",
            ],
            "Projeto 2 — Buscador de Vagas": [
                "requests — chamadas HTTP",
                "BeautifulSoup — parsing HTML",
                "manipulacao de dicionarios",
                "salvamento em CSV",
                "try/except para erros de rede",
                "loops e filtragem de dados",
            ],
            "Projeto 3 — Dashboard BACEN/IBGE": [
                "requests — consumir APIs REST",
                "pandas — JSON para DataFrame",
                "Streamlit — estrutura basica",
                "Streamlit — sidebar e filtros",
                "plotly — graficos interativos",
                "st.cache_data",
            ],
            "Projeto 4 — ETL de Planilha": [
                "pandas — leitura de Excel openpyxl",
                "pandas — limpeza de strings",
                "pandas — remocao de duplicatas",
                "pandas — tratamento de nulos",
                "pandas — exportar para Excel",
                "funcoes reutilizaveis",
            ],
            "Projeto 5 — Relatorio PDF": [
                "pandas — calculo de metricas",
                "reportlab — criacao de PDF",
                "matplotlib — salvar como imagem",
                "automacao de documentos",
                "formatacao de tabelas em PDF",
            ],
            "Projeto 6 — Pipeline com Banco": [
                "SQLAlchemy — conexao com banco",
                "SQLite — banco local",
                "schedule — agendamento",
                "SQL INSERT SELECT UPDATE",
                "conceitos de pipeline",
            ],
            "Projeto 7 — Dashboard B3": [
                "yfinance — dados de acoes",
                "pandas — medias moveis",
                "plotly — candlestick chart",
                "Streamlit — layout avancado",
                "selecao dinamica de ativos",
            ],
        },
    },
    "C — Logica": {
        "icon": "⚙️", "color": "#1565c0",
        "sections": {
            "Modulo 1 — Fundamentos": [
                "variaveis e tipos int float char",
                "sizeof e tamanho na memoria",
                "operadores aritmeticos",
                "operadores de comparacao",
                "operadores logicos AND OR NOT",
                "printf e scanf",
                "compilacao com gcc",
            ],
            "Modulo 2 — Controle de Fluxo": [
                "if else if else",
                "operador ternario",
                "switch case",
                "for com contador",
                "while e do while",
                "break e continue",
            ],
            "Modulo 3 — Funcoes": [
                "declaracao e definicao",
                "parametros e tipos de retorno",
                "void sem retorno",
                "escopo de variaveis",
                "recursao fatorial",
                "recursao fibonacci",
                "prototipos de funcao",
            ],
            "Modulo 4 — Arrays": [
                "declaracao de arrays",
                "acesso por indice",
                "percorrer com for",
                "arrays em funcoes",
                "strings char[]",
                "strlen strcpy",
                "matrizes 2D",
            ],
            "Modulo 5 — Ponteiros": [
                "o que e um ponteiro",
                "operadores & e *",
                "ponteiro e array",
                "passagem por referencia",
                "aritmetica de ponteiros",
                "malloc e free",
            ],
            "Modulo 6 — Structs e Algoritmos": [
                "struct definicao e uso",
                "array de structs",
                "busca linear",
                "busca binaria",
                "bubble sort",
                "selection sort",
                "insertion sort",
            ],
        },
    },
    "SQL": {
        "icon": "🗄️", "color": "#6a1b9a",
        "sections": {
            "SQL Basico": [
                "SELECT e FROM",
                "WHERE filtros",
                "ORDER BY",
                "LIMIT",
                "DISTINCT",
                "AND OR NOT",
                "LIKE padrao",
            ],
            "SQL Intermediario": [
                "GROUP BY agrupamento",
                "HAVING filtro pos-grupo",
                "COUNT SUM AVG MAX MIN",
                "INNER JOIN",
                "LEFT JOIN",
                "subqueries",
                "CREATE TABLE e tipos",
            ],
        },
    },
    "Power BI": {
        "icon": "📊", "color": "#c62828",
        "sections": {
            "Power BI Essencial": [
                "importar CSV e Excel",
                "Power Query limpeza",
                "relacionamentos entre tabelas",
                "DAX SUM COUNT AVERAGE",
                "DAX CALCULATE e filtros",
                "DAX RELATED e LOOKUPVALUE",
                "visuais barras linha pizza",
                "filtros e segmentacoes",
                "publicar no Power BI Service",
            ],
        },
    },
}

ENEM = {
    "Matematica": {
        "icon": "📐", "color": "#1565c0",
        "topics": [
            "Porcentagem e regra de tres",
            "Equacoes de 1 grau",
            "Equacoes de 2 grau",
            "Sistemas de equacoes",
            "Funcao afim",
            "Funcao quadratica",
            "Funcao exponencial",
            "Geometria area e perimetro",
            "Geometria volume",
            "Trigonometria",
            "Estatistica e probabilidade",
            "Juros simples",
            "Juros compostos",
        ],
    },
    "Fisica": {
        "icon": "⚡", "color": "#e65100",
        "topics": [
            "Mecanica movimento e velocidade",
            "Leis de Newton",
            "Trabalho e energia",
            "Termodinamica calor e temperatura",
            "Optica reflexao e refracao",
            "Eletricidade corrente e resistencia",
            "Ondas e som",
            "Fisica Moderna",
        ],
    },
    "Quimica": {
        "icon": "🧪", "color": "#2e7d32",
        "topics": [
            "Estrutura atomica e tabela periodica",
            "Ligacoes quimicas",
            "Quimica Organica funcoes e reacoes",
            "Acidos bases e sais",
            "Estequiometria e mol",
            "Termoquimica",
            "Quimica Ambiental",
        ],
    },
    "Biologia": {
        "icon": "🧬", "color": "#00695c",
        "topics": [
            "Citologia celulas e organelas",
            "Genetica leis de Mendel",
            "Ecologia cadeias alimentares",
            "Fisiologia Humana",
            "Evolucao selecao natural",
            "Microbiologia virus e bacterias",
            "Botanica fotossintese",
        ],
    },
    "Historia": {
        "icon": "🏛️", "color": "#4a148c",
        "topics": [
            "Antiguidade e Idade Media",
            "Revolucoes Industrial Francesa Americana",
            "Colonizacao do Brasil",
            "Imperio e Republica no Brasil",
            "Guerras Mundiais",
            "Guerra Fria",
            "Movimentos Sociais",
        ],
    },
    "Geografia": {
        "icon": "🌍", "color": "#004d40",
        "topics": [
            "Clima relevo e vegetacao",
            "Urbanizacao e migracoes",
            "Geopolitica e blocos economicos",
            "Sustentabilidade e ODS",
            "Cartografia e mapas",
            "Regioes do Brasil",
        ],
    },
    "Portugues": {
        "icon": "📖", "color": "#880e4f",
        "topics": [
            "Gramatica ortografia e concordancia",
            "Interpretacao de textos",
            "Literatura movimentos literarios",
            "Generos textuais",
            "Figuras de linguagem",
        ],
    },
    "Redacao": {
        "icon": "✍️", "color": "#37474f",
        "topics": [
            "Estrutura da redacao ENEM",
            "Coerencia e coesao",
            "Argumentacao e proposta de intervencao",
            "Temas meio ambiente",
            "Temas saude e educacao",
            "Pratica semanal de redacao",
        ],
    },
    "Ingles e Espanhol": {
        "icon": "🌐", "color": "#1a237e",
        "topics": [
            "Interpretacao de textos em ingles",
            "Gramatica basica ingles",
            "Interpretacao de textos em espanhol",
        ],
    },
}

def make_key(area, secao, topico):
    return f"{area}||{secao}||{topico}"

def make_enem_key(materia, topico):
    return f"ENEM||{materia}||{topico}"

# ── Init ──────────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()
if "revisao_data" not in st.session_state:
    st.session_state.revisao_data = get_revisao_data()
if "revisao_atual" not in st.session_state:
    st.session_state.revisao_atual = None

progress = st.session_state.progress
revisao_data = st.session_state.revisao_data

# ── Stats ─────────────────────────────────────────────────────────────────
def prog_stats():
    total = sum(len(t) for a in PROG.values() for t in a["sections"].values())
    done  = sum(
        1 for an, ad in PROG.items()
        for sn, topics in ad["sections"].items()
        for t in topics
        if progress.get(make_key(an, sn, t), False)
    )
    return done, total

def enem_stats():
    total = sum(len(m["topics"]) for m in ENEM.values())
    done  = sum(
        1 for mn, md in ENEM.items()
        for t in md["topics"]
        if progress.get(make_enem_key(mn, t), False)
    )
    return done, total

def materia_stats(mn, md):
    total = len(md["topics"])
    done  = sum(1 for t in md["topics"] if progress.get(make_enem_key(mn, t), False))
    return done, total

def area_stats(an, ad):
    total = sum(len(t) for t in ad["sections"].values())
    done  = sum(
        1 for sn, topics in ad["sections"].items()
        for t in topics if progress.get(make_key(an, sn, t), False)
    )
    return done, total

done_prog, total_prog = prog_stats()
done_enem, total_enem = enem_stats()
pct_prog = round(done_prog / total_prog * 100, 1) if total_prog else 0
pct_enem = round(done_enem / total_enem * 100, 1) if total_enem else 0
due_today = get_due_today(revisao_data)
total_revisao = len([k for k, v in revisao_data.items()])

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@600;700&display=swap');

html, body, [class*="css"], p, span, label, div {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
.stApp { background: #f8f9fa; }
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e9ecef !important;
}
.page-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 22px !important;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 2px;
}
.page-sub {
    font-size: 11px !important;
    color: #adb5bd;
    letter-spacing: 0.08em;
    margin-bottom: 20px;
}
.kpi {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.kpi-num {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 24px !important;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 3px;
}
.kpi-lbl {
    font-size: 10px !important;
    color: #adb5bd;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.prog-card {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 10px;
}
.prog-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600;
    color: #212529;
    margin-bottom: 6px;
}
.prog-sub { font-size: 11px !important; color: #adb5bd; margin-bottom: 8px; }
.sec-label {
    font-size: 10px !important;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #868e96;
    border-left: 3px solid #e9ecef;
    padding-left: 8px;
    margin: 16px 0 6px;
}
div[data-testid="stCheckbox"] {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 5px 10px;
    margin-bottom: 3px;
}
div[data-testid="stCheckbox"]:hover {
    border-color: #ced4da;
    background: #f8f9fa;
}
div[data-testid="stCheckbox"] label p {
    font-size: 12px !important;
    color: #495057 !important;
}
.stProgress > div > div {
    background: #e9ecef !important;
    border-radius: 4px !important;
    height: 5px !important;
}
.stProgress > div > div > div {
    border-radius: 4px !important;
    height: 5px !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #868e96 !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 6px 12px !important;
}
.stTabs [aria-selected="true"] {
    background: #f1f3f5 !important;
    color: #212529 !important;
}

/* Cartão de revisão */
.rev-card {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 12px;
    padding: 28px 32px;
    text-align: center;
    max-width: 560px;
    margin: 0 auto;
}
.rev-materia {
    font-size: 11px !important;
    color: #adb5bd;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.rev-topico {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 18px !important;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 6px;
    line-height: 1.3;
}
.rev-intervalo {
    font-size: 11px !important;
    color: #adb5bd;
    margin-bottom: 24px;
}
.badge-due {
    background: #fff3cd;
    border: 1px solid #ffc107;
    color: #856404;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px !important;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 10px;
}
.badge-ok {
    background: #d1e7dd;
    border: 1px solid #198754;
    color: #0f5132;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px !important;
    font-weight: 600;
    display: inline-block;
}
.stDownloadButton button, button[kind="secondary"] {
    font-size: 12px !important;
    border-radius: 6px !important;
    background: #fff !important;
    border: 1px solid #e9ecef !important;
    color: #495057 !important;
}
.sidebar-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700;
    color: #1a1a2e;
}
.sidebar-sub { font-size: 10px !important; color: #adb5bd; letter-spacing: 0.08em; }
hr { border-color: #e9ecef !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 16px">
        <div class="sidebar-title">🧠 Tracker de Estudos</div>
        <div class="sidebar-sub">ISAQUE SENA · SENALABS</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Revisão pendente
    if due_today:
        st.markdown(f"""
        <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;
                    padding:10px 14px;margin-bottom:12px">
            <div style="font-size:12px!important;font-weight:600;color:#856404">
                🔁 {len(due_today)} revisão(ões) pendente(s) hoje
            </div>
            <div style="font-size:11px!important;color:#856404;margin-top:2px">
                Vá para a aba Revisão ENEM
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Prog programação
    st.markdown(f"""
    <div class="prog-card">
        <div class="prog-title">💻 Programação</div>
        <div class="prog-sub">{done_prog} de {total_prog} tópicos · {pct_prog}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct_prog / 100)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    for an, ad in PROG.items():
        d, t = area_stats(an, ad)
        p = round(d / t * 100) if t else 0
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:6px 10px;background:#f8f9fa;border-radius:6px;
                    border:1px solid #e9ecef;margin-bottom:4px">
            <span style="font-size:12px!important;color:#495057">{ad['icon']} {an}</span>
            <span style="font-size:11px!important;color:#adb5bd">{d}/{t}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Prog ENEM
    st.markdown(f"""
    <div class="prog-card">
        <div class="prog-title">📚 ENEM 2026</div>
        <div class="prog-sub">{done_enem} de {total_enem} tópicos · {pct_enem}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct_enem / 100)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    for mn, md in ENEM.items():
        d, t = materia_stats(mn, md)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:6px 10px;background:#f8f9fa;border-radius:6px;
                    border:1px solid #e9ecef;margin-bottom:4px">
            <span style="font-size:12px!important;color:#495057">{md['icon']} {mn}</span>
            <span style="font-size:11px!important;color:#adb5bd">{d}/{t}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.download_button(
        "⬇️ Exportar CSV",
        data=export_csv(),
        file_name=f"progresso_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Resetar progresso", use_container_width=True, type="secondary"):
        reset_progress()
        st.session_state.progress = {}
        st.session_state.revisao_data = {}
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-title">Trilha de Estudos</div>
<div class="page-sub">MARQUE O QUE JÁ ESTUDOU · SALVO AUTOMATICAMENTE</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
for col, num, lbl, cor in [
    (c1, f"{pct_prog}%",  "PROG. PROG.",   "#1565c0"),
    (c2, done_prog,       "CONCLUÍDOS",    "#2e7d32"),
    (c3, total_prog - done_prog, "RESTANTES", "#c62828"),
    (c4, f"{pct_enem}%", "PROG. ENEM",    "#4a148c"),
    (c5, done_enem,       "CONCLUÍDOS",    "#2e7d32"),
    (c6, total_enem - done_enem, "RESTANTES", "#c62828"),
    (c7, len(due_today),  "REVISAR HOJE",  "#e65100"),
]:
    with col:
        st.markdown(f"""
        <div class="kpi">
            <div class="kpi-num" style="color:{cor}">{num}</div>
            <div class="kpi-lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────
rev_label = f"🔁 Revisão ENEM {'🔴' if due_today else ''}"
tab_prog, tab_enem, tab_rev = st.tabs(["💻 Programação", "📚 ENEM 2026", rev_label])

# ─────────────────────────────────────────────────────────────────────────
# ABA PROGRAMAÇÃO
# ─────────────────────────────────────────────────────────────────────────
with tab_prog:
    subtabs = st.tabs([f"{v['icon']} {k}" for k, v in PROG.items()])
    for subtab, (an, ad) in zip(subtabs, PROG.items()):
        with subtab:
            d_a, t_a = area_stats(an, ad)
            p_a = round(d_a / t_a * 100, 1) if t_a else 0
            col_l, col_r = st.columns([1, 4])
            with col_l:
                st.markdown(f"""
                <div class="kpi" style="text-align:left">
                    <div class="kpi-num" style="color:{ad['color']}">{p_a}%</div>
                    <div class="kpi-lbl">{d_a}/{t_a} tópicos</div>
                </div>
                """, unsafe_allow_html=True)
            with col_r:
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                st.progress(p_a / 100)
            for sn, topics in ad["sections"].items():
                d_s = sum(1 for t in topics if progress.get(make_key(an, sn, t), False))
                st.markdown(f'<div class="sec-label">{sn} — {d_s}/{len(topics)}</div>', unsafe_allow_html=True)
                for topic in topics:
                    key = make_key(an, sn, topic)
                    cur = progress.get(key, False)
                    chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                    if chk != cur:
                        progress[key] = chk
                        save_topic(key, an, sn, topic, chk)
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────
# ABA ENEM
# ─────────────────────────────────────────────────────────────────────────
with tab_enem:
    mat_tabs = st.tabs([f"{v['icon']} {k}" for k, v in ENEM.items()])
    for mat_tab, (mn, md) in zip(mat_tabs, ENEM.items()):
        with mat_tab:
            d_m, t_m = materia_stats(mn, md)
            p_m = round(d_m / t_m * 100, 1) if t_m else 0
            col_l, col_r = st.columns([1, 4])
            with col_l:
                st.markdown(f"""
                <div class="kpi" style="text-align:left">
                    <div class="kpi-num" style="color:{md['color']}">{p_m}%</div>
                    <div class="kpi-lbl">{d_m}/{t_m} tópicos</div>
                </div>
                """, unsafe_allow_html=True)
            with col_r:
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                st.progress(p_m / 100)
            st.markdown(f'<div class="sec-label">{md["icon"]} {mn}</div>', unsafe_allow_html=True)
            for topic in md["topics"]:
                key = make_enem_key(mn, topic)
                cur = progress.get(key, False)
                chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                if chk != cur:
                    progress[key] = chk
                    save_topic(key, "ENEM", mn, topic, chk)
                    # Ao marcar como concluído, entra na fila de revisão
                    if chk:
                        adicionar_revisao(key, mn, topic)
                        st.session_state.revisao_data = get_revisao_data()
                    st.rerun()

# ─────────────────────────────────────────────────────────────────────────
# ABA REVISÃO ENEM — SM-2
# ─────────────────────────────────────────────────────────────────────────
with tab_rev:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    revisao_data = st.session_state.revisao_data
    due_today = get_due_today(revisao_data)
    due_list = list(due_today.items())

    # Resumo por matéria
    resumo_cols = st.columns(len(ENEM))
    for col, (mn, md) in zip(resumo_cols, ENEM.items()):
        total_m = sum(1 for k, v in revisao_data.items() if v["materia"] == mn)
        due_m   = sum(1 for k, v in due_today.items()    if v["materia"] == mn)
        with col:
            bg = "#fff3cd" if due_m > 0 else "#f8f9fa"
            bc = "#ffc107" if due_m > 0 else "#e9ecef"
            tc = "#856404" if due_m > 0 else "#495057"
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bc};border-radius:8px;
                        padding:10px 12px;text-align:center">
                <div style="font-size:16px!important">{md['icon']}</div>
                <div style="font-size:10px!important;font-weight:600;color:{tc};margin-top:3px">{mn[:6]}</div>
                <div style="font-size:11px!important;color:{tc}">{due_m} hoje / {total_m} total</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if not revisao_data:
        st.markdown("""
        <div style="text-align:center;padding:48px 0;color:#adb5bd">
            <div style="font-size:32px!important">📭</div>
            <div style="font-size:14px!important;font-weight:600;color:#495057;margin-top:12px">
                Nenhum tópico na fila ainda
            </div>
            <div style="font-size:12px!important;margin-top:6px">
                Marque tópicos como concluídos na aba ENEM 2026 para começar a revisar.
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif not due_list:
        proximas = sorted(revisao_data.items(), key=lambda x: x[1]["proxima_revisao"])
        prox_key, prox_v = proximas[0]
        st.markdown(f"""
        <div style="text-align:center;padding:40px 0;color:#adb5bd">
            <div style="font-size:32px!important">✅</div>
            <div style="font-size:14px!important;font-weight:600;color:#495057;margin-top:12px">
                Nenhuma revisão pendente hoje!
            </div>
            <div style="font-size:12px!important;margin-top:6px">
                Próxima revisão: <b>{prox_v['topico']}</b> em {prox_v['proxima_revisao']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Selecionar tópico atual
        if st.session_state.revisao_atual is None or st.session_state.revisao_atual not in due_today:
            st.session_state.revisao_atual = due_list[0][0]

        cur_key = st.session_state.revisao_atual
        cur_item = due_today.get(cur_key, due_list[0][1])
        cur_rev = revisao_data.get(cur_key, {})

        intervalo = cur_rev.get("intervalo", 1)
        repeticoes = cur_rev.get("repeticoes", 0)
        facilidade = cur_rev.get("facilidade", 2.5)

        # Navegação entre pendentes
        idx = next((i for i, (k, _) in enumerate(due_list) if k == cur_key), 0)
        nav_cols = st.columns([1, 4, 1])
        with nav_cols[0]:
            if idx > 0 and st.button("← Anterior"):
                st.session_state.revisao_atual = due_list[idx - 1][0]
                st.rerun()
        with nav_cols[1]:
            st.markdown(f"""
            <div style="text-align:center;padding:6px 0">
                <span style="font-size:12px!important;color:#868e96">
                    {idx + 1} de {len(due_list)} pendentes hoje
                </span>
            </div>
            """, unsafe_allow_html=True)
        with nav_cols[2]:
            if idx < len(due_list) - 1 and st.button("Próximo →"):
                st.session_state.revisao_atual = due_list[idx + 1][0]
                st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Card de revisão
        materia_icon = ENEM.get(cur_item["materia"], {}).get("icon", "📚")
        materia_cor  = ENEM.get(cur_item["materia"], {}).get("color", "#1a1a2e")

        prox_data = cur_rev.get("proxima_revisao", date.today().isoformat())
        dias_atraso = (date.today() - date.fromisoformat(prox_data)).days if prox_data <= date.today().isoformat() else 0

        st.markdown(f"""
        <div class="rev-card">
            <div class="rev-materia" style="color:{materia_cor}">
                {materia_icon} {cur_item['materia']}
            </div>
            <div class="rev-topico">{cur_item['topico']}</div>
            <div class="rev-intervalo">
                Revisão nº {repeticoes + 1} · Intervalo atual: {intervalo} dia(s)
                {f"· <span style='color:#c62828'>{dias_atraso}d atrasado</span>" if dias_atraso > 0 else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # Pergunta de avaliação
        st.markdown("""
        <div style="text-align:center;font-size:13px!important;font-weight:600;
                    color:#212529;margin-bottom:14px">
            Como foi sua lembrança desse tópico?
        </div>
        """, unsafe_allow_html=True)

        bc1, bc2, bc3, bc4 = st.columns(4)

        notas = [
            (bc1, 0, "😰", "Não lembro",  "#c62828", "Volta amanhã"),
            (bc2, 1, "😅", "Difícil",     "#e65100", "Revisa em 2 dias"),
            (bc3, 2, "🙂", "Médio",       "#1565c0", "Revisa em ~4 dias"),
            (bc4, 3, "😎", "Fácil",       "#2e7d32", "Revisa em ~7 dias"),
        ]

        for col, nota, emoji, label, cor, hint in notas:
            with col:
                st.markdown(f"""
                <div style="text-align:center;margin-bottom:6px">
                    <div style="font-size:22px!important">{emoji}</div>
                    <div style="font-size:11px!important;color:{cor};font-weight:600">{label}</div>
                    <div style="font-size:10px!important;color:#adb5bd">{hint}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(label, key=f"nota_{nota}_{cur_key}", use_container_width=True):
                    novo_int, nova_fac, novas_rep, nova_prox = sm2_update(
                        intervalo, facilidade, repeticoes, nota
                    )
                    save_revisao(cur_key, cur_item["materia"], cur_item["topico"],
                                 novo_int, nova_fac, novas_rep, nova_prox, nota)
                    st.session_state.revisao_data = get_revisao_data()

                    # Avança para o próximo pendente
                    remaining = [(k, v) for k, v in due_list if k != cur_key]
                    if remaining:
                        st.session_state.revisao_atual = remaining[0][0]
                    else:
                        st.session_state.revisao_atual = None

                    st.success(f"Salvo! Próxima revisão em {novo_int} dia(s) — {nova_prox}")
                    st.rerun()

        # Lista de todas as revisões
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Todas as revisões agendadas</div>', unsafe_allow_html=True)

        todas = sorted(revisao_data.items(), key=lambda x: x[1]["proxima_revisao"])
        for rk, rv in todas:
            hoje = date.today().isoformat()
            is_due = rv["proxima_revisao"] <= hoje
            icon_m = ENEM.get(rv["materia"], {}).get("icon", "📚")
            bg  = "#fff3cd" if is_due else "#fff"
            bc  = "#ffc107" if is_due else "#e9ecef"
            tag = "HOJE" if is_due else rv["proxima_revisao"]
            tc  = "#856404" if is_due else "#adb5bd"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        background:{bg};border:1px solid {bc};border-radius:6px;
                        padding:8px 12px;margin-bottom:4px">
                <div>
                    <span style="font-size:12px!important;color:#212529">
                        {icon_m} <b>{rv['materia']}</b> · {rv['topico']}
                    </span>
                </div>
                <div style="text-align:right;min-width:120px">
                    <span style="font-size:10px!important;color:{tc};font-weight:600">{tag}</span>
                    <span style="font-size:10px!important;color:#adb5bd;margin-left:8px">
                        {rv['repeticoes']}x · {rv['intervalo']}d
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)


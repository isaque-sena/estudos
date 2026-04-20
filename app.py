import streamlit as st
import sqlite3
import math
import json
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Tracker — Isaque Sena",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "progresso.db"

# ── Banco ─────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS progresso (
        id TEXT PRIMARY KEY, area TEXT, secao TEXT, topico TEXT,
        concluido INTEGER DEFAULT 0, atualizado_em TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS revisao (
        id TEXT PRIMARY KEY, materia TEXT, topico TEXT,
        proxima_revisao TEXT, intervalo INTEGER DEFAULT 1,
        facilidade REAL DEFAULT 2.5, repeticoes INTEGER DEFAULT 0,
        ultima_nota INTEGER DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sessoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, area TEXT, minutos INTEGER, nota TEXT)""")
    conn.commit()
    return conn

def load_progress():
    conn = get_conn()
    rows = conn.execute("SELECT id, concluido FROM progresso").fetchall()
    conn.close()
    return {r[0]: bool(r[1]) for r in rows}

def save_topic(key, area, secao, topico, concluido):
    conn = get_conn()
    conn.execute("""INSERT INTO progresso (id,area,secao,topico,concluido,atualizado_em)
        VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
        concluido=excluded.concluido, atualizado_em=excluded.atualizado_em""",
        (key, area, secao, topico, int(concluido), datetime.now().isoformat()))
    conn.commit(); conn.close()

def reset_all():
    conn = get_conn()
    conn.execute("DELETE FROM progresso")
    conn.execute("DELETE FROM revisao")
    conn.execute("DELETE FROM sessoes")
    conn.commit(); conn.close()

def export_csv():
    conn = get_conn()
    rows = conn.execute("SELECT area,secao,topico,concluido,atualizado_em FROM progresso ORDER BY area,secao").fetchall()
    conn.close()
    lines = ["area,secao,topico,concluido,atualizado_em"]
    for r in rows:
        lines.append(f'"{r[0]}","{r[1]}","{r[2]}","{"Sim" if r[3] else "Nao"}","{r[4] or ""}"')
    return "\n".join(lines)

def get_revisao_data():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM revisao").fetchall()
    conn.close()
    data = {}
    for r in rows:
        data[r[0]] = {"materia":r[1],"topico":r[2],"proxima_revisao":r[3],
                      "intervalo":r[4],"facilidade":r[5],"repeticoes":r[6],"ultima_nota":r[7]}
    return data

def adicionar_revisao(key, materia, topico):
    conn = get_conn()
    ex = conn.execute("SELECT id FROM revisao WHERE id=?", (key,)).fetchone()
    if not ex:
        conn.execute("""INSERT INTO revisao (id,materia,topico,proxima_revisao,intervalo,facilidade,repeticoes,ultima_nota)
            VALUES (?,?,?,?,1,2.5,0,0)""", (key, materia, topico, date.today().isoformat()))
        conn.commit()
    conn.close()

def save_revisao(key, materia, topico, intervalo, facilidade, repeticoes, proxima, nota):
    conn = get_conn()
    conn.execute("""INSERT INTO revisao (id,materia,topico,proxima_revisao,intervalo,facilidade,repeticoes,ultima_nota)
        VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
        proxima_revisao=excluded.proxima_revisao, intervalo=excluded.intervalo,
        facilidade=excluded.facilidade, repeticoes=excluded.repeticoes, ultima_nota=excluded.ultima_nota""",
        (key, materia, topico, proxima, intervalo, facilidade, repeticoes, nota))
    conn.commit(); conn.close()

def sm2_update(intervalo, facilidade, repeticoes, nota):
    q = [1,2,4,5][nota]
    if q < 3:
        repeticoes = 0; intervalo = 1
    else:
        if repeticoes == 0: intervalo = 1
        elif repeticoes == 1: intervalo = 6
        else: intervalo = math.ceil(intervalo * facilidade)
        repeticoes += 1
    facilidade = max(1.3, facilidade + 0.1 - (5-q)*(0.08+(5-q)*0.02))
    proxima = (date.today() + timedelta(days=intervalo)).isoformat()
    return intervalo, facilidade, repeticoes, proxima

def get_due_today(revisao_data):
    hoje = date.today().isoformat()
    return {k:v for k,v in revisao_data.items() if v["proxima_revisao"] <= hoje}

# ── Calendário semanal ────────────────────────────────────────────────────
CALENDARIO = {
    "Segunda": [
        {"bloco": "Bloco 1 — 1h30", "area": "C", "icon": "⚙️", "cor": "#1565c0",
         "desc": "Lógica e algoritmos — CS50 ou exercícios"},
        {"bloco": "Bloco 2 — 1h30", "area": "Python Conceitos", "icon": "🐍", "cor": "#2e7d32",
         "desc": "Fundamentos: variáveis, funções, estruturas de dados"},
        {"bloco": "Bloco 3 — 30min", "area": "ENEM", "icon": "📚", "cor": "#78909c",
         "desc": "Matemática"},
        {"bloco": "Passivo — manhã/noite", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Podcast Syntax.fm ou vídeo Fireship"},
    ],
    "Terça": [
        {"bloco": "Bloco 1 — 1h30", "area": "C", "icon": "⚙️", "cor": "#1565c0",
         "desc": "Lógica e algoritmos — CS50 ou exercícios"},
        {"bloco": "Bloco 2 — 1h30", "area": "SQL", "icon": "🗄️", "cor": "#6a1b9a",
         "desc": "Teoria + exercícios HackerRank"},
        {"bloco": "Bloco 3 — 30min", "area": "ENEM", "icon": "📚", "cor": "#78909c",
         "desc": "Português"},
        {"bloco": "Passivo — manhã/noite", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Ler documentação técnica em inglês"},
    ],
    "Quarta": [
        {"bloco": "Bloco 1 — 1h30", "area": "C", "icon": "⚙️", "cor": "#1565c0",
         "desc": "Lógica e algoritmos — CS50 ou exercícios"},
        {"bloco": "Bloco 2 — 1h30", "area": "Power BI", "icon": "📊", "cor": "#c62828",
         "desc": "DAX, modelagem e dashboard"},
        {"bloco": "Bloco 3 — 30min", "area": "ENEM", "icon": "📚", "cor": "#78909c",
         "desc": "Redação"},
        {"bloco": "Passivo — manhã/noite", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Podcast ou vídeo técnico"},
    ],
    "Quinta": [
        {"bloco": "Bloco 1 — 1h30", "area": "C", "icon": "⚙️", "cor": "#1565c0",
         "desc": "Lógica e algoritmos — CS50 ou exercícios"},
        {"bloco": "Bloco 2 — 1h30", "area": "Python Projetos", "icon": "🚀", "cor": "#00695c",
         "desc": "Projeto atual — construir e avançar"},
        {"bloco": "Bloco 3 — 30min", "area": "ENEM", "icon": "📚", "cor": "#78909c",
         "desc": "Ciências da Natureza"},
        {"bloco": "Passivo — manhã/noite", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Anki vocabulário técnico"},
    ],
    "Sexta": [
        {"bloco": "Bloco 1 — 1h30", "area": "C", "icon": "⚙️", "cor": "#1565c0",
         "desc": "Revisão da semana em C"},
        {"bloco": "Bloco 2 — 1h30", "area": "SQL + Power BI", "icon": "📊", "cor": "#6a1b9a",
         "desc": "Integrar SQL com Power BI — projeto prático"},
        {"bloco": "Bloco 3 — 30min", "area": "ENEM", "icon": "📚", "cor": "#78909c",
         "desc": "Revisão geral da semana"},
        {"bloco": "Passivo — manhã/noite", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Série ou filme com legenda em inglês"},
    ],
    "Sábado": [
        {"bloco": "Bloco 1 — 1h", "area": "Python Projetos", "icon": "🚀", "cor": "#00695c",
         "desc": "Avançar no projeto da semana"},
        {"bloco": "Bloco 2 — 30min", "area": "Revisão Geral", "icon": "🔁", "cor": "#455a64",
         "desc": "Revisar o que estudou na semana"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Série ou podcast — sem pressão"},
    ],
    "Domingo": [
        {"bloco": "Descanso", "area": "Descanso", "icon": "😴", "cor": "#90a4ae",
         "desc": "O cérebro consolida o aprendizado. Descanse de verdade."},
    ],
}

# ── Conteúdo Python Conceitos ──────────────────────────────────────────────
PYTHON_CONCEITOS = {
    "Fundamentos": {
        "icon": "🔢", "color": "#1565c0",
        "topics": [
            "Variáveis e tipos de dados (int, float, str, bool)",
            "Conversão de tipos (int(), float(), str())",
            "Operadores aritméticos (+, -, *, /, //, %, **)",
            "Operadores de comparação (==, !=, >, <, >=, <=)",
            "Operadores lógicos (and, or, not)",
            "Operadores de atribuição (=, +=, -=, *=)",
            "f-strings e formatação de strings",
            "Input e output (input(), print())",
        ]
    },
    "Estruturas de Controle": {
        "icon": "🔀", "color": "#6a1b9a",
        "topics": [
            "if / elif / else",
            "Operador ternário",
            "for loop — percorrer listas",
            "for loop — range(inicio, fim, passo)",
            "while loop",
            "break e continue",
            "enumerate() — índice + valor",
            "zip() — duas listas ao mesmo tempo",
        ]
    },
    "Funções": {
        "icon": "⚡", "color": "#2e7d32",
        "topics": [
            "Definir funções com def",
            "Parâmetros e argumentos",
            "Valor de retorno (return)",
            "Valores padrão de parâmetros",
            "Argumentos nomeados (keyword arguments)",
            "*args — número variável de argumentos",
            "**kwargs — argumentos nomeados variáveis",
            "Funções lambda",
            "Escopo de variáveis (local vs global)",
            "Recursão — fatorial e fibonacci",
        ]
    },
    "Estruturas de Dados": {
        "icon": "📦", "color": "#e65100",
        "topics": [
            "Listas — criação e acesso por índice",
            "Listas — métodos (append, remove, sort, reverse)",
            "Listas — fatiamento (slicing)",
            "Tuplas — imutabilidade e desempacotamento",
            "Conjuntos (sets) — sem duplicatas",
            "Dicionários — chave e valor",
            "Dicionários — métodos (keys, values, items, get)",
            "List comprehension",
            "Dict comprehension",
            "Generator expression",
        ]
    },
    "Strings Avançado": {
        "icon": "📝", "color": "#880e4f",
        "topics": [
            ".strip() .upper() .lower() .title()",
            ".replace() .split() .join()",
            ".startswith() .endswith() .find()",
            ".count() e len()",
            "Formatação f-string avançada",
            "Expressões regulares básicas (re)",
        ]
    },
    "Orientação a Objetos": {
        "icon": "🏗️", "color": "#4a148c",
        "topics": [
            "Classes e objetos",
            "__init__ e self",
            "Atributos e métodos",
            "Herança",
            "super()",
            "Encapsulamento",
            "@property",
            "Métodos especiais (__str__, __repr__)",
        ]
    },
    "Tratamento de Erros": {
        "icon": "🛡️", "color": "#c62828",
        "topics": [
            "try / except / finally",
            "Tipos de erros (ValueError, TypeError, KeyError)",
            "Capturar a mensagem do erro (as e)",
            "Criar exceções customizadas",
            "else no try/except",
        ]
    },
    "Módulos e Arquivos": {
        "icon": "📁", "color": "#00695c",
        "topics": [
            "import e from...import",
            "Módulo math",
            "Módulo random",
            "Módulo datetime",
            "Módulo os e os.path",
            "Módulo json",
            "Leitura de arquivos (with open, read, readlines)",
            "Escrita de arquivos (write, writelines)",
            "Leitura e escrita de JSON",
        ]
    },
}

# ── Python Projetos ───────────────────────────────────────────────────────
PYTHON_PROJETOS = {
    "Projeto 1 — Analisador de Gastos": {
        "icon": "💰", "color": "#1565c0", "nivel": "Básico",
        "desc": "Importa CSV de gastos e mostra resumo por categoria com gráficos.",
        "topics": [
            "pandas — leitura de CSV",
            "pandas — groupby e agrupamento",
            "pandas — filtros e seleção",
            "matplotlib — gráfico de barras",
            "matplotlib — gráfico de pizza",
            "f-strings e formatação de números",
            "tratamento de erros básico",
        ]
    },
    "Projeto 2 — Buscador de Vagas": {
        "icon": "🔍", "color": "#1565c0", "nivel": "Básico",
        "desc": "Busca vagas em APIs públicas e salva em CSV organizado.",
        "topics": [
            "requests — chamadas HTTP",
            "BeautifulSoup — parsing HTML",
            "manipulação de dicionários",
            "salvamento em CSV",
            "try/except para erros de rede",
            "loops e filtragem de dados",
        ]
    },
    "Projeto 3 — Dashboard BACEN/IBGE": {
        "icon": "📈", "color": "#1565c0", "nivel": "Básico",
        "desc": "Puxa IPCA, SELIC e câmbio do BACEN e exibe num dashboard Streamlit.",
        "topics": [
            "requests — consumir APIs REST",
            "pandas — JSON para DataFrame",
            "Streamlit — estrutura básica",
            "Streamlit — sidebar e filtros",
            "plotly — gráficos interativos",
            "st.cache_data",
        ]
    },
    "Projeto 4 — ETL de Planilha": {
        "icon": "🔄", "color": "#1565c0", "nivel": "Básico",
        "desc": "Recebe planilha bagunçada, limpa e gera relatório em Excel.",
        "topics": [
            "pandas — leitura de Excel openpyxl",
            "pandas — limpeza de strings",
            "pandas — remoção de duplicatas",
            "pandas — tratamento de nulos",
            "pandas — exportar para Excel",
            "funções reutilizáveis",
        ]
    },
    "Projeto 5 — Gerador de Relatório PDF": {
        "icon": "📄", "color": "#1565c0", "nivel": "Básico",
        "desc": "Lê dados de CSV e gera PDF com tabelas e gráficos automaticamente.",
        "topics": [
            "pandas — cálculo de métricas",
            "reportlab — criação de PDF",
            "matplotlib — salvar como imagem",
            "automação de documentos",
            "formatação de tabelas em PDF",
        ]
    },
    "Projeto 6 — Pipeline com Banco de Dados": {
        "icon": "🗄️", "color": "#e65100", "nivel": "Intermediário",
        "desc": "Coleta dados de API, transforma e armazena em SQLite. Roda automaticamente.",
        "topics": [
            "SQLAlchemy — conexão com banco",
            "SQLite — banco local",
            "schedule — agendamento",
            "SQL INSERT SELECT UPDATE",
            "conceitos de pipeline de dados",
        ]
    },
    "Projeto 7 — Dashboard Financeiro B3": {
        "icon": "💹", "color": "#e65100", "nivel": "Intermediário",
        "desc": "Puxa ações da B3 com yfinance e exibe indicadores técnicos interativos.",
        "topics": [
            "yfinance — dados de ações",
            "pandas — médias móveis",
            "plotly — candlestick chart",
            "Streamlit — layout avançado",
            "seleção dinâmica de ativos",
        ]
    },
    "Projeto 8 — API com FastAPI": {
        "icon": "🔌", "color": "#e65100", "nivel": "Intermediário",
        "desc": "Cria API REST que recebe CSV, processa e retorna métricas em JSON.",
        "topics": [
            "FastAPI — estrutura básica",
            "Pydantic — validação de dados",
            "uvicorn — servidor",
            "endpoints GET e POST",
            "upload de arquivos",
            "documentação automática",
        ]
    },
    "Projeto 9 — Agente com LLM": {
        "icon": "🤖", "color": "#4a148c", "nivel": "Avançado",
        "desc": "Agente que analisa CSV e responde perguntas em português via Groq API.",
        "topics": [
            "Groq API — chamadas básicas",
            "prompt engineering técnico",
            "integração LLM + pandas",
            "contexto dinâmico",
            "tratamento de respostas JSON",
        ]
    },
    "Projeto 10 — Colmeia de Agentes": {
        "icon": "🐝", "color": "#4a148c", "nivel": "Avançado",
        "desc": "Sistema multi-agentes CLI com memória persistente e agentes especializados.",
        "topics": [
            "arquitetura de agentes",
            "memória comprimida em markdown",
            "Groq API avançada",
            "CLI com Rich",
            "design de sistemas",
            "Playwright para automação",
        ]
    },
}

# ── C Módulos ─────────────────────────────────────────────────────────────
C_MODULOS = {
    "Módulo 1 — Fundamentos": {
        "icon": "🔧", "color": "#1565c0",
        "topics": ["variáveis e tipos int float char","sizeof e tamanho na memória",
                   "operadores aritméticos","operadores de comparação",
                   "operadores lógicos AND OR NOT","printf e scanf","compilação com gcc"]
    },
    "Módulo 2 — Controle de Fluxo": {
        "icon": "🔀", "color": "#1565c0",
        "topics": ["if else if else","operador ternário","switch case",
                   "for com contador","while e do while","break e continue"]
    },
    "Módulo 3 — Funções": {
        "icon": "⚡", "color": "#1565c0",
        "topics": ["declaração e definição","parâmetros e tipos de retorno",
                   "void sem retorno","escopo de variáveis","recursão fatorial",
                   "recursão fibonacci","protótipos de função"]
    },
    "Módulo 4 — Arrays": {
        "icon": "📦", "color": "#1565c0",
        "topics": ["declaração de arrays","acesso por índice","percorrer com for",
                   "arrays em funções","strings char[]","strlen strcpy","matrizes 2D"]
    },
    "Módulo 5 — Ponteiros": {
        "icon": "👉", "color": "#1565c0",
        "topics": ["o que é um ponteiro","operadores & e *","ponteiro e array",
                   "passagem por referência","aritmética de ponteiros","malloc e free"]
    },
    "Módulo 6 — Structs e Algoritmos": {
        "icon": "🏗️", "color": "#1565c0",
        "topics": ["struct definição e uso","array de structs","busca linear",
                   "busca binária","bubble sort","selection sort","insertion sort"]
    },
}

# ── SQL ───────────────────────────────────────────────────────────────────
SQL_MODULOS = {
    "SQL Básico": {
        "icon": "🔍", "color": "#6a1b9a",
        "topics": ["SELECT e FROM","WHERE filtros","ORDER BY","LIMIT",
                   "DISTINCT","AND OR NOT","LIKE padrão"]
    },
    "SQL Intermediário": {
        "icon": "🔗", "color": "#6a1b9a",
        "topics": ["GROUP BY agrupamento","HAVING filtro pós-grupo",
                   "COUNT SUM AVG MAX MIN","INNER JOIN","LEFT JOIN",
                   "subqueries","CREATE TABLE e tipos"]
    },
}

# ── Power BI ──────────────────────────────────────────────────────────────
POWERBI_MODULOS = {
    "Power BI Essencial": {
        "icon": "📊", "color": "#c62828",
        "topics": ["importar CSV e Excel","Power Query limpeza",
                   "relacionamentos entre tabelas","DAX SUM COUNT AVERAGE",
                   "DAX CALCULATE e filtros","DAX RELATED e LOOKUPVALUE",
                   "visuais barras linha pizza","filtros e segmentações",
                   "publicar no Power BI Service"]
    },
}

# ── Inglês ────────────────────────────────────────────────────────────────
INGLES_MODULOS = {
    "Vocabulário Técnico": {
        "icon": "💬", "color": "#e65100",
        "topics": ["termos de programação (function, array, loop, variable)",
                   "termos de dados (dataset, query, pipeline, aggregation)",
                   "termos de IA (model, inference, embedding, token)",
                   "erros comuns em inglês (TypeError, KeyError, undefined)",
                   "verbos técnicos (deploy, fetch, parse, render, compile)"]
    },
    "Leitura Técnica": {
        "icon": "📖", "color": "#e65100",
        "topics": ["documentação do Python em inglês",
                   "documentação do pandas em inglês",
                   "artigos no Dev.to ou Medium",
                   "Stack Overflow sem tradutor",
                   "README de projetos no GitHub"]
    },
    "Listening": {
        "icon": "🎧", "color": "#e65100",
        "topics": ["Podcast Syntax.fm — 3 episódios",
                   "Canal Fireship no YouTube — 10 vídeos",
                   "CS50 Harvard em inglês com legenda EN",
                   "TED Talks técnicos — 5 assistidos"]
    },
    "ENEM Inglês": {
        "icon": "📝", "color": "#e65100",
        "topics": ["interpretação de textos — prova 2023",
                   "interpretação de textos — prova 2022",
                   "interpretação de textos — prova 2021",
                   "gramática básica — tempos verbais",
                   "vocabulário cotidiano ENEM"]
    },
}

# ── ENEM ──────────────────────────────────────────────────────────────────
ENEM = {
    "Matemática": {"icon": "📐", "color": "#1565c0",
        "topics": ["Porcentagem e regra de três","Equações de 1 grau",
                   "Equações de 2 grau","Sistemas de equações","Função afim",
                   "Função quadrática","Função exponencial","Geometria área e perímetro",
                   "Geometria volume","Trigonometria","Estatística e probabilidade",
                   "Juros simples","Juros compostos"]},
    "Física": {"icon": "⚡", "color": "#e65100",
        "topics": ["Mecânica movimento e velocidade","Leis de Newton",
                   "Trabalho e energia","Termodinâmica","Óptica","Eletricidade","Ondas","Física Moderna"]},
    "Química": {"icon": "🧪", "color": "#2e7d32",
        "topics": ["Estrutura atômica e tabela periódica","Ligações químicas",
                   "Química Orgânica","Ácidos bases e sais","Estequiometria","Termoquímica","Química Ambiental"]},
    "Biologia": {"icon": "🧬", "color": "#00695c",
        "topics": ["Citologia","Genética","Ecologia","Fisiologia Humana",
                   "Evolução","Microbiologia","Botânica"]},
    "História": {"icon": "🏛️", "color": "#4a148c",
        "topics": ["Antiguidade e Idade Média","Revoluções","Colonização do Brasil",
                   "Império e República","Guerras Mundiais","Guerra Fria","Movimentos Sociais"]},
    "Geografia": {"icon": "🌍", "color": "#004d40",
        "topics": ["Clima relevo e vegetação","Urbanização e migrações",
                   "Geopolítica","Sustentabilidade","Cartografia","Regiões do Brasil"]},
    "Português": {"icon": "📖", "color": "#880e4f",
        "topics": ["Gramática e concordância","Interpretação de textos",
                   "Literatura","Gêneros textuais","Figuras de linguagem"]},
    "Redação": {"icon": "✍️", "color": "#37474f",
        "topics": ["Estrutura da redação ENEM","Coerência e coesão",
                   "Argumentação e proposta","Temas meio ambiente","Temas saúde e educação","Prática semanal"]},
}

def make_key(area, secao, topico):
    return f"{area}||{secao}||{topico}"

def make_enem_key(mn, t):
    return f"ENEM||{mn}||{t}"

# ── Init ──────────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()
if "revisao_data" not in st.session_state:
    st.session_state.revisao_data = get_revisao_data()
if "revisao_atual" not in st.session_state:
    st.session_state.revisao_atual = None

progress = st.session_state.progress
revisao_data = st.session_state.revisao_data
due_today = get_due_today(revisao_data)

# ── Stats helpers ──────────────────────────────────────────────────────────
def count_done(modulos, key_fn):
    total = sum(len(v["topics"]) for v in modulos.values())
    done  = sum(1 for mn, md in modulos.items()
                for t in md["topics"] if progress.get(key_fn(mn, t), False))
    return done, total

def proj_stats():
    total = sum(len(v["topics"]) for v in PYTHON_PROJETOS.values())
    done  = sum(1 for pn, pd in PYTHON_PROJETOS.items()
                for t in pd["topics"]
                if progress.get(make_key("ProjPython", pn, t), False))
    return done, total

done_conc, total_conc = count_done(PYTHON_CONCEITOS, lambda mn,t: make_key("PyConc", mn, t))
done_proj, total_proj = proj_stats()
done_c,    total_c    = count_done(C_MODULOS,        lambda mn,t: make_key("C", mn, t))
done_sql,  total_sql  = count_done(SQL_MODULOS,      lambda mn,t: make_key("SQL", mn, t))
done_pbi,  total_pbi  = count_done(POWERBI_MODULOS,  lambda mn,t: make_key("PBI", mn, t))
done_en,   total_en   = count_done(INGLES_MODULOS,   lambda mn,t: make_key("EN", mn, t))
done_enem, total_enem = count_done(ENEM,             lambda mn,t: make_enem_key(mn, t))

done_prog  = done_conc + done_proj + done_c + done_sql + done_pbi
total_prog = total_conc + total_proj + total_c + total_sql + total_pbi
pct_prog   = round(done_prog / total_prog * 100, 1) if total_prog else 0
pct_enem   = round(done_enem / total_enem * 100, 1) if total_enem else 0
pct_en     = round(done_en / total_en * 100, 1) if total_en else 0

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"],p,span,label,div{font-family:'Inter',sans-serif!important;font-size:13px!important}
.stApp{background:#f8f9fa}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e9ecef!important}
.page-title{font-family:'Space Grotesk',sans-serif!important;font-size:22px!important;font-weight:700;color:#1a1a2e;margin:0 0 2px}
.page-sub{font-size:11px!important;color:#adb5bd;letter-spacing:.08em;margin-bottom:20px}
.kpi{background:#fff;border:1px solid #e9ecef;border-radius:10px;padding:14px 18px;text-align:center}
.kpi-num{font-family:'Space Grotesk',sans-serif!important;font-size:22px!important;font-weight:700;line-height:1;margin-bottom:3px}
.kpi-lbl{font-size:10px!important;color:#adb5bd;letter-spacing:.08em;text-transform:uppercase}
.sec-label{font-size:10px!important;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#868e96;border-left:3px solid #e9ecef;padding-left:8px;margin:16px 0 6px}
div[data-testid="stCheckbox"]{background:#fff;border:1px solid #e9ecef;border-radius:6px;padding:5px 10px;margin-bottom:3px}
div[data-testid="stCheckbox"]:hover{border-color:#ced4da;background:#f8f9fa}
div[data-testid="stCheckbox"] label p{font-size:12px!important;color:#495057!important}
.stProgress>div>div{background:#e9ecef!important;border-radius:4px!important;height:5px!important}
.stProgress>div>div>div{border-radius:4px!important;height:5px!important}
.stTabs [data-baseweb="tab-list"]{background:#fff;border:1px solid #e9ecef;border-radius:8px;padding:3px;gap:2px}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#868e96!important;border-radius:6px!important;font-size:12px!important;font-weight:500!important;padding:6px 12px!important}
.stTabs [aria-selected="true"]{background:#f1f3f5!important;color:#212529!important}
.cal-day{background:#fff;border:1px solid #e9ecef;border-radius:10px;padding:14px;height:100%}
.cal-dayname{font-family:'Space Grotesk',sans-serif!important;font-size:12px!important;font-weight:700;color:#212529;margin-bottom:10px}
.cal-bloco{border-radius:6px;padding:8px 10px;margin-bottom:6px}
.cal-bloco-label{font-size:10px!important;color:#868e96;letter-spacing:.05em}
.cal-bloco-area{font-size:12px!important;font-weight:600;color:#212529;margin:2px 0}
.cal-bloco-desc{font-size:11px!important;color:#868e96}
.proj-card{background:#fff;border:1px solid #e9ecef;border-radius:10px;padding:14px 16px;margin-bottom:10px}
.proj-title{font-family:'Space Grotesk',sans-serif!important;font-size:13px!important;font-weight:700;color:#212529}
.proj-desc{font-size:11px!important;color:#868e96;margin:4px 0 10px}
.nivel-badge{display:inline-block;font-size:10px!important;font-weight:600;padding:2px 8px;border-radius:4px;margin-bottom:8px}
.stDownloadButton button,button[kind="secondary"]{font-size:12px!important;border-radius:6px!important;background:#fff!important;border:1px solid #e9ecef!important;color:#495057!important}
.sidebar-title{font-family:'Space Grotesk',sans-serif!important;font-size:15px!important;font-weight:700;color:#1a1a2e}
.sidebar-sub{font-size:10px!important;color:#adb5bd;letter-spacing:.08em}
hr{border-color:#e9ecef!important}
</style>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="padding:8px 0 16px"><div class="sidebar-title">🧠 Tracker de Estudos</div><div class="sidebar-sub">ISAQUE SENA · SENALABS</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    if due_today:
        st.markdown(f'<div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:10px 14px;margin-bottom:12px"><div style="font-size:12px!important;font-weight:600;color:#856404">🔁 {len(due_today)} revisão(ões) hoje</div></div>', unsafe_allow_html=True)

    def sidebar_bloco(icon, label, done, total, pct):
        st.markdown(f'''<div style="background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:10px 12px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between">
                <span style="font-size:12px!important;font-weight:600;color:#212529">{icon} {label}</span>
                <span style="font-size:11px!important;color:#adb5bd">{pct}%</span>
            </div>
            <div style="font-size:10px!important;color:#adb5bd;margin:2px 0 6px">{done}/{total} tópicos</div>
        </div>''', unsafe_allow_html=True)
        st.progress(pct / 100)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px!important;font-weight:600;color:#495057;margin-bottom:8px">💻 PROGRAMAÇÃO</div>', unsafe_allow_html=True)
    sidebar_bloco("🐍","Python Conceitos", done_conc, total_conc, round(done_conc/total_conc*100) if total_conc else 0)
    sidebar_bloco("🚀","Python Projetos",  done_proj, total_proj, round(done_proj/total_proj*100) if total_proj else 0)
    sidebar_bloco("⚙️","C — Lógica",       done_c,    total_c,    round(done_c/total_c*100) if total_c else 0)
    sidebar_bloco("🗄️","SQL",              done_sql,  total_sql,  round(done_sql/total_sql*100) if total_sql else 0)
    sidebar_bloco("📊","Power BI",         done_pbi,  total_pbi,  round(done_pbi/total_pbi*100) if total_pbi else 0)

    st.markdown('<div style="font-size:11px!important;font-weight:600;color:#495057;margin:12px 0 8px">🌐 INGLÊS</div>', unsafe_allow_html=True)
    sidebar_bloco("🌐","Inglês", done_en, total_en, round(done_en/total_en*100) if total_en else 0)

    st.markdown('<div style="font-size:11px!important;font-weight:600;color:#495057;margin:12px 0 8px">📚 ENEM 2026</div>', unsafe_allow_html=True)
    sidebar_bloco("📚","ENEM", done_enem, total_enem, round(done_enem/total_enem*100) if total_enem else 0)

    st.markdown("---")
    st.download_button("⬇️ Exportar CSV", data=export_csv(),
        file_name=f"progresso_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv", use_container_width=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Resetar progresso", use_container_width=True, type="secondary"):
        reset_all()
        st.session_state.progress = {}
        st.session_state.revisao_data = {}
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Trilha de Estudos</div><div class="page-sub">MARQUE O QUE JÁ ESTUDOU · SALVO AUTOMATICAMENTE</div>', unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
for col,num,lbl,cor in [
    (c1,f"{pct_prog}%","PROGRAMAÇÃO","#1565c0"),
    (c2,f"{round(done_conc/total_conc*100) if total_conc else 0}%","PY CONCEITOS","#2e7d32"),
    (c3,f"{round(done_proj/total_proj*100) if total_proj else 0}%","PY PROJETOS","#00695c"),
    (c4,f"{round(done_c/total_c*100) if total_c else 0}%","C LÓGICA","#1565c0"),
    (c5,f"{pct_en}%","INGLÊS","#e65100"),
    (c6,f"{pct_enem}%","ENEM","#78909c"),
    (c7,len(due_today),"REVISAR HOJE","#ffc107"),
]:
    with col:
        st.markdown(f'<div class="kpi"><div class="kpi-num" style="color:{cor}">{num}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────
rev_lbl = f"🔁 Revisão ENEM {'🔴' if due_today else ''}"
tabs = st.tabs(["📅 Calendário","🐍 Python Conceitos","🚀 Python Projetos",
                "⚙️ C — Lógica","🗄️ SQL","📊 Power BI","🌐 Inglês","📚 ENEM",rev_lbl])
tab_cal,tab_conc,tab_proj,tab_c,tab_sql,tab_pbi,tab_en,tab_enem,tab_rev = tabs

# ── CALENDÁRIO ────────────────────────────────────────────────────────────
with tab_cal:
    hoje = date.today()
    dia_semana = hoje.strftime("%A")
    dias_pt = {"Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta",
               "Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"}
    dia_hoje = dias_pt.get(dia_semana, "Segunda")

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e9ecef;border-radius:10px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;gap:14px">
        <div style="font-size:28px!important">📅</div>
        <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:15px!important;font-weight:700;color:#212529">
                Hoje é {dia_hoje}, {hoje.strftime('%d/%m/%Y')}
            </div>
            <div style="font-size:11px!important;color:#adb5bd;margin-top:2px">
                Veja abaixo o que estudar hoje e a programação da semana
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Destaque do dia
    if dia_hoje in CALENDARIO:
        st.markdown('<div class="sec-label">📌 Hoje</div>', unsafe_allow_html=True)
        blocos_hoje = CALENDARIO[dia_hoje]
        cols_hoje = st.columns(len(blocos_hoje))
        for col, bloco in zip(cols_hoje, blocos_hoje):
            with col:
                st.markdown(f"""
                <div style="background:{bloco['cor']}12;border:1px solid {bloco['cor']}40;
                            border-left:4px solid {bloco['cor']};border-radius:8px;padding:12px 14px">
                    <div style="font-size:10px!important;color:{bloco['cor']};font-weight:600;
                                letter-spacing:.05em;text-transform:uppercase">{bloco['bloco']}</div>
                    <div style="font-size:13px!important;font-weight:600;color:#212529;margin:4px 0">
                        {bloco['icon']} {bloco['area']}
                    </div>
                    <div style="font-size:11px!important;color:#868e96">{bloco['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">📆 Semana completa</div>', unsafe_allow_html=True)

    dias_ordem = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    cols_sem = st.columns(7)
    for col, dia in zip(cols_sem, dias_ordem):
        with col:
            is_hoje = dia == dia_hoje
            borda = "#1565c0" if is_hoje else "#e9ecef"
            bg_header = "#1565c010" if is_hoje else "#f8f9fa"
            st.markdown(f"""
            <div style="background:#fff;border:1px solid {borda};border-radius:10px;
                        padding:10px 10px 14px;height:100%">
                <div style="font-family:'Space Grotesk',sans-serif;font-size:11px!important;
                            font-weight:700;color:{'#1565c0' if is_hoje else '#495057'};
                            margin-bottom:10px;padding:4px 6px;background:{bg_header};
                            border-radius:5px;text-align:center">
                    {dia} {'← hoje' if is_hoje else ''}
                </div>
            """, unsafe_allow_html=True)
            for bloco in CALENDARIO.get(dia, []):
                st.markdown(f"""
                <div style="background:{bloco['cor']}10;border-left:3px solid {bloco['cor']};
                            border-radius:0 5px 5px 0;padding:6px 8px;margin-bottom:5px">
                    <div style="font-size:9px!important;color:{bloco['cor']};font-weight:600;
                                letter-spacing:.03em">{bloco['bloco']}</div>
                    <div style="font-size:11px!important;font-weight:600;color:#212529;margin:2px 0">
                        {bloco['icon']} {bloco['area']}
                    </div>
                    <div style="font-size:10px!important;color:#868e96">{bloco['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ── helper render_modulos ──────────────────────────────────────────────────
def render_modulos(modulos, prefix, tab):
    with tab:
        subtabs = st.tabs([f"{v['icon']} {k}" for k,v in modulos.items()])
        for subtab, (mn, md) in zip(subtabs, modulos.items()):
            with subtab:
                done_m = sum(1 for t in md["topics"] if progress.get(make_key(prefix, mn, t), False))
                total_m = len(md["topics"])
                pct_m = round(done_m/total_m*100,1) if total_m else 0
                cl, cr = st.columns([1,4])
                with cl:
                    st.markdown(f'<div class="kpi" style="text-align:left"><div class="kpi-num" style="color:{md["color"]}">{pct_m}%</div><div class="kpi-lbl">{done_m}/{total_m}</div></div>', unsafe_allow_html=True)
                with cr:
                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    st.progress(pct_m/100)
                st.markdown(f'<div class="sec-label">{md["icon"]} {mn}</div>', unsafe_allow_html=True)
                for topic in md["topics"]:
                    key = make_key(prefix, mn, topic)
                    cur = progress.get(key, False)
                    chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                    if chk != cur:
                        progress[key] = chk
                        save_topic(key, prefix, mn, topic, chk)
                        st.rerun()

render_modulos(PYTHON_CONCEITOS, "PyConc", tab_conc)
render_modulos(C_MODULOS, "C", tab_c)
render_modulos(SQL_MODULOS, "SQL", tab_sql)
render_modulos(POWERBI_MODULOS, "PBI", tab_pbi)
render_modulos(INGLES_MODULOS, "EN", tab_en)

# ── PYTHON PROJETOS ───────────────────────────────────────────────────────
with tab_proj:
    niveis = {"Básico":"#1565c0","Intermediário":"#e65100","Avançado":"#4a148c"}
    for pn, pd in PYTHON_PROJETOS.items():
        done_p = sum(1 for t in pd["topics"] if progress.get(make_key("ProjPython", pn, t), False))
        total_p = len(pd["topics"])
        pct_p = round(done_p/total_p*100) if total_p else 0
        cor_nivel = niveis.get(pd["nivel"], "#868e96")
        with st.expander(f"{pd['icon']} {pn}  —  {done_p}/{total_p} tópicos  ({pct_p}%)"):
            st.markdown(f"""
            <span class="nivel-badge" style="background:{cor_nivel}15;color:{cor_nivel};border:1px solid {cor_nivel}40">
                {pd['nivel']}
            </span>
            <div class="proj-desc">{pd['desc']}</div>
            """, unsafe_allow_html=True)
            st.progress(pct_p/100)
            st.markdown('<div class="sec-label">Tópicos para aprender</div>', unsafe_allow_html=True)
            for topic in pd["topics"]:
                key = make_key("ProjPython", pn, topic)
                cur = progress.get(key, False)
                chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                if chk != cur:
                    progress[key] = chk
                    save_topic(key, "ProjPython", pn, topic, chk)
                    st.rerun()

# ── ENEM ──────────────────────────────────────────────────────────────────
with tab_enem:
    st.markdown('<div style="background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:10px 14px;margin-bottom:16px"><div style="font-size:12px!important;color:#868e96">📌 ENEM é prioridade secundária — 30min por dia é suficiente. Foque em programação primeiro.</div></div>', unsafe_allow_html=True)
    mat_tabs = st.tabs([f"{v['icon']} {k}" for k,v in ENEM.items()])
    for mat_tab, (mn, md) in zip(mat_tabs, ENEM.items()):
        with mat_tab:
            done_m = sum(1 for t in md["topics"] if progress.get(make_enem_key(mn, t), False))
            total_m = len(md["topics"])
            pct_m = round(done_m/total_m*100,1) if total_m else 0
            cl, cr = st.columns([1,4])
            with cl:
                st.markdown(f'<div class="kpi" style="text-align:left"><div class="kpi-num" style="color:{md["color"]}">{pct_m}%</div><div class="kpi-lbl">{done_m}/{total_m}</div></div>', unsafe_allow_html=True)
            with cr:
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                st.progress(pct_m/100)
            st.markdown(f'<div class="sec-label">{md["icon"]} {mn}</div>', unsafe_allow_html=True)
            for topic in md["topics"]:
                key = make_enem_key(mn, topic)
                cur = progress.get(key, False)
                chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                if chk != cur:
                    progress[key] = chk
                    save_topic(key, "ENEM", mn, topic, chk)
                    if chk:
                        adicionar_revisao(key, mn, topic)
                        st.session_state.revisao_data = get_revisao_data()
                    st.rerun()

# ── REVISÃO SM-2 ──────────────────────────────────────────────────────────
with tab_rev:
    revisao_data = st.session_state.revisao_data
    due_today = get_due_today(revisao_data)
    due_list = list(due_today.items())

    if not revisao_data:
        st.markdown('<div style="text-align:center;padding:48px 0;color:#adb5bd"><div style="font-size:32px!important">📭</div><div style="font-size:14px!important;font-weight:600;color:#495057;margin-top:12px">Nenhum tópico na fila ainda</div><div style="font-size:12px!important;margin-top:6px">Marque tópicos na aba ENEM para começar a revisar.</div></div>', unsafe_allow_html=True)
    elif not due_list:
        proximas = sorted(revisao_data.items(), key=lambda x: x[1]["proxima_revisao"])
        prox_v = proximas[0][1]
        st.markdown(f'<div style="text-align:center;padding:40px 0"><div style="font-size:32px!important">✅</div><div style="font-size:14px!important;font-weight:600;color:#495057;margin-top:12px">Nenhuma revisão pendente hoje!</div><div style="font-size:12px!important;color:#adb5bd;margin-top:6px">Próxima: <b>{prox_v["topico"]}</b> em {prox_v["proxima_revisao"]}</div></div>', unsafe_allow_html=True)
    else:
        if st.session_state.revisao_atual is None or st.session_state.revisao_atual not in due_today:
            st.session_state.revisao_atual = due_list[0][0]
        cur_key = st.session_state.revisao_atual
        cur_item = due_today.get(cur_key, due_list[0][1])
        cur_rev = revisao_data.get(cur_key, {})
        intervalo = cur_rev.get("intervalo",1)
        repeticoes = cur_rev.get("repeticoes",0)
        facilidade = cur_rev.get("facilidade",2.5)
        idx = next((i for i,(k,_) in enumerate(due_list) if k==cur_key), 0)

        nc1,nc2,nc3 = st.columns([1,4,1])
        with nc1:
            if idx > 0 and st.button("← Anterior"): st.session_state.revisao_atual = due_list[idx-1][0]; st.rerun()
        with nc2:
            st.markdown(f'<div style="text-align:center;padding:6px 0"><span style="font-size:12px!important;color:#868e96">{idx+1} de {len(due_list)} pendentes hoje</span></div>', unsafe_allow_html=True)
        with nc3:
            if idx < len(due_list)-1 and st.button("Próximo →"): st.session_state.revisao_atual = due_list[idx+1][0]; st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        materia_icon = ENEM.get(cur_item["materia"],{}).get("icon","📚")
        materia_cor  = ENEM.get(cur_item["materia"],{}).get("color","#1a1a2e")
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e9ecef;border-radius:12px;
                    padding:28px 32px;text-align:center;max-width:560px;margin:0 auto">
            <div style="font-size:11px!important;color:{materia_cor};letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">
                {materia_icon} {cur_item['materia']}
            </div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:18px!important;font-weight:700;color:#1a1a2e;margin-bottom:6px">
                {cur_item['topico']}
            </div>
            <div style="font-size:11px!important;color:#adb5bd;margin-bottom:24px">
                Revisão nº {repeticoes+1} · Intervalo atual: {intervalo} dia(s)
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:13px!important;font-weight:600;color:#212529;margin-bottom:14px">Como foi sua lembrança desse tópico?</div>', unsafe_allow_html=True)

        bc1,bc2,bc3,bc4 = st.columns(4)
        for col,nota,emoji,label,cor,hint in [
            (bc1,0,"😰","Não lembro","#c62828","Volta amanhã"),
            (bc2,1,"😅","Difícil","#e65100","~2 dias"),
            (bc3,2,"🙂","Médio","#1565c0","~4 dias"),
            (bc4,3,"😎","Fácil","#2e7d32","~7 dias"),
        ]:
            with col:
                st.markdown(f'<div style="text-align:center;margin-bottom:6px"><div style="font-size:22px!important">{emoji}</div><div style="font-size:11px!important;color:{cor};font-weight:600">{label}</div><div style="font-size:10px!important;color:#adb5bd">{hint}</div></div>', unsafe_allow_html=True)
                if st.button(label, key=f"nota_{nota}_{cur_key}", use_container_width=True):
                    ni,nf,nr,np = sm2_update(intervalo,facilidade,repeticoes,nota)
                    save_revisao(cur_key,cur_item["materia"],cur_item["topico"],ni,nf,nr,np,nota)
                    st.session_state.revisao_data = get_revisao_data()
                    remaining = [(k,v) for k,v in due_list if k!=cur_key]
                    st.session_state.revisao_atual = remaining[0][0] if remaining else None
                    st.success(f"Salvo! Próxima revisão em {ni} dia(s) — {np}")
                    st.rerun()

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Todas as revisões agendadas</div>', unsafe_allow_html=True)
        for rk,rv in sorted(revisao_data.items(), key=lambda x: x[1]["proxima_revisao"]):
            is_due = rv["proxima_revisao"] <= date.today().isoformat()
            icon_m = ENEM.get(rv["materia"],{}).get("icon","📚")
            bg = "#fff3cd" if is_due else "#fff"
            bc_c = "#ffc107" if is_due else "#e9ecef"
            tag = "HOJE" if is_due else rv["proxima_revisao"]
            tc = "#856404" if is_due else "#adb5bd"
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;background:{bg};border:1px solid {bc_c};border-radius:6px;padding:8px 12px;margin-bottom:4px"><span style="font-size:12px!important;color:#212529">{icon_m} <b>{rv["materia"]}</b> · {rv["topico"]}</span><span style="font-size:10px!important;color:{tc};font-weight:600">{tag} · {rv["repeticoes"]}x · {rv["intervalo"]}d</span></div>', unsafe_allow_html=True)


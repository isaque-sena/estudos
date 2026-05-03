import streamlit as st
import sqlite3
import math
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
    conn.commit(); conn.close()

def export_csv():
    conn = get_conn()
    rows = conn.execute("SELECT area,secao,topico,concluido,atualizado_em FROM progresso ORDER BY area,secao").fetchall()
    conn.close()
    lines = ["area,secao,topico,concluido,atualizado_em"]
    for r in rows:
        lines.append(f'"{r[0]}","{r[1]}","{r[2]}","{"Sim" if r[3] else "Nao"}","{r[4] or ""}"')
    return "\n".join(lines)

def make_key(area, secao, topico):
    return f"{area}||{secao}||{topico}"

# ── Calendário ────────────────────────────────────────────────────────────
CALENDARIO = {
    "Segunda": [
        {"bloco": "Bloco 1 — 1h30", "area": "C — Lógica", "icon": "⚙️", "cor": "#1565c0",
         "desc": "CS50 ou exercícios de algoritmo"},
        {"bloco": "Bloco 2 — 1h30", "area": "Python Conceitos", "icon": "🐍", "cor": "#2e7d32",
         "desc": "Fundamentos, funções, estruturas de dados"},
        {"bloco": "Bloco 3 — 30min", "area": "Leitura", "icon": "📖", "cor": "#5c6bc0",
         "desc": "Artigo técnico ou livro — leia e interprete"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Podcast Syntax.fm ou vídeo Fireship"},
    ],
    "Terça": [
        {"bloco": "Bloco 1 — 1h30", "area": "C — Lógica", "icon": "⚙️", "cor": "#1565c0",
         "desc": "CS50 ou exercícios de algoritmo"},
        {"bloco": "Bloco 2 — 1h30", "area": "SQL Avançado", "icon": "🗄️", "cor": "#6a1b9a",
         "desc": "Window functions, CTEs, performance"},
        {"bloco": "Bloco 3 — 30min", "area": "Matemática", "icon": "📐", "cor": "#00695c",
         "desc": "Trilha: Álgebra → Funções → Cálculo"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Ler documentação técnica em inglês"},
    ],
    "Quarta": [
        {"bloco": "Bloco 1 — 1h30", "area": "C — Lógica", "icon": "⚙️", "cor": "#1565c0",
         "desc": "CS50 ou exercícios de algoritmo"},
        {"bloco": "Bloco 2 — 45min", "area": "Power BI", "icon": "📊", "cor": "#c62828",
         "desc": "DAX, modelagem, dashboard"},
        {"bloco": "Bloco 3 — 45min", "area": "Git Profissional", "icon": "🌿", "cor": "#c62828",
         "desc": "Branches, commits semânticos, README"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Podcast ou vídeo técnico"},
    ],
    "Quinta": [
        {"bloco": "Bloco 1 — 1h30", "area": "C — Lógica", "icon": "⚙️", "cor": "#1565c0",
         "desc": "CS50 ou exercícios de algoritmo"},
        {"bloco": "Bloco 2 — 1h30", "area": "Python Projetos", "icon": "🚀", "cor": "#00695c",
         "desc": "Construir e avançar no projeto atual"},
        {"bloco": "Bloco 3 — 30min", "area": "Leitura", "icon": "📖", "cor": "#5c6bc0",
         "desc": "Artigo, documentação ou livro técnico"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Anki vocabulário técnico"},
    ],
    "Sexta": [
        {"bloco": "Bloco 1 — 1h", "area": "APIs REST", "icon": "🔌", "cor": "#c62828",
         "desc": "FastAPI — endpoints, validação, deploy"},
        {"bloco": "Bloco 2 — 1h", "area": "Pandas Avançado", "icon": "🐼", "cor": "#c62828",
         "desc": "merge, groupby, apply, otimização"},
        {"bloco": "Bloco 3 — 30min", "area": "Matemática", "icon": "📐", "cor": "#00695c",
         "desc": "Continuar a trilha de matemática"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Série ou filme com legenda em inglês"},
    ],
    "Sábado": [
        {"bloco": "Bloco 1 — 1h", "area": "Python Projetos", "icon": "🚀", "cor": "#00695c",
         "desc": "Avançar no projeto + boas práticas"},
        {"bloco": "Bloco 2 — 30min", "area": "Leitura", "icon": "📖", "cor": "#5c6bc0",
         "desc": "Leitura livre — técnica ou não técnica"},
        {"bloco": "Passivo", "area": "Inglês", "icon": "🌐", "cor": "#e65100",
         "desc": "Série ou podcast — sem pressão"},
    ],
    "Domingo": [
        {"bloco": "Descanso", "area": "Descanso 😴", "icon": "😴", "cor": "#90a4ae",
         "desc": "O cérebro consolida o aprendizado dormindo. Descanse."},
    ],
}

# ── Python Conceitos ──────────────────────────────────────────────────────
PYTHON_CONCEITOS = {
    "Fundamentos": {"icon": "🔢", "color": "#1565c0", "topics": [
        "Variáveis e tipos (int, float, str, bool)",
        "Conversão de tipos (int(), float(), str())",
        "Operadores aritméticos (+, -, *, /, //, %, **)",
        "Operadores de comparação (==, !=, >, <, >=, <=)",
        "Operadores lógicos (and, or, not)",
        "Operadores de atribuição (+=, -=, *=)",
        "f-strings e formatação de strings",
        "Input e output (input(), print())",
    ]},
    "Estruturas de Controle": {"icon": "🔀", "color": "#6a1b9a", "topics": [
        "if / elif / else",
        "Operador ternário",
        "for loop — percorrer listas",
        "for loop — range(inicio, fim, passo)",
        "while loop",
        "break e continue",
        "enumerate() — índice + valor",
        "zip() — duas listas ao mesmo tempo",
    ]},
    "Funções": {"icon": "⚡", "color": "#2e7d32", "topics": [
        "Definir funções com def",
        "Parâmetros e argumentos",
        "Valor de retorno (return)",
        "Valores padrão de parâmetros",
        "Argumentos nomeados",
        "*args — número variável de argumentos",
        "**kwargs — argumentos nomeados variáveis",
        "Funções lambda",
        "Escopo de variáveis (local vs global)",
        "Recursão — fatorial e fibonacci",
    ]},
    "Estruturas de Dados": {"icon": "📦", "color": "#e65100", "topics": [
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
    ]},
    "Strings Avançado": {"icon": "📝", "color": "#880e4f", "topics": [
        ".strip() .upper() .lower() .title()",
        ".replace() .split() .join()",
        ".startswith() .endswith() .find()",
        ".count() e len()",
        "f-string formatação avançada",
        "Expressões regulares básicas (re)",
    ]},
    "Orientação a Objetos": {"icon": "🏗️", "color": "#4a148c", "topics": [
        "Classes e objetos",
        "__init__ e self",
        "Atributos e métodos",
        "Herança e super()",
        "Encapsulamento",
        "@property",
        "Métodos especiais (__str__, __repr__)",
    ]},
    "Tratamento de Erros": {"icon": "🛡️", "color": "#c62828", "topics": [
        "try / except / finally",
        "Tipos de erros (ValueError, TypeError, KeyError)",
        "Capturar mensagem do erro (as e)",
        "Exceções customizadas",
        "else no try/except",
    ]},
    "Módulos e Arquivos": {"icon": "📁", "color": "#00695c", "topics": [
        "import e from...import",
        "Módulos math, random, datetime, os, json",
        "Leitura de arquivos (with open, read, readlines)",
        "Escrita de arquivos (write, writelines)",
        "Leitura e escrita de JSON",
    ]},
}

# ── Python Projetos ───────────────────────────────────────────────────────
PYTHON_PROJETOS = {
    "Projeto 1 — Analisador de Gastos": {
        "icon": "💰", "color": "#1565c0", "nivel": "Básico",
        "desc": "Importa CSV de gastos e exibe resumo por categoria com gráficos.",
        "topics": ["pandas — leitura de CSV","pandas — groupby","pandas — filtros",
                   "matplotlib — gráfico de barras","matplotlib — gráfico de pizza",
                   "f-strings e formatação","tratamento de erros básico"]},
    "Projeto 2 — Buscador de Vagas": {
        "icon": "🔍", "color": "#1565c0", "nivel": "Básico",
        "desc": "Busca vagas em APIs e salva em CSV organizado.",
        "topics": ["requests — HTTP","BeautifulSoup — HTML","dicionários",
                   "salvamento em CSV","try/except rede","loops e filtragem"]},
    "Projeto 3 — Dashboard BACEN/IBGE": {
        "icon": "📈", "color": "#1565c0", "nivel": "Básico",
        "desc": "Puxa IPCA, SELIC e câmbio e exibe num dashboard Streamlit.",
        "topics": ["requests — APIs REST","pandas — JSON para DataFrame",
                   "Streamlit básico","Streamlit sidebar","plotly interativo","st.cache_data"]},
    "Projeto 4 — ETL de Planilha": {
        "icon": "🔄", "color": "#1565c0", "nivel": "Básico",
        "desc": "Recebe planilha bagunçada, limpa e gera relatório Excel.",
        "topics": ["pandas — Excel openpyxl","pandas — limpeza strings",
                   "pandas — duplicatas","pandas — nulos","pandas — exportar Excel","funções reutilizáveis"]},
    "Projeto 5 — Gerador de Relatório PDF": {
        "icon": "📄", "color": "#1565c0", "nivel": "Básico",
        "desc": "Lê dados de CSV e gera PDF com tabelas e gráficos automaticamente.",
        "topics": ["pandas — métricas","reportlab — PDF","matplotlib — imagem",
                   "automação de documentos","formatação de tabelas"]},
    "Projeto 6 — Pipeline com Banco": {
        "icon": "🗄️", "color": "#e65100", "nivel": "Intermediário",
        "desc": "Coleta dados de API, transforma e armazena em SQLite automaticamente.",
        "topics": ["SQLAlchemy","SQLite","schedule","SQL INSERT SELECT UPDATE","conceitos de pipeline"]},
    "Projeto 7 — Dashboard Financeiro B3": {
        "icon": "💹", "color": "#e65100", "nivel": "Intermediário",
        "desc": "Puxa ações da B3 com yfinance e exibe indicadores técnicos.",
        "topics": ["yfinance","pandas — médias móveis","plotly candlestick",
                   "Streamlit avançado","seleção dinâmica de ativos"]},
    "Projeto 8 — API com FastAPI": {
        "icon": "🔌", "color": "#e65100", "nivel": "Intermediário",
        "desc": "Cria API REST que recebe CSV, processa e retorna métricas em JSON.",
        "topics": ["FastAPI básico","Pydantic","uvicorn","endpoints GET POST",
                   "upload de arquivos","documentação automática"]},
    "Projeto 9 — Agente com LLM": {
        "icon": "🤖", "color": "#4a148c", "nivel": "Avançado",
        "desc": "Agente que analisa CSV e responde perguntas via Groq API.",
        "topics": ["Groq API","prompt engineering","LLM + pandas","contexto dinâmico","JSON responses"]},
    "Projeto 10 — Colmeia de Agentes": {
        "icon": "🐝", "color": "#4a148c", "nivel": "Avançado",
        "desc": "Sistema multi-agentes CLI com memória e agentes especializados.",
        "topics": ["arquitetura de agentes","memória comprimida","Groq API avançada",
                   "CLI com Rich","design de sistemas","Playwright"]},
}

# ── C Módulos ─────────────────────────────────────────────────────────────
C_MODULOS = {
    "Módulo 1 — Fundamentos": {"icon": "🔧", "color": "#1565c0", "topics": [
        "variáveis e tipos int float char","sizeof e memória","operadores aritméticos",
        "operadores de comparação","operadores lógicos AND OR NOT","printf e scanf","gcc"]},
    "Módulo 2 — Controle de Fluxo": {"icon": "🔀", "color": "#1565c0", "topics": [
        "if else if else","operador ternário","switch case","for com contador","while e do while","break e continue"]},
    "Módulo 3 — Funções": {"icon": "⚡", "color": "#1565c0", "topics": [
        "declaração e definição","parâmetros e retorno","void","escopo",
        "recursão fatorial","recursão fibonacci","protótipos"]},
    "Módulo 4 — Arrays": {"icon": "📦", "color": "#1565c0", "topics": [
        "declaração","acesso por índice","percorrer com for","arrays em funções",
        "strings char[]","strlen strcpy","matrizes 2D"]},
    "Módulo 5 — Ponteiros": {"icon": "👉", "color": "#1565c0", "topics": [
        "o que é um ponteiro","& e *","ponteiro e array","passagem por referência",
        "aritmética de ponteiros","malloc e free"]},
    "Módulo 6 — Structs e Algoritmos": {"icon": "🏗️", "color": "#1565c0", "topics": [
        "struct","array de structs","busca linear","busca binária",
        "bubble sort","selection sort","insertion sort"]},
}

# ── SQL ───────────────────────────────────────────────────────────────────
SQL_MODULOS = {
    "SQL Básico": {"icon": "🔍", "color": "#6a1b9a", "topics": [
        "SELECT e FROM","WHERE filtros","ORDER BY","LIMIT","DISTINCT","AND OR NOT","LIKE padrão"]},
    "SQL Intermediário": {"icon": "🔗", "color": "#6a1b9a", "topics": [
        "GROUP BY","HAVING","COUNT SUM AVG MAX MIN","INNER JOIN","LEFT JOIN","subqueries","CREATE TABLE"]},
    "SQL Avançado 🔴": {"icon": "⚡", "color": "#c62828", "topics": [
        "Window functions — ROW_NUMBER()","Window functions — RANK() e DENSE_RANK()",
        "Window functions — LAG() e LEAD()","Window functions — SUM() OVER (PARTITION BY)",
        "CTEs — WITH nome AS (...)","CTEs recursivas","Subquery vs CTE",
        "Índices — o que são e por que importam","EXPLAIN ANALYZE — plano de execução",
        "Performance — evitar SELECT *","Performance — índices compostos",
        "Transações — BEGIN COMMIT ROLLBACK","Views e Materialized Views"]},
}

# ── Power BI ──────────────────────────────────────────────────────────────
POWERBI_MODULOS = {
    "Power BI Essencial": {"icon": "📊", "color": "#c62828", "topics": [
        "importar CSV e Excel","Power Query limpeza","relacionamentos entre tabelas",
        "DAX SUM COUNT AVERAGE","DAX CALCULATE e filtros","DAX RELATED e LOOKUPVALUE",
        "visuais barras linha pizza","filtros e segmentações","publicar no Power BI Service"]},
}

# ── Inglês ────────────────────────────────────────────────────────────────
INGLES_MODULOS = {
    "Vocabulário Técnico": {"icon": "💬", "color": "#e65100", "topics": [
        "termos de programação (function, array, loop, variable)",
        "termos de dados (dataset, query, pipeline, aggregation)",
        "termos de IA (model, inference, embedding, token)",
        "erros em inglês (TypeError, KeyError, undefined)",
        "verbos técnicos (deploy, fetch, parse, render, compile)"]},
    "Leitura Técnica": {"icon": "📖", "color": "#e65100", "topics": [
        "documentação do Python em inglês","documentação do pandas em inglês",
        "artigos no Dev.to ou Medium","Stack Overflow sem tradutor","README no GitHub"]},
    "Listening": {"icon": "🎧", "color": "#e65100", "topics": [
        "Podcast Syntax.fm — 3 episódios","Canal Fireship — 10 vídeos",
        "CS50 em inglês com legenda EN","TED Talks técnicos — 5 assistidos"]},
}

# ── Leitura e Interpretação ───────────────────────────────────────────────
LEITURA_MODULOS = {
    "Leitura Técnica em PT": {"icon": "📘", "color": "#5c6bc0", "topics": [
        "Ler 1 artigo técnico por semana — Dev.to em PT",
        "Ler documentação de biblioteca — pandas docs",
        "Resumir em 3 frases o que entendeu",
        "Identificar argumento principal do texto",
        "Identificar exemplos e evidências usados",
        "Ler post-mortem de incidente técnico",
        "Ler README de projeto open source",
    ]},
    "Leitura Técnica em EN": {"icon": "📗", "color": "#5c6bc0", "topics": [
        "Ler 1 artigo técnico por semana — Medium ou Dev.to",
        "Ler changelog de biblioteca (pandas, FastAPI, Streamlit)",
        "Ler thread técnica no Stack Overflow sem tradutor",
        "Identificar palavras desconhecidas e anotar",
        "Resumir artigo em inglês com suas próprias palavras",
    ]},
    "Interpretação de Código": {"icon": "🔬", "color": "#5c6bc0", "topics": [
        "Ler código de projeto open source no GitHub",
        "Explicar em português o que cada função faz",
        "Identificar padrões — acumulador, busca, transformação",
        "Rastrear o fluxo de dados de entrada até saída",
        "Entender mensagens de erro sem buscar no Google",
        "Ler código de colega e dar feedback construtivo",
    ]},
    "Livros Técnicos": {"icon": "📚", "color": "#5c6bc0", "topics": [
        "Python Fluente — capítulos 1 ao 5",
        "Clean Code — capítulos sobre funções e nomes",
        "The Pragmatic Programmer — 3 capítulos",
        "Pense em Python — Allen Downey (gratuito em PT)",
        "Estruturas de Dados com Python — capítulos 1 ao 4",
    ]},
}

# ── Matemática — trilha do zero ao Cálculo ────────────────────────────────
MATEMATICA_MODULOS = {
    "Etapa 1 — Álgebra Básica": {"icon": "🔢", "color": "#00695c", "topics": [
        "Expressões algébricas — simplificar e substituir",
        "Equações de 1º grau — isolar variável",
        "Equações de 2º grau — fórmula de Bhaskara",
        "Sistemas de equações — substituição e adição",
        "Inequações de 1º grau — maior, menor, intervalo",
        "Inequações de 2º grau — parábola e sinal",
        "Fatoração — produto notável e fator comum",
        "Frações algébricas — simplificar e operar",
        "Módulo — |x| e inequações com módulo",
    ]},
    "Etapa 2 — Funções": {"icon": "📈", "color": "#00695c", "topics": [
        "O que é uma função — domínio, imagem, contradomínio",
        "Gráfico no plano cartesiano",
        "Função afim — f(x) = ax + b",
        "Função quadrática — f(x) = ax² + bx + c",
        "Vértice da parábola e concavidade",
        "Função modular — f(x) = |x|",
        "Função definida por partes",
        "Composição de funções — f(g(x))",
        "Função inversa — f⁻¹(x)",
        "Injetora, sobrejetora e bijetora",
    ]},
    "Etapa 3 — Exponenciais e Logaritmos": {"icon": "🔁", "color": "#00695c", "topics": [
        "Potências — base, expoente, operações",
        "Potência com expoente negativo e fracionário",
        "Função exponencial — f(x) = aˣ",
        "Gráfico da exponencial — crescimento e decrescimento",
        "Definição de logaritmo — log_a(b) = c",
        "Propriedades dos logaritmos (produto, quociente, potência)",
        "Logaritmo natural — ln(x)",
        "Equações exponenciais",
        "Equações logarítmicas",
        "Aplicações — crescimento populacional, juros compostos",
    ]},
    "Etapa 4 — Trigonometria": {"icon": "📐", "color": "#00695c", "topics": [
        "Ângulos — graus e radianos",
        "Seno, cosseno e tangente no triângulo retângulo",
        "Círculo trigonométrico",
        "Valores notáveis — 30°, 45°, 60°, 90°",
        "Funções trigonométricas — f(x) = sen(x), cos(x), tan(x)",
        "Gráfico de seno e cosseno — período e amplitude",
        "Identidades trigonométricas básicas",
        "Equações trigonométricas simples",
    ]},
    "Etapa 5 — Limites e Continuidade": {"icon": "🎯", "color": "#00695c", "topics": [
        "Ideia intuitiva de limite",
        "Notação — lim f(x) quando x→a",
        "Limites laterais — esquerda e direita",
        "Limite no infinito — x→+∞ e x→-∞",
        "Formas indeterminadas — 0/0 e ∞/∞",
        "Técnica — fatorar para eliminar indeterminação",
        "Técnica — dividir pelo maior grau",
        "Limites trigonométricos — sen(x)/x quando x→0",
        "Continuidade — definição e verificação",
        "Descontinuidade — removível e essencial",
    ]},
    "Etapa 6 — Derivadas": {"icon": "📉", "color": "#00695c", "topics": [
        "O que é a derivada — taxa de variação",
        "Definição formal — limite do quociente",
        "Derivada de constante — f(x)=c → f'(x)=0",
        "Derivada de xⁿ — regra da potência",
        "Derivada de sen(x), cos(x), eˣ, ln(x)",
        "Regra da soma e diferença",
        "Regra do produto — (f·g)'",
        "Regra do quociente — (f/g)'",
        "Regra da cadeia — f(g(x))'",
        "Derivada de funções compostas",
        "Análise de gráfico pela derivada — crescimento e decrescimento",
        "Pontos críticos — máximo e mínimo",
        "Problemas de otimização",
    ]},
    "Etapa 7 — Integrais": {"icon": "∫", "color": "#00695c", "topics": [
        "O que é a integral — área sob a curva",
        "Integral como operação inversa da derivada",
        "Integral de constante e de xⁿ",
        "Integral de sen(x), cos(x), eˣ, 1/x",
        "Regra da soma e diferença",
        "Constante de integração C",
        "Método da substituição — u-substitution",
        "Integração por partes — ∫u dv = uv - ∫v du",
        "Integral definida — Teorema Fundamental do Cálculo",
        "Cálculo de área entre curvas",
    ]},
}

# ── Carreira Alta ─────────────────────────────────────────────────────────
CARREIRA_ALTA = {
    "Git Profissional 🔴": {"icon": "🌿", "color": "#c62828", "topics": [
        "git init add commit push pull","branches — criar trocar deletar",
        "merge e rebase","git stash","resolução de conflitos",
        "commits semânticos — feat: fix: docs: refactor:","README profissional",
        ".gitignore para Python","Pull Requests","GitHub Actions CI básico"]},
    "Python Boas Práticas 🔴": {"icon": "✨", "color": "#c62828", "topics": [
        "Estrutura de projeto — src/ tests/ docs/","PEP8 — convenções",
        "Black e isort — formatação automática","Type hints — def fn(x: int) -> str:",
        "Docstrings — Google style","Funções com responsabilidade única",
        "DRY — Don't Repeat Yourself","requirements.txt e pyproject.toml","venv e pip"]},
    "APIs REST 🔴": {"icon": "🔌", "color": "#c62828", "topics": [
        "REST — GET POST PUT DELETE","Status codes — 200 201 400 404 500",
        "requests — GET e POST com headers","Bearer token — autenticação",
        "FastAPI estrutura básica","FastAPI endpoints GET e POST",
        "Pydantic — validação","FastAPI upload de arquivo",
        "Swagger — documentação automática","variáveis de ambiente .env"]},
    "Pandas Avançado 🔴": {"icon": "🐼", "color": "#c62828", "topics": [
        "merge — inner left right outer","concat — empilhar DataFrames",
        "groupby + agg — múltiplas agregações","apply — função customizada",
        "transform — manter shape original","pivot_table",
        "melt — wide para long","query() — filtros com string",
        "category dtype — otimização","chunksize — arquivos grandes"]},
}

# ── Carreira Média ────────────────────────────────────────────────────────
CARREIRA_MEDIA = {
    "Modelagem de Dados 🟡": {"icon": "🗂️", "color": "#e65100", "topics": [
        "Tipos de dados — int varchar decimal timestamp",
        "Chave primária e estrangeira","Normalização — 1NF 2NF 3NF",
        "Relacionamentos — 1:1 1:N N:N","Diagrama ER",
        "Star schema — fato e dimensão","Snowflake schema","Quando desnormalizar"]},
    "Deploy Básico 🟡": {"icon": "🚀", "color": "#e65100", "topics": [
        "Variáveis de ambiente — .env e python-dotenv","Streamlit Cloud",
        "Render — FastAPI gratuito","Railway — banco na nuvem",
        "requirements.txt para deploy","Logs e monitoramento básico"]},
    "Testes com Pytest 🟡": {"icon": "🧪", "color": "#e65100", "topics": [
        "O que é um teste e por que escrever","pytest — primeiro teste",
        "assert — verificar resultados","Fixtures — setup reutilizável",
        "Testar funções de dados com pandas","Testar endpoints FastAPI",
        "coverage — percentual testado"]},
    "Estatística Aplicada 🟡": {"icon": "📊", "color": "#e65100", "topics": [
        "Média mediana moda — quando usar","Desvio padrão e variância",
        "Distribuição normal","Correlação — Pearson e Spearman",
        "Regressão linear simples","Teste A/B","Intervalo de confiança","p-valor"]},
}

# ── Carreira Longo Prazo ──────────────────────────────────────────────────
CARREIRA_LONGO = {
    "LLMs na Prática 🟢": {"icon": "🤖", "color": "#2e7d32", "topics": [
        "Como funcionam LLMs — tokens e atenção","Prompt engineering",
        "Groq API","OpenAI API","RAG — Retrieval Augmented Generation",
        "Embeddings","LangChain chains","FAISS — busca por similaridade","Fine-tuning"]},
    "Orquestração de Pipelines 🟢": {"icon": "🔄", "color": "#2e7d32", "topics": [
        "O que é orquestração","Prefect — primeiro flow",
        "Prefect — tasks e dependências","Prefect — agendamento","Airflow — DAGs"]},
    "Cloud Básico 🟢": {"icon": "☁️", "color": "#2e7d32", "topics": [
        "IaaS PaaS SaaS","AWS S3","AWS Lambda","AWS RDS",
        "GCP BigQuery","GCP Cloud Run","Custos — não estourar a fatura"]},
}

# ── Init ──────────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()
progress = st.session_state.progress

# ── Stats ─────────────────────────────────────────────────────────────────
def count_done(modulos, key_fn):
    total = sum(len(v["topics"]) for v in modulos.values())
    done  = sum(1 for mn,md in modulos.items()
                for t in md["topics"] if progress.get(key_fn(mn,t), False))
    return done, total

def proj_stats():
    total = sum(len(v["topics"]) for v in PYTHON_PROJETOS.values())
    done  = sum(1 for pn,pd in PYTHON_PROJETOS.items()
                for t in pd["topics"] if progress.get(make_key("ProjPython",pn,t), False))
    return done, total

done_conc,  total_conc  = count_done(PYTHON_CONCEITOS, lambda mn,t: make_key("PyConc",mn,t))
done_proj,  total_proj  = proj_stats()
done_c,     total_c     = count_done(C_MODULOS,         lambda mn,t: make_key("C",mn,t))
done_sql,   total_sql   = count_done(SQL_MODULOS,       lambda mn,t: make_key("SQL",mn,t))
done_pbi,   total_pbi   = count_done(POWERBI_MODULOS,   lambda mn,t: make_key("PBI",mn,t))
done_en,    total_en    = count_done(INGLES_MODULOS,    lambda mn,t: make_key("EN",mn,t))
done_leit,  total_leit  = count_done(LEITURA_MODULOS,   lambda mn,t: make_key("Leit",mn,t))
done_mat,   total_mat   = count_done(MATEMATICA_MODULOS,lambda mn,t: make_key("Mat",mn,t))
done_alta,  total_alta  = count_done(CARREIRA_ALTA,     lambda mn,t: make_key("Alta",mn,t))
done_media, total_media = count_done(CARREIRA_MEDIA,    lambda mn,t: make_key("Media",mn,t))
done_longo, total_longo = count_done(CARREIRA_LONGO,    lambda mn,t: make_key("Longo",mn,t))

done_prog  = done_conc+done_proj+done_c+done_sql+done_pbi+done_alta+done_media
total_prog = total_conc+total_proj+total_c+total_sql+total_pbi+total_alta+total_media
pct_prog   = round(done_prog/total_prog*100,1) if total_prog else 0
pct_en     = round(done_en/total_en*100,1)     if total_en   else 0
pct_leit   = round(done_leit/total_leit*100,1) if total_leit else 0
pct_mat    = round(done_mat/total_mat*100,1)   if total_mat  else 0

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
.stDownloadButton button,button[kind="secondary"]{font-size:12px!important;border-radius:6px!important;background:#fff!important;border:1px solid #e9ecef!important;color:#495057!important}
.sidebar-title{font-family:'Space Grotesk',sans-serif!important;font-size:15px!important;font-weight:700;color:#1a1a2e}
.sidebar-sub{font-size:10px!important;color:#adb5bd;letter-spacing:.08em}
hr{border-color:#e9ecef!important}
</style>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
def sidebar_bloco(icon, label, done, total, pct, cor="#1565c0"):
    st.markdown(f"""
    <div style="background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;
                padding:10px 12px;margin-bottom:6px">
        <div style="display:flex;justify-content:space-between">
            <span style="font-size:12px!important;font-weight:600;color:#212529">{icon} {label}</span>
            <span style="font-size:11px!important;color:{cor};font-weight:600">{pct}%</span>
        </div>
        <div style="font-size:10px!important;color:#adb5bd;margin:2px 0 6px">{done}/{total} tópicos</div>
    </div>""", unsafe_allow_html=True)
    st.progress(pct/100)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div style="padding:8px 0 16px"><div class="sidebar-title">🧠 Tracker</div><div class="sidebar-sub">ISAQUE SENA · SENALABS</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<div style="font-size:11px!important;font-weight:600;color:#495057;margin-bottom:8px">💻 PROGRAMAÇÃO</div>', unsafe_allow_html=True)
    sidebar_bloco("🐍","Python Conceitos", done_conc, total_conc, round(done_conc/total_conc*100) if total_conc else 0, "#2e7d32")
    sidebar_bloco("🚀","Python Projetos",  done_proj, total_proj, round(done_proj/total_proj*100) if total_proj else 0, "#00695c")
    sidebar_bloco("⚙️","C — Lógica",       done_c,    total_c,    round(done_c/total_c*100) if total_c else 0, "#1565c0")
    sidebar_bloco("🗄️","SQL",              done_sql,  total_sql,  round(done_sql/total_sql*100) if total_sql else 0, "#6a1b9a")
    sidebar_bloco("📊","Power BI",         done_pbi,  total_pbi,  round(done_pbi/total_pbi*100) if total_pbi else 0, "#c62828")
    sidebar_bloco("🔴","Alta Prioridade",  done_alta, total_alta, round(done_alta/total_alta*100) if total_alta else 0, "#c62828")
    sidebar_bloco("🟡","Média Prioridade", done_media,total_media,round(done_media/total_media*100) if total_media else 0, "#e65100")
    sidebar_bloco("🟢","Longo Prazo",      done_longo,total_longo,round(done_longo/total_longo*100) if total_longo else 0, "#2e7d32")

    st.markdown('<div style="font-size:11px!important;font-weight:600;color:#495057;margin:12px 0 8px">📐 MATEMÁTICA</div>', unsafe_allow_html=True)
    sidebar_bloco("📐","Matemática",       done_mat,  total_mat,  round(done_mat/total_mat*100) if total_mat else 0, "#00695c")

    st.markdown('<div style="font-size:11px!important;font-weight:600;color:#495057;margin:12px 0 8px">📚 HABILIDADES</div>', unsafe_allow_html=True)
    sidebar_bloco("🌐","Inglês",           done_en,   total_en,   round(done_en/total_en*100) if total_en else 0, "#e65100")
    sidebar_bloco("📖","Leitura",          done_leit, total_leit, round(done_leit/total_leit*100) if total_leit else 0, "#5c6bc0")

    st.markdown("---")
    st.download_button("⬇️ Exportar CSV", data=export_csv(),
        file_name=f"progresso_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv", use_container_width=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Resetar progresso", use_container_width=True, type="secondary"):
        reset_all()
        st.session_state.progress = {}
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Trilha de Estudos</div><div class="page-sub">MARQUE O QUE JÁ ESTUDOU · SALVO AUTOMATICAMENTE</div>', unsafe_allow_html=True)

c1,c2,c3,c4,c5 = st.columns(5)
for col,num,lbl,cor in [
    (c1, f"{pct_prog}%",  "PROGRAMAÇÃO", "#1565c0"),
    (c2, f"{pct_mat}%",   "MATEMÁTICA",  "#00695c"),
    (c3, f"{pct_en}%",    "INGLÊS",      "#e65100"),
    (c4, f"{pct_leit}%",  "LEITURA",     "#5c6bc0"),
    (c5, f"{round((done_prog+done_mat+done_en+done_leit)/(total_prog+total_mat+total_en+total_leit)*100,1) if (total_prog+total_mat+total_en+total_leit) else 0}%", "GERAL", "#212529"),
]:
    with col:
        st.markdown(f'<div class="kpi"><div class="kpi-num" style="color:{cor}">{num}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["📅 Calendário","🐍 Py Conceitos","🚀 Py Projetos",
                "⚙️ C — Lógica","🗄️ SQL","📊 Power BI",
                "📐 Matemática","🌐 Inglês","📖 Leitura","🎯 Carreira"])
tab_cal,tab_conc,tab_proj,tab_c,tab_sql,tab_pbi,tab_mat,tab_en,tab_leit,tab_car = tabs

# ── helper ────────────────────────────────────────────────────────────────
def render_modulos(modulos, prefix, tab):
    with tab:
        subtabs = st.tabs([f"{v['icon']} {k}" for k,v in modulos.items()])
        for subtab,(mn,md) in zip(subtabs, modulos.items()):
            with subtab:
                done_m = sum(1 for t in md["topics"] if progress.get(make_key(prefix,mn,t), False))
                total_m = len(md["topics"])
                pct_m = round(done_m/total_m*100,1) if total_m else 0
                cl,cr = st.columns([1,4])
                with cl:
                    st.markdown(f'<div class="kpi" style="text-align:left"><div class="kpi-num" style="color:{md["color"]}">{pct_m}%</div><div class="kpi-lbl">{done_m}/{total_m}</div></div>', unsafe_allow_html=True)
                with cr:
                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    st.progress(pct_m/100)
                st.markdown(f'<div class="sec-label">{md["icon"]} {mn}</div>', unsafe_allow_html=True)
                for topic in md["topics"]:
                    key = make_key(prefix,mn,topic)
                    cur = progress.get(key, False)
                    chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                    if chk != cur:
                        progress[key] = chk
                        save_topic(key, prefix, mn, topic, chk)
                        st.rerun()

# ── CALENDÁRIO ────────────────────────────────────────────────────────────
with tab_cal:
    hoje = date.today()
    dias_pt = {"Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta",
               "Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"}
    dia_hoje = dias_pt.get(hoje.strftime("%A"), "Segunda")

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e9ecef;border-radius:10px;
                padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;gap:14px">
        <div style="font-size:28px!important">📅</div>
        <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:15px!important;font-weight:700;color:#212529">
                Hoje é {dia_hoje}, {hoje.strftime('%d/%m/%Y')}
            </div>
            <div style="font-size:11px!important;color:#adb5bd;margin-top:2px">
                Veja o que estudar hoje e a programação da semana
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if dia_hoje in CALENDARIO:
        st.markdown('<div class="sec-label">📌 Hoje</div>', unsafe_allow_html=True)
        blocos_hoje = CALENDARIO[dia_hoje]
        cols_hoje = st.columns(len(blocos_hoje))
        for col, bloco in zip(cols_hoje, blocos_hoje):
            with col:
                st.markdown(f"""
                <div style="background:{bloco['cor']}10;border:1px solid {bloco['cor']}40;
                            border-left:4px solid {bloco['cor']};border-radius:8px;padding:12px 14px">
                    <div style="font-size:10px!important;color:{bloco['cor']};font-weight:600;
                                letter-spacing:.05em;text-transform:uppercase">{bloco['bloco']}</div>
                    <div style="font-size:13px!important;font-weight:600;color:#212529;margin:4px 0">
                        {bloco['icon']} {bloco['area']}
                    </div>
                    <div style="font-size:11px!important;color:#868e96">{bloco['desc']}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">📆 Semana completa</div>', unsafe_allow_html=True)

    dias_ordem = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    cols_sem = st.columns(7)
    for col, dia in zip(cols_sem, dias_ordem):
        with col:
            is_hoje = dia == dia_hoje
            borda = "#1565c0" if is_hoje else "#e9ecef"
            st.markdown(f"""
            <div style="background:#fff;border:1px solid {borda};border-radius:10px;padding:10px;height:100%">
                <div style="font-family:'Space Grotesk',sans-serif;font-size:11px!important;font-weight:700;
                            color:{'#1565c0' if is_hoje else '#495057'};margin-bottom:10px;padding:4px 6px;
                            background:{'#e3f2fd' if is_hoje else '#f8f9fa'};border-radius:5px;text-align:center">
                    {dia}{' ← hoje' if is_hoje else ''}
                </div>""", unsafe_allow_html=True)
            for bloco in CALENDARIO.get(dia, []):
                st.markdown(f"""
                <div style="background:{bloco['cor']}10;border-left:3px solid {bloco['cor']};
                            border-radius:0 5px 5px 0;padding:6px 8px;margin-bottom:5px">
                    <div style="font-size:9px!important;color:{bloco['cor']};font-weight:600">{bloco['bloco']}</div>
                    <div style="font-size:11px!important;font-weight:600;color:#212529;margin:2px 0">
                        {bloco['icon']} {bloco['area']}
                    </div>
                    <div style="font-size:10px!important;color:#868e96">{bloco['desc']}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ── Abas simples ──────────────────────────────────────────────────────────
render_modulos(PYTHON_CONCEITOS,  "PyConc", tab_conc)
render_modulos(C_MODULOS,         "C",      tab_c)
render_modulos(SQL_MODULOS,       "SQL",    tab_sql)
render_modulos(POWERBI_MODULOS,   "PBI",    tab_pbi)
render_modulos(MATEMATICA_MODULOS,"Mat",    tab_mat)
render_modulos(INGLES_MODULOS,    "EN",     tab_en)
render_modulos(LEITURA_MODULOS,   "Leit",   tab_leit)

# ── PYTHON PROJETOS ───────────────────────────────────────────────────────
with tab_proj:
    niveis = {"Básico":"#1565c0","Intermediário":"#e65100","Avançado":"#4a148c"}
    for pn,pd in PYTHON_PROJETOS.items():
        done_p  = sum(1 for t in pd["topics"] if progress.get(make_key("ProjPython",pn,t), False))
        total_p = len(pd["topics"])
        pct_p   = round(done_p/total_p*100) if total_p else 0
        cor_n   = niveis.get(pd["nivel"],"#868e96")
        with st.expander(f"{pd['icon']} {pn}  —  {done_p}/{total_p}  ({pct_p}%)"):
            st.markdown(f'<span style="background:{cor_n}15;color:{cor_n};border:1px solid {cor_n}40;border-radius:4px;padding:2px 8px;font-size:10px!important;font-weight:600">{pd["nivel"]}</span><div style="font-size:11px!important;color:#868e96;margin:6px 0 10px">{pd["desc"]}</div>', unsafe_allow_html=True)
            st.progress(pct_p/100)
            st.markdown('<div class="sec-label">Tópicos para aprender</div>', unsafe_allow_html=True)
            for topic in pd["topics"]:
                key = make_key("ProjPython",pn,topic)
                cur = progress.get(key, False)
                chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                if chk != cur:
                    progress[key] = chk
                    save_topic(key,"ProjPython",pn,topic,chk)
                    st.rerun()

# ── CARREIRA ──────────────────────────────────────────────────────────────
with tab_car:
    pct_alta  = round(done_alta/total_alta*100)   if total_alta  else 0
    pct_media = round(done_media/total_media*100) if total_media else 0
    pct_longo = round(done_longo/total_longo*100) if total_longo else 0

    ca,cm,cl = st.columns(3)
    for col,emoji,label,done,total,pct,cor,hint in [
        (ca,"🔴","Alta Prioridade", done_alta, total_alta, pct_alta,  "#c62828","Impacto direto em vaga — faça primeiro"),
        (cm,"🟡","Média Prioridade",done_media,total_media,pct_media, "#e65100","Diferencial de portfólio"),
        (cl,"🟢","Longo Prazo",     done_longo,total_longo,pct_longo, "#2e7d32","Quando tiver as bases sólidas"),
    ]:
        with col:
            st.markdown(f'<div class="kpi" style="text-align:left;border-left:4px solid {cor}"><div style="font-size:11px!important;color:{cor};font-weight:600;margin-bottom:4px">{emoji} {label}</div><div class="kpi-num" style="color:{cor}">{pct}%</div><div class="kpi-lbl">{done}/{total} tópicos</div><div style="font-size:10px!important;color:#adb5bd;margin-top:6px">{hint}</div></div>', unsafe_allow_html=True)
            st.progress(pct/100)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    for titulo, modulos, prefix, cor_sec in [
        ("🔴 Alta Prioridade — impacto direto em vaga", CARREIRA_ALTA,  "Alta",  "#c62828"),
        ("🟡 Média Prioridade — diferencial de portfólio", CARREIRA_MEDIA, "Media", "#e65100"),
        ("🟢 Longo Prazo — quando tiver as bases sólidas", CARREIRA_LONGO, "Longo", "#2e7d32"),
    ]:
        st.markdown(f'<div class="sec-label" style="border-left-color:{cor_sec};color:{cor_sec}">{titulo}</div>', unsafe_allow_html=True)
        for mn,md in modulos.items():
            done_m  = sum(1 for t in md["topics"] if progress.get(make_key(prefix,mn,t), False))
            total_m = len(md["topics"])
            pct_m   = round(done_m/total_m*100) if total_m else 0
            with st.expander(f"{md['icon']} {mn}  —  {done_m}/{total_m}  ({pct_m}%)"):
                st.progress(pct_m/100)
                if prefix == "Longo":
                    st.markdown('<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:8px 12px;margin-bottom:10px"><div style="font-size:11px!important;color:#15803d">⏳ Comece depois de dominar Alta e Média Prioridade</div></div>', unsafe_allow_html=True)
                for topic in md["topics"]:
                    key = make_key(prefix,mn,topic)
                    cur = progress.get(key, False)
                    chk = st.checkbox(topic, value=cur, key=f"cb_{key}")
                    if chk != cur:
                        progress[key] = chk
                        save_topic(key, prefix, mn, topic, chk)
                        st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


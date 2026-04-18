# 🧠 Tracker de Estudos — Isaque Sena

Aplicação Streamlit para acompanhar o progresso de estudos em Python, C, SQL, Power BI e ENEM 2026.

## Como rodar localmente

```bash
pip install streamlit
streamlit run app.py
```

## Como hospedar no Streamlit Cloud

1. Suba este repositório no GitHub
2. Acesse share.streamlit.io
3. Clique em "New app"
4. Selecione seu repositório e o arquivo `app.py`
5. Clique em "Deploy"

## Funcionalidades

- Marcar tópicos como concluídos
- Progresso salvo automaticamente em SQLite (`progresso.db`)
- Barra de progresso por área e geral
- Exportar progresso em CSV
- Resetar progresso

## Estrutura

- `app.py` — aplicação principal
- `requirements.txt` — dependências
- `progresso.db` — banco SQLite (criado automaticamente)

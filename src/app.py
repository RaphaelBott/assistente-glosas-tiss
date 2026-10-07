"""
Tissê — Assistente de Glosas TISS
Aplicação Streamlit que consulta a base de conhecimento local.

Rode com: streamlit run src/app.py
"""

import os
import re
import unicodedata
import pandas as pd
import streamlit as st

from prompts import (
    PROMPT_SISTEMA,
    PROMPT_FALLBACK,
    MENSAGEM_BOAS_VINDAS,
)

from ia import ia_disponivel, gerar_resposta_ia

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Tissê — Assistente de Glosas TISS",
    page_icon="🏥",
    layout="centered",
)

# ============================================================
# CARREGAMENTO DA BASE DE CONHECIMENTO
# ============================================================
PASTA_DATA = os.path.join(os.path.dirname(__file__), "..", "data")
PASTA_DATA = os.path.abspath(PASTA_DATA)

PASTA_DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
PASTA_DOCS = os.path.abspath(PASTA_DOCS)


@st.cache_data
def carregar_base():
    glosas = pd.read_csv(os.path.join(PASTA_DATA, "glosas.csv"))
    status = pd.read_csv(os.path.join(PASTA_DATA, "status_solicitacao.csv"))
    tabelas = pd.read_csv(os.path.join(PASTA_DATA, "tabelas_tiss.csv"))
    return glosas, status, tabelas


@st.cache_data
def carregar_processo_recurso():
    caminho = os.path.join(PASTA_DOCS, "processo_recurso.md")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return ""


glosas, status_solicitacao, tabelas_tiss = carregar_base()
processo_recurso = carregar_processo_recurso()


# ============================================================
# FUNÇÕES DE BUSCA
# ============================================================
def normalizar(texto):
    """Remove acentos, coloca em minúsculas e remove pontuação."""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def buscar_glosa_por_codigo(codigo):
    codigo = str(codigo).strip()
    resultado = glosas[glosas["codigo"].astype(str) == codigo]
    if not resultado.empty:
        return resultado.iloc[0]
    return None


def buscar_glosa_por_texto(pergunta, top_n=3):
    pergunta_norm = normalizar(pergunta)
    palavras = [p for p in pergunta_norm.split() if len(p) > 3]
    if not palavras:
        return []
    resultados = []
    for _, row in glosas.iterrows():
        texto = normalizar(f"{row['descricao']} {row['categoria']} {row['observacao']}")
        score = sum(1 for p in palavras if p in texto)
        if score > 0:
            resultados.append((score, row))
    resultados.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in resultados[:top_n]]


def buscar_status_por_codigo(codigo):
    codigo = str(codigo).strip()
    resultado = status_solicitacao[status_solicitacao["codigo"].astype(str) == codigo]
    if not resultado.empty:
        return resultado.iloc[0]
    return None


def buscar_tabela_por_codigo(codigo):
    codigo = str(codigo).strip()
    resultado = tabelas_tiss[tabelas_tiss["codigo"].astype(str) == codigo]
    if not resultado.empty:
        return resultado.iloc[0]
    return None


# ============================================================
# EXTRAÇÃO DE CÓDIGOS
# ============================================================
def extrair_codigo(pergunta, tamanhos=(4,)):
    for tam in tamanhos:
        match = re.search(rf"\b(\d{{{tam}}})\b", pergunta)
        if match:
            return match.group(1)
    return None


def extrair_codigo_tabela(pergunta):
    match = re.search(r"tabela\s+(\d{2,4})", pergunta, re.IGNORECASE)
    return match.group(1) if match else None


# ============================================================
# MONTAGEM DE CONTEXTO PARA A IA
# ============================================================
def montar_contexto(pergunta):
    """Monta o contexto a partir da base local para enviar à IA."""
    pergunta_norm = normalizar(pergunta)
    partes = []

    # 1. Processo de recurso
    palavras_processo = ["recurso", "recorrer", "prazo", "processo", "reanalise", "fluxo"]
    if any(p in pergunta_norm for p in palavras_processo):
        partes.append("### Processo de Recurso de Glosa\n" + processo_recurso[:3000])

    # 2. Tabelas TISS
    if "tabela" in pergunta_norm:
        codigo_tab = extrair_codigo_tabela(pergunta) or extrair_codigo(pergunta)
        if codigo_tab:
            tab = buscar_tabela_por_codigo(codigo_tab)
            if tab is not None:
                partes.append(
                    f"### Tabela {tab['codigo']} — {tab['descricao']}\n{tab['detalhe']}"
                )
        else:
            for _, row in tabelas_tiss.iterrows():
                partes.append(f"- Tabela {row['codigo']}: {row['descricao']} — {row['detalhe']}")

    # 3. Código de glosa ou status
    codigo = extrair_codigo(pergunta)
    if codigo:
        glosa = buscar_glosa_por_codigo(codigo)
        if glosa is not None:
            partes.append(
                f"### Glosa {glosa['codigo']}\n"
                f"Descrição: {glosa['descricao']}\n"
                f"Categoria: {glosa['categoria']}\n"
                f"Observação: {glosa['observacao']}"
            )
        else:
            status = buscar_status_por_codigo(codigo)
            if status is not None:
                partes.append(
                    f"### Status {status['codigo']} — {status['descricao']}\n{status['detalhe']}"
                )

    # 4. Busca por texto livre em glosas
    resultados = buscar_glosa_por_texto(pergunta, top_n=5)
    for r in resultados:
        partes.append(
            f"### Glosa {r['codigo']} — {r['descricao']}\n"
            f"Categoria: {r['categoria']}\n"
            f"Observação: {r['observacao']}"
        )

    return "\n\n".join(partes) if partes else ""


# ============================================================
# RESPOSTA LOCAL (SEM IA)
# ============================================================
def buscar_no_processo(pergunta):
    pergunta_norm = normalizar(pergunta)
    palavras_processo = [
        "recurso", "recorrer", "prazo", "processo", "reanalise",
        "fluxo", "como funciona", "como recorrer"
    ]
    if any(p in pergunta_norm for p in palavras_processo):
        return (
            "**Processo de Recurso de Glosa — Padrão TISS**\n\n"
            "**1. O que é:** Instrumento formal pelo qual o prestador contesta "
            "uma glosa aplicada pela operadora, solicitando reanálise da cobrança.\n\n"
            "**2. Fluxo do processo:**\n"
            "- Prestador envia mensagem `RecursoGlosa` com justificativa (até 500 caracteres)\n"
            "- Operadora responde com `RecebimentoRecursoGlosa` (número de protocolo)\n"
            "- Operadora analisa e responde com `RespostaRecursoGlosa`\n"
            "- Resposta pode ser: acatar, não acatar, acatar parcialmente ou solicitar mais informações\n\n"
            "**3. Prazos:**\n"
            "- Prazo para solicitar reanálise: **180 dias** a partir do recebimento do demonstrativo (glosa 2907)\n"
            "- Prazos podem variar conforme contrato — sempre verifique\n\n"
            "**4. Boas práticas:**\n"
            "- Identifique o código da glosa e leia a descrição oficial\n"
            "- Reúna evidências (prescrição, laudo, nota fiscal, prontuário)\n"
            "- Seja específico na justificativa\n"
            "- Respeite o prazo\n\n"
            "**Para detalhes completos, consulte a documentação em `docs/processo_recurso.md`.**"
        )
    return None


def buscar_tabela_por_texto(pergunta):
    pergunta_norm = normalizar(pergunta)
    if "tabela" not in pergunta_norm:
        return None

    codigo = extrair_codigo_tabela(pergunta)
    if not codigo:
        codigo = extrair_codigo(pergunta)

    if codigo:
        tab = buscar_tabela_por_codigo(codigo)
        if tab is not None:
            return (
                f"**Tabela {tab['codigo']} — {tab['descricao']}**\n\n"
                f"{tab['detalhe']}"
            )

    linhas = ["**Tabelas de domínio do TISS (Tabela 87):**\n"]
    for _, row in tabelas_tiss.iterrows():
        linhas.append(f"- **{row['codigo']}** — {row['descricao']}")
    linhas.append(
        "\nDigite o código de uma tabela para mais detalhes (ex: 'o que é a tabela 22?')"
    )
    return "\n".join(linhas)


def gerar_resposta_local(pergunta):
    """Gera resposta consultando a base local (sem IA)."""
    resp_processo = buscar_no_processo(pergunta)
    if resp_processo:
        return resp_processo

    resp_tabela = buscar_tabela_por_texto(pergunta)
    if resp_tabela:
        return resp_tabela

    codigo = extrair_codigo(pergunta)
    if codigo:
        glosa = buscar_glosa_por_codigo(codigo)
        if glosa is not None:
            return (
                f"**Glosa {glosa['codigo']} — {glosa['descricao']}**\n\n"
                f"**Categoria:** {glosa['categoria']}\n\n"
                f"**O que verificar:** {glosa['observacao']}\n\n"
                f"**Próxima ação:** Revise as evidências relacionadas a essa categoria "
                f"e, se aplicável, prepare o recurso de glosa conforme o Padrão TISS."
            )

        st_status = buscar_status_por_codigo(codigo)
        if st_status is not None:
            return (
                f"**Status {st_status['codigo']} — {st_status['descricao']}**\n\n"
                f"{st_status['detalhe']}"
            )

        tab = buscar_tabela_por_codigo(codigo)
        if tab is not None:
            return (
                f"**Tabela {tab['codigo']} — {tab['descricao']}**\n\n"
                f"{tab['detalhe']}"
            )

    resultados = buscar_glosa_por_texto(pergunta)
    if resultados:
        linhas = [f"Encontrei **{len(resultados)}** resultado(s) na base:\n"]
        for r in resultados:
            linhas.append(
                f"**Glosa {r['codigo']} — {r['descricao']}**\n"
                f"- Categoria: {r['categoria']}\n"
                f"- O que verificar: {r['observacao']}\n"
            )
        linhas.append(
            "\nSe algum desses códigos for o que você procura, digite o número "
            "para eu detalhar melhor."
        )
        return "\n".join(linhas)

    return PROMPT_FALLBACK.format(pergunta=pergunta)


# ============================================================
# INTERFACE
# ============================================================
st.title("🏥 Tissê — Assistente de Glosas TISS")
st.caption("Consulta de códigos de glosa, status e processo de recurso — Padrão TISS/ANS")

with st.sidebar:
    st.header("ℹ️ Sobre o assistente")
    st.markdown(
        "O **Tissê** ajuda analistas de faturamento hospitalar a entender "
        "códigos de glosa e o processo de recurso, com base no Padrão TISS da ANS."
    )
    st.markdown("**Base de conhecimento:**")
    st.markdown(f"- 📋 {len(glosas)} códigos de glosa (Tabela 38)")
    st.markdown(f"- 📊 {len(status_solicitacao)} status de solicitação (Tabela 45)")
    st.markdown(f"- 📚 {len(tabelas_tiss)} tabelas de domínio (Tabela 87)")

    st.divider()

    if ia_disponivel():
        st.success("🤖 Modo IA ativado (Gemini)")
    else:
        st.warning("⚠️ Modo local (sem IA)")

    st.divider()

    st.markdown("**Exemplos de perguntas:**")
    st.markdown("- O que significa a glosa 1703?")
    st.markdown("- Como funciona o recurso de glosa?")
    st.markdown("- O que é a tabela 22?")
    st.markdown("- Glosa 1809")

    st.divider()

    if "historico" in st.session_state:
        if st.button("🗑️ Limpar conversa"):
            st.session_state.historico = []
            st.rerun()


# Estado da conversa
if "historico" not in st.session_state:
    st.session_state.historico = []

if not st.session_state.historico:
    with st.chat_message("assistant"):
        st.markdown(MENSAGEM_BOAS_VINDAS)

for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Digite sua pergunta sobre glosas TISS...")

if pergunta:
    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando base de conhecimento..."):
            contexto = montar_contexto(pergunta)

            if ia_disponivel() and contexto:
                resposta = gerar_resposta_ia(pergunta, contexto)
                if resposta is None:
                    resposta = gerar_resposta_local(pergunta)
                    resposta = (
                        "ℹ️ *A IA está sobrecarregada no momento. "
                        "Respondendo com base local:*\n\n" + resposta
                    )
            else:
                resposta = gerar_resposta_local(pergunta)

        st.markdown(resposta)

    st.session_state.historico.append({"role": "assistant", "content": resposta})
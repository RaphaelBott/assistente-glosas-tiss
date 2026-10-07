"""
Tissê — Assistente TISS
Aplicação Streamlit que consulta a base de conhecimento via SQLite.

Rode com: streamlit run src/app.py
"""

import os
import re
import sqlite3
import unicodedata
import streamlit as st
from huggingface_hub import hf_hub_download

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
    page_title="Tissê — Assistente TISS",
    page_icon="🏥",
    layout="centered",
)

# ============================================================
# CARREGAMENTO DA BASE (SQLite via Hugging Face)
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

PASTA_DATA = os.path.join(PROJECT_ROOT, "data")
PASTA_DOCS = os.path.join(PROJECT_ROOT, "docs")


@st.cache_resource
def baixar_banco():
    caminho_local = os.path.join(PASTA_DATA, "tiss.db")
    if os.path.exists(caminho_local):
        return caminho_local
    try:
        caminho = hf_hub_download(
            repo_id="RaphaBott/tiss-db",
            filename="tiss.db",
            repo_type="dataset",
            local_dir=PASTA_DATA,
        )
        return caminho
    except Exception as e:
        st.error(f"Erro ao baixar o banco: {e}")
        return None


def conectar_banco():
    caminho = baixar_banco()
    if caminho is None:
        return None
    return sqlite3.connect(caminho, check_same_thread=False)


@st.cache_data
def carregar_processo_recurso():
    caminho = os.path.join(PASTA_DOCS, "processo_recurso.md")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return ""


conn = conectar_banco()
processo_recurso = carregar_processo_recurso()


# ============================================================
# UTILITÁRIOS
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


def dict_from_row(cursor, row):
    colunas = [d[0] for d in cursor.description]
    return dict(zip(colunas, row))


def contar_registros(tabela):
    if conn is None:
        return 0
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        return cur.fetchone()[0]
    except Exception:
        return 0


# ============================================================
# FUNÇÕES DE BUSCA
# ============================================================
def buscar_glosa_por_codigo(codigo):
    if conn is None:
        return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM glosas WHERE codigo = ?", (str(codigo).strip(),))
    row = cur.fetchone()
    return dict_from_row(cur, row) if row else None


def buscar_glosa_por_texto(pergunta, top_n=5):
    if conn is None:
        return []
    pergunta_norm = normalizar(pergunta)
    palavras = [p for p in pergunta_norm.split() if len(p) > 3]
    if not palavras:
        return []
    cur = conn.cursor()
    where = " OR ".join(["LOWER(descricao) LIKE ?"] * len(palavras))
    params = [f"%{p}%" for p in palavras]
    cur.execute(f"SELECT * FROM glosas WHERE {where} LIMIT ?", params + [top_n])
    return [dict_from_row(cur, row) for row in cur.fetchall()]


def buscar_status_por_codigo(codigo):
    if conn is None:
        return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM status_solicitacao WHERE codigo = ?", (str(codigo).strip(),))
    row = cur.fetchone()
    return dict_from_row(cur, row) if row else None


def buscar_tabela_por_codigo(codigo):
    if conn is None:
        return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM tabelas_tiss WHERE codigo = ?", (str(codigo).strip(),))
    row = cur.fetchone()
    return dict_from_row(cur, row) if row else None


def buscar_procedimento_por_codigo(codigo):
    if conn is None:
        return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM procedimentos WHERE codigo = ?", (str(codigo).strip(),))
    row = cur.fetchone()
    return dict_from_row(cur, row) if row else None


def buscar_por_texto(tabela, pergunta, top_n=10):
    """Busca genérica por texto usando a coluna normalizada (termo_norm)."""
    if conn is None:
        return []
    pergunta_norm = normalizar(pergunta)
    palavras = [p for p in pergunta_norm.split() if len(p) > 2]
    if not palavras:
        return []

    cur = conn.cursor()
    # Busca no termo E na apresentação (se existir)
    condicoes = []
    params = []
    for p in palavras:
        condicoes.append("termo_norm LIKE ?")
        params.append(f"%{p}%")

    where = " OR ".join(condicoes)

    try:
        cur.execute(
            f"SELECT * FROM {tabela} WHERE {where} LIMIT ?",
            params + [top_n],
        )
        return [dict_from_row(cur, row) for row in cur.fetchall()]
    except Exception:
        return []


def buscar_em_todas_tabelas(pergunta, top_n=5):
    """Busca em todas as tabelas TUSS de uma vez."""
    if conn is None:
        return []
    pergunta_norm = normalizar(pergunta)
    palavras = [p for p in pergunta_norm.split() if len(p) > 2]
    if not palavras:
        return []

    tabelas = [
        ("medicamentos", "Medicamento"),
        ("materiais_opme", "Material/OPME"),
        ("procedimentos", "Procedimento"),
        ("diarias_taxas", "Diária/Taxa"),
    ]

    resultados = []
    for tabela, rotulo in tabelas:
        cur = conn.cursor()
        where = " OR ".join(["termo_norm LIKE ?"] * len(palavras))
        params = [f"%{p}%" for p in palavras]
        try:
            # SELECT * pra pegar todas as colunas (incluindo extras_apresentacao)
            cur.execute(
                f"SELECT * FROM {tabela} WHERE {where} LIMIT ?",
                params + [top_n],
            )
            for row in cur.fetchall():
                r = dict_from_row(cur, row)
                r["tabela"] = rotulo
                resultados.append(r)
        except Exception:
            continue
    return resultados


def buscar_procedimento_por_texto(pergunta, top_n=10):
    return buscar_por_texto("procedimentos", pergunta, top_n)


def buscar_diaria_por_texto(pergunta, top_n=10):
    return buscar_por_texto("diarias_taxas", pergunta, top_n)


def buscar_medicamento_por_texto(pergunta, top_n=10):
    return buscar_por_texto("medicamentos", pergunta, top_n)


def buscar_material_por_texto(pergunta, top_n=10):
    return buscar_por_texto("materiais_opme", pergunta, top_n)


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


def extrair_codigo_procedimento(pergunta):
    match = re.search(r"\b(\d{8})\b", pergunta)
    return match.group(1) if match else None


def pergunta_eh_sobre_procedimento(pergunta):
    pergunta_norm = normalizar(pergunta)
    palavras = ["procedimento", "exame", "consulta", "cirurgia", "internacao", "terapia"]
    return any(p in pergunta_norm for p in palavras)


def pergunta_eh_sobre_medicamento(pergunta):
    pergunta_norm = normalizar(pergunta)
    return any(p in pergunta_norm for p in ["medicamento", "remedio", "droga", "farmaco"])


def pergunta_eh_sobre_material(pergunta):
    pergunta_norm = normalizar(pergunta)
    return any(p in pergunta_norm for p in ["material", "opme", "protese", "ortese", "stent"])


def pergunta_eh_sobre_diaria(pergunta):
    pergunta_norm = normalizar(pergunta)
    return any(p in pergunta_norm for p in ["diaria", "taxa", "gas", "acomodacao"])


# ============================================================
# MONTAGEM DE CONTEXTO PARA A IA
# ============================================================
def montar_contexto(pergunta):
    pergunta_norm = normalizar(pergunta)
    partes = []

    palavras_processo = ["recurso", "recorrer", "prazo", "processo", "reanalise", "fluxo"]
    if any(p in pergunta_norm for p in palavras_processo):
        partes.append("### Processo de Recurso de Glosa\n" + processo_recurso[:3000])

    if "tabela" in pergunta_norm:
        codigo_tab = extrair_codigo_tabela(pergunta) or extrair_codigo(pergunta)
        if codigo_tab:
            tab = buscar_tabela_por_codigo(codigo_tab)
            if tab:
                partes.append(f"### Tabela {tab['codigo']} — {tab['descricao']}\n{tab['detalhe']}")
        else:
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM tabelas_tiss")
                for row in cur.fetchall():
                    r = dict_from_row(cur, row)
                    partes.append(f"- Tabela {r['codigo']}: {r['descricao']} — {r['detalhe']}")

    codigo_proc = extrair_codigo_procedimento(pergunta)
    if codigo_proc:
        proc = buscar_procedimento_por_codigo(codigo_proc)
        if proc:
            partes.append(f"### Procedimento TUSS {proc['codigo']}\nTermo: {proc['termo']}")

    codigo = extrair_codigo(pergunta)
    if codigo and not codigo_proc:
        glosa = buscar_glosa_por_codigo(codigo)
        if glosa:
            partes.append(
                f"### Glosa {glosa['codigo']}\n"
                f"Descrição: {glosa['descricao']}\n"
                f"Categoria: {glosa['categoria']}\n"
                f"Observação: {glosa['observacao']}"
            )
        else:
            status = buscar_status_por_codigo(codigo)
            if status:
                partes.append(f"### Status {status['codigo']} — {status['descricao']}\n{status['detalhe']}")

    for r in buscar_glosa_por_texto(pergunta, top_n=5):
        partes.append(
            f"### Glosa {r['codigo']} — {r['descricao']}\n"
            f"Categoria: {r['categoria']}\n"
            f"Observação: {r['observacao']}"
        )

    if pergunta_eh_sobre_procedimento(pergunta):
        for r in buscar_procedimento_por_texto(pergunta, top_n=10):
            partes.append(f"### Procedimento TUSS {r['codigo']}\nTermo: {r['termo']}")

    if pergunta_eh_sobre_medicamento(pergunta):
        for r in buscar_medicamento_por_texto(pergunta, top_n=10):
            partes.append(f"### Medicamento TUSS {r['codigo']}\nTermo: {r['termo']}")

    if pergunta_eh_sobre_material(pergunta):
        for r in buscar_material_por_texto(pergunta, top_n=10):
            partes.append(f"### Material/OPME TUSS {r['codigo']}\nTermo: {r['termo']}")

    if pergunta_eh_sobre_diaria(pergunta):
        for r in buscar_diaria_por_texto(pergunta, top_n=10):
            partes.append(f"### Diária/Taxa TUSS {r['codigo']}\nTermo: {r['termo']}")

    return "\n\n".join(partes) if partes else ""


# ============================================================
# RESPOSTA LOCAL (SEM IA)
# ============================================================
def buscar_no_processo(pergunta):
    pergunta_norm = normalizar(pergunta)
    palavras = ["recurso", "recorrer", "prazo", "processo", "reanalise", "fluxo", "como funciona"]
    if any(p in pergunta_norm for p in palavras):
        return (
            "**Processo de Recurso de Glosa — Padrão TISS**\n\n"
            "**1. O que é:** Instrumento formal pelo qual o prestador contesta "
            "uma glosa aplicada pela operadora, solicitando reanálise da cobrança.\n\n"
            "**2. Fluxo do processo:**\n"
            "- Prestador envia mensagem `RecursoGlosa` com justificativa (até 500 caracteres)\n"
            "- Operadora responde com `RecebimentoRecursoGlosa` (número de protocolo)\n"
            "- Operadora analisa e responde com `RespostaRecursoGlosa`\n\n"
            "**3. Prazos:**\n"
            "- Prazo para solicitar reanálise: **180 dias** a partir do recebimento do demonstrativo (glosa 2907)\n\n"
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

    codigo = extrair_codigo_tabela(pergunta) or extrair_codigo(pergunta)
    if codigo:
        tab = buscar_tabela_por_codigo(codigo)
        if tab:
            return f"**Tabela {tab['codigo']} — {tab['descricao']}**\n\n{tab['detalhe']}"

    if conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tabelas_tiss")
        linhas = ["**Tabelas de domínio do TISS (Tabela 87):**\n"]
        for row in cur.fetchall():
            r = dict_from_row(cur, row)
            linhas.append(f"- **{r['codigo']}** — {r['descricao']}")
        linhas.append("\nDigite o código de uma tabela para mais detalhes.")
        return "\n".join(linhas)
    return None


def formatar_lista(res, rotulo, dica=""):
    """Formata uma lista de resultados para exibir no chat."""
    linhas = [f"Encontrei **{len(res)}** {rotulo}:\n"]
    for r in res:
        # Se tem apresentação, mostra entre parênteses
        apresentacao = r.get("extras_apresentacao")
        if apresentacao and isinstance(apresentacao, str) and apresentacao.strip():
            linhas.append(f"**{r['codigo']}** — {r['termo']} ({apresentacao})")
        else:
            linhas.append(f"**{r['codigo']}** — {r['termo']}")
    if dica:
        linhas.append(f"\n{dica}")
    else:
        linhas.append("\nDigite o código completo para mais detalhes.")
    return "\n".join(linhas)


def gerar_resposta_local(pergunta):
    pergunta_norm = normalizar(pergunta)

    # 1. Processo
    resp = buscar_no_processo(pergunta)
    if resp:
        return resp

    # 2. Tabelas
    resp = buscar_tabela_por_texto(pergunta)
    if resp:
        return resp

    # 3. Procedimento por código de 8 dígitos
    codigo_proc = extrair_codigo_procedimento(pergunta)
    if codigo_proc:
        proc = buscar_procedimento_por_codigo(codigo_proc)
        if proc:
            return f"**Procedimento TUSS {proc['codigo']}**\n\n{proc['termo']}"

    # 4. Glosa ou status por código de 4 dígitos
    codigo = extrair_codigo(pergunta)
    if codigo:
        glosa = buscar_glosa_por_codigo(codigo)
        if glosa:
            return (
                f"**Glosa {glosa['codigo']} — {glosa['descricao']}**\n\n"
                f"**Categoria:** {glosa['categoria']}\n\n"
                f"**O que verificar:** {glosa['observacao']}"
            )
        st_status = buscar_status_por_codigo(codigo)
        if st_status:
            return f"**Status {st_status['codigo']} — {st_status['descricao']}**\n\n{st_status['detalhe']}"

    # 5. Busca por procedimento
    if pergunta_eh_sobre_procedimento(pergunta):
        res = buscar_procedimento_por_texto(pergunta, top_n=10)
        if res:
            return formatar_lista(
                res, "procedimento(s) TUSS",
                "Se não encontrou, tente ser mais específico (ex: 'consulta em domicílio')."
            )

    # 6. Busca por medicamento
    if pergunta_eh_sobre_medicamento(pergunta):
        res = buscar_medicamento_por_texto(pergunta, top_n=10)
        if res:
            return formatar_lista(res, "medicamento(s) TUSS")

    # 7. Busca por material
    if pergunta_eh_sobre_material(pergunta):
        res = buscar_material_por_texto(pergunta, top_n=10)
        if res:
            return formatar_lista(res, "material(is) TUSS")

    # 8. Busca por diária/taxa
    if pergunta_eh_sobre_diaria(pergunta):
        res = buscar_diaria_por_texto(pergunta, top_n=10)
        if res:
            return formatar_lista(
                res, "diária(s)/taxa(s) TUSS",
                "Se não encontrou, tente ser mais específico (ex: 'taxa de ventilação')."
            )

    # 9. Busca por glosa (texto livre)
    res = buscar_glosa_por_texto(pergunta)
    if res:
        linhas = [f"Encontrei **{len(res)}** glosa(s):\n"]
        for r in res:
            linhas.append(f"**Glosa {r['codigo']} — {r['descricao']}**")
        return "\n".join(linhas)

       # 10. Busca universal
    resultados_universal = buscar_em_todas_tabelas(pergunta, top_n=5)
    if resultados_universal:
        linhas = [f"Encontrei **{len(resultados_universal)}** resultado(s):\n"]
        for r in resultados_universal:
            apresentacao = r.get("extras_apresentacao")
            if apresentacao and isinstance(apresentacao, str) and apresentacao.strip():
                linhas.append(f"**[{r['tabela']}]** {r['codigo']} — {r['termo']} ({apresentacao})")
            else:
                linhas.append(f"**[{r['tabela']}]** {r['codigo']} — {r['termo']}")
        linhas.append("\nDigite o código completo para mais detalhes.")
        return "\n".join(linhas)

    return PROMPT_FALLBACK.format(pergunta=pergunta)


# ============================================================
# INTERFACE
# ============================================================
st.title("🏥 Tissê — Assistente TISS")
st.caption("Consulta de glosas, procedimentos, medicamentos, materiais e diárias — Padrão TISS/ANS")

with st.sidebar:
    st.header("ℹ️ Sobre o assistente")
    st.markdown(
        "O **Tissê** ajuda analistas de faturamento hospitalar a entender "
        "códigos de glosa, procedimentos TUSS e o processo de recurso."
    )
    st.markdown("**Base de conhecimento:**")
    st.markdown(f"- 📋 {contar_registros('glosas')} códigos de glosa (Tabela 38)")
    st.markdown(f"- 📊 {contar_registros('status_solicitacao')} status (Tabela 45)")
    st.markdown(f"- 📚 {contar_registros('tabelas_tiss')} tabelas (Tabela 87)")
    st.markdown(f"- 🩺 {contar_registros('procedimentos')} procedimentos (Tabela 22)")
    st.markdown(f"- 💊 {contar_registros('medicamentos'):,} medicamentos (Tabela 20)")
    st.markdown(f"- 🔧 {contar_registros('materiais_opme'):,} materiais (Tabela 19)")
    st.markdown(f"- 💰 {contar_registros('diarias_taxas'):,} diárias/taxas (Tabela 18)")

    st.divider()

    if ia_disponivel():
        st.success("🤖 Modo IA ativado (Gemini)")
    else:
        st.warning("⚠️ Modo local (sem IA)")

    st.divider()

    st.markdown("**Exemplos de perguntas:**")
    st.markdown("- O que significa a glosa 1703?")
    st.markdown("- O que é o procedimento 10101012?")
    st.markdown("- Buscar rivaroxabana")
    st.markdown("- Taxa de ventilação")
    st.markdown("- Como funciona o recurso de glosa?")

    st.divider()

    if "historico" in st.session_state:
        if st.button("🗑️ Limpar conversa"):
            st.session_state.historico = []
            st.rerun()


if "historico" not in st.session_state:
    st.session_state.historico = []

if not st.session_state.historico:
    with st.chat_message("assistant"):
        st.markdown(MENSAGEM_BOAS_VINDAS)

for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Digite sua pergunta sobre TISS...")

if pergunta:
    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando base de conhecimento..."):

            pergunta_norm = normalizar(pergunta)

            # Busca local DIRETA para procedimentos, medicamentos, materiais e diárias
            usar_local_direto = False

            if pergunta_eh_sobre_procedimento(pergunta) and buscar_procedimento_por_texto(pergunta, top_n=1):
                usar_local_direto = True
            elif pergunta_eh_sobre_medicamento(pergunta) and buscar_medicamento_por_texto(pergunta, top_n=1):
                usar_local_direto = True
            elif pergunta_eh_sobre_material(pergunta) and buscar_material_por_texto(pergunta, top_n=1):
                usar_local_direto = True
            elif pergunta_eh_sobre_diaria(pergunta) and buscar_diaria_por_texto(pergunta, top_n=1):
                usar_local_direto = True

            if usar_local_direto:
                resposta = gerar_resposta_local(pergunta)
            else:
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
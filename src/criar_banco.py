"""
Cria o banco de dados SQLite (tiss.db) a partir dos CSVs da pasta data/.

Rode com: python src/criar_banco.py
"""

import os
import sqlite3
import pandas as pd


# ============================================================
# CAMINHOS
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
PASTA_DATA = os.path.join(PROJECT_ROOT, "data")
CAMINHO_DB = os.path.join(PASTA_DATA, "tiss.db")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def ler_csv(nome_arquivo, **kwargs):
    """Lê um CSV tratando separador e encoding com tolerância a erros."""
    caminho = os.path.join(PASTA_DATA, nome_arquivo)
    kwargs.setdefault("on_bad_lines", "skip")
    kwargs.setdefault("engine", "python")
    return pd.read_csv(caminho, **kwargs)


def ler_csv_padrao(caminho_ou_nome):
    """Lê CSV com separador ';' usando o módulo csv nativo (mais tolerante)."""
    import csv

    if os.path.isabs(caminho_ou_nome):
        caminho = caminho_ou_nome
    else:
        caminho = os.path.join(PASTA_DATA, caminho_ou_nome)

    try:
        with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            linhas = []
            for linha in leitor:
                if linha:
                    linhas.append(linha)
            return pd.DataFrame(linhas)
    except Exception as e:
        print(f"  ⚠️ Erro em {caminho_ou_nome}: {e}")
        return pd.DataFrame()


def gravar_df(conn, df, nome_tabela):
    """Grava um DataFrame numa tabela SQLite."""
    df.to_sql(nome_tabela, conn, if_exists="replace", index=False)
    print(f"  ✅ {nome_tabela}: {len(df)} registros")


def criar_indice(conn, tabela, coluna="codigo"):
    """Cria um índice pra acelerar buscas."""
    try:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{tabela}_{coluna} ON {tabela}({coluna})")
    except Exception as e:
        print(f"  ⚠️ Erro ao criar índice em {tabela}: {e}")


# ============================================================
# PROCESSAMENTO POR TABELA
# ============================================================
def processar_glosas(conn):
    df = ler_csv("glosas.csv")
    gravar_df(conn, df, "glosas")
    criar_indice(conn, "glosas")


def processar_status(conn):
    df = ler_csv("status_solicitacao.csv")
    gravar_df(conn, df, "status_solicitacao")
    criar_indice(conn, "status_solicitacao")


def processar_tabelas_tiss(conn):
    df = ler_csv("tabelas_tiss.csv")
    gravar_df(conn, df, "tabelas_tiss")
    criar_indice(conn, "tabelas_tiss")


def processar_procedimentos(conn):
    """Tabela 22 — procedimentos (separador ponto-e-vírgula)."""
    import csv
    import unicodedata

    caminho = os.path.join(PASTA_DATA, "procedimentos.csv")

    def normalizar(texto):
        if not isinstance(texto, str):
            texto = str(texto)
        texto = unicodedata.normalize("NFKD", texto)
        texto = texto.encode("ASCII", "ignore").decode("ASCII")
        return texto.lower()

    linhas = []
    with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        for i, linha in enumerate(leitor):
            if i == 0:
                continue
            if len(linha) >= 2:
                linhas.append({
                    "codigo": linha[0].strip(),
                    "termo": linha[1].strip(),
                })

    df = pd.DataFrame(linhas)
    df = df.dropna(subset=["codigo", "termo"])
    df = df[df["codigo"] != ""]
    df["codigo"] = df["codigo"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["termo_norm"] = df["termo"].apply(normalizar)

    gravar_df(conn, df, "procedimentos")
    criar_indice(conn, "procedimentos")
    criar_indice(conn, "procedimentos", "termo_norm")


def processar_tuss_generico(conn, padrao_nome, nome_tabela):
    """Processa arquivos tuss-XX com formato padronizado."""
    import unicodedata

    arquivos = sorted([f for f in os.listdir(PASTA_DATA) if f.startswith(padrao_nome) and f.endswith(".csv")])

    if not arquivos:
        print(f"  ⚠️ Nenhum arquivo encontrado para {padrao_nome}")
        return

    def normalizar(texto):
        if not isinstance(texto, str):
            texto = str(texto)
        texto = unicodedata.normalize("NFKD", texto)
        texto = texto.encode("ASCII", "ignore").decode("ASCII")
        return texto.lower()

    dfs = []
    for arq in arquivos:
        try:
            df = ler_csv_padrao(arq)
            if not df.empty:
                dfs.append(df)
        except Exception as e:
            print(f"  ⚠️ Erro ao ler {arq}: {e}")

    if not dfs:
        return

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = df_final.rename(columns={
        "id": "codigo",
        "display_name": "termo",
    })

       # Guarda TODAS as colunas extras que existirem
    colunas_uteis = ["codigo", "termo", "extras_laboratorio", "extras_apresentacao",
                     "extras_modelo", "extras_fabricante", "extras_classe_risco",
                     "extras_registro_anvisa"]
    colunas_presentes = [c for c in colunas_uteis if c in df_final.columns]
    df_final = df_final[colunas_presentes]
    df_final = df_final.dropna(subset=["codigo"])

    # Cria coluna normalizada (sem acentos, minúscula) para busca
    df_final["termo_norm"] = df_final["termo"].apply(normalizar)
    # Normaliza TAMBÉM a apresentação (pra buscar por miligrama)
    if "extras_apresentacao" in df_final.columns:
        df_final["apresentacao_norm"] = df_final["extras_apresentacao"].apply(
            lambda x: normalizar(x) if isinstance(x, str) else ""
        )

    gravar_df(conn, df_final, nome_tabela)
    criar_indice(conn, nome_tabela)
    criar_indice(conn, nome_tabela, "termo_norm")


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("Criando banco de dados tiss.db")
    print("=" * 60)
    print()

    if os.path.exists(CAMINHO_DB):
        os.remove(CAMINHO_DB)
        print(f"Banco antigo removido.")
        print()

    conn = sqlite3.connect(CAMINHO_DB)

    try:
        print("📋 Processando glosas (Tabela 38)...")
        processar_glosas(conn)
        print()

        print("📊 Processando status de solicitação (Tabela 45)...")
        processar_status(conn)
        print()

        print("📚 Processando tabelas de domínio (Tabela 87)...")
        processar_tabelas_tiss(conn)
        print()

        print("🩺 Processando procedimentos TUSS (Tabela 22)...")
        processar_procedimentos(conn)
        print()

        print("💰 Processando diárias, taxas e gases (Tabela 18)...")
        processar_tuss_generico(conn, "tuss-18", "diarias_taxas")
        print()

        print("🔧 Processando materiais e OPME (Tabela 19)...")
        processar_tuss_generico(conn, "tuss-19", "materiais_opme")
        print()

        print("💊 Processando medicamentos (Tabela 20)...")
        processar_tuss_generico(conn, "tuss-20", "medicamentos")
        print()

        conn.commit()

        # Resumo final
        print("=" * 60)
        print("RESUMO DO BANCO")
        print("=" * 60)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = [row[0] for row in cursor.fetchall()]

        for tabela in tabelas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"  {tabela}: {count:,} registros")

        # Tamanho do arquivo
        tamanho_mb = os.path.getsize(CAMINHO_DB) / 1024 / 1024
        print()
        print(f"📦 Tamanho do arquivo: {tamanho_mb:.2f} MB")
        print(f"📁 Local: {CAMINHO_DB}")

    finally:
        conn.close()

    print()
    print("✅ Banco criado com sucesso!")


if __name__ == "__main__":
    main()
"""
Módulo de integração com IA (Google Gemini).
Com timeout curto e fallback pra modo local.
"""

import os
from google import genai
from dotenv import load_dotenv

from prompts import PROMPT_SISTEMA

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODELO = "gemini-flash-lite-latest"

_client = None

if API_KEY:
    _client = genai.Client(api_key=API_KEY)


def ia_disponivel():
    """Verifica se a IA está configurada e pronta pra uso."""
    return _client is not None


def gerar_resposta_ia(pergunta, contexto):
    """
    Gera resposta usando o Gemini.
    Retorna None se falhar (para o app cair no fallback local).
    """
    if not ia_disponivel():
        return None

    try:
        prompt_completo = (
            f"{PROMPT_SISTEMA}\n\n"
            f"--- CONTEXTO ---\n"
            f"{contexto}\n\n"
            f"--- PERGUNTA ---\n"
            f"{pergunta}"
        )

        # Chama a IA com timeout de 15 segundos
        response = _client.models.generate_content(
            model=MODELO,
            contents=prompt_completo,
            config={
                "http_options": {
                    "timeout": 15000,  # 15 segundos em milissegundos
                }
            },
        )

        if response and response.text:
            return response.text
        return None

    except Exception as e:
        # Qualquer erro (timeout, 503, 404) → retorna None → fallback local
        print(f"[IA] Erro: {type(e).__name__}: {str(e)[:200]}")
        return None
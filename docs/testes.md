# Testes do Assistente

Registro dos testes realizados no Tissê, com data e resultado.

---

## Teste 1 — Consulta por código de glosa

**Data:** 2026-10-07
**Pergunta:** `o que significa a glosa 1703?`
**Resultado esperado:** Descrição da glosa + categoria + observação + próxima ação
**Resultado obtido:** ✅ Resposta correta via base local

---

## Teste 2 — Consulta por código curto

**Data:** 2026-10-07
**Pergunta:** `glosa 1809`
**Resultado esperado:** Descrição da glosa + categoria + observação + próxima ação
**Resultado obtido:** ✅ Resposta correta via base local

---

## Teste 3 — Processo de recurso

**Data:** 2026-10-07
**Pergunta:** `como funciona o recurso de glosa?`
**Resultado esperado:** Resumo do processo com fluxo, prazos e boas práticas
**Resultado obtido:** ✅ Resposta correta via base local

---

## Teste 4 — Consulta de tabela

**Data:** 2026-10-07
**Pergunta:** `o que é a tabela 22?`
**Resultado esperado:** Definição da Tabela 22 (Procedimentos e eventos em saúde)
**Resultado obtido:** ✅ Resposta correta via base local

---

## Teste 5 — Pergunta fora do escopo

**Data:** 2026-10-07
**Pergunta:** `qual a capital da França?`
**Resultado esperado:** Fallback — admite que não sabe e redireciona
**Resultado obtido:** ✅ Fallback correto

---

## Teste 6 — Comportamento com IA indisponível

**Data:** 2026-10-07
**Contexto:** A API do Google Gemini apresentou erro 503 (high demand)
**Comportamento esperado:** O app não deve travar; deve cair pro modo local
**Resultado obtido:** ✅ Fallback automático funcionou

---

## Observações

- O fallback automático para o modo local é uma prática profissional que garante disponibilidade contínua do assistente.
- Quando a API do Gemini estiver disponível, o assistente usa a IA para gerar respostas mais naturais.
- O timeout configurado é de 15 segundos — se a IA não responder nesse tempo, o fallback entra em ação.
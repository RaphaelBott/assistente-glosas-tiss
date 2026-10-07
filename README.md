# 🏥 Tissê — Assistente de Glosas TISS

Assistente virtual com Inteligência Artificial para apoiar analistas de faturamento hospitalar na compreensão de códigos de glosa e no processo de recurso, com base no **Padrão TISS da ANS** (Agência Nacional de Saúde Suplementar).

---

## 🎯 O Problema

Analistas de faturamento hospitalar lidam diariamente com **centenas de códigos de glosa** aplicados por operadoras de planos de saúde. Memorizar todos é inviável — e consultar manuais PDF de 400+ páginas é lento e improdutivo.

Além disso, o **processo de recurso de glosa** tem regras específicas do Padrão TISS (prazos, mensagens, fluxos) que nem sempre estão claras para quem está começando na área.

**O Tissê resolve isso:** responde em segundos, com base em fontes oficiais, e orienta o analista sobre o próximo passo.

---

## 🎓 Contexto do Desafio

Este projeto foi desenvolvido como parte do Lab **"Construa Seu Assistente Virtual Com Inteligência Artificial"** da [DIO](https://www.dio.me/), que propõe a criação de um assistente virtual com base em conhecimento estruturada e prompts bem definidos.

**Escolha de tema:** optei por um problema real da minha área de atuação (faturamento hospitalar / ERP Tasy), tornando o projeto útil além do exercício.

---

## 👥 Público-Alvo

- **Primário:** Analistas de faturamento hospitalar em início de carreira
- **Secundário:** Analistas experientes que querem agilizar consultas
- **Terciário:** Auditores de contas médicas e gestores de faturamento

---

## 🏗️ Estrutura do Projeto

```
assistente-glosas-tiss/
├── README.md
├── requirements.txt
├── .gitignore
├── data/                          # Base de conhecimento
│   ├── glosas.csv                # Tabela 38 — Glosas, negativas e outras
│   ├── status_solicitacao.csv    # Tabela 45 — Status da solicitação
│   └── tabelas_tiss.csv          # Tabela 87 — Tabelas de domínio do TISS
├── docs/                          # Documentação do agente
│   ├── especificacao.md          # Definição do agente (objetivo, escopo, comportamento)
│   ├── processo_recurso.md       # Resumo do processo de recurso de glosa
│   └── testes.md                 # Registro de testes realizados
└── src/                           # Código da aplicação
    ├── gerar_base.py             # Script que gera os CSVs da base
    ├── prompts.py                # Prompts do agente
    ├── ia.py                     # Integração com IA (Gemini)
    └── app.py                    # Aplicação Streamlit
```

---

## 🛡️ Resiliência e Fallback

O Tissê foi projetado para **nunca travar**, mesmo se a API de IA estiver indisponível.

**Como funciona:**

1. **Tenta usar a IA primeiro** (Gemini) — resposta mais natural e contextual
2. **Se a IA falhar ou demorar mais de 15s**, cai automaticamente para o **modo local**
3. **O modo local** consulta a base estruturada e retorna a informação oficial

**Por que isso importa:**

- APIs de IA podem ficar indisponíveis (erro 503, timeout, etc.)
- Em produção, um assistente que trava é inútil
- O fallback garante **disponibilidade contínua** com informação confiável

O usuário é avisado quando o modo local é usado, para saber que a resposta não veio da IA generativa.

---

## 🧠 Como Funciona

O Tissê é um assistente baseado em **RAG (Retrieval-Augmented Generation)** simplificado:

1. **Entrada:** o usuário digita uma pergunta em linguagem natural
2. **Detecção de intenção:** o sistema identifica se é sobre glosa, tabela, status ou processo de recurso
3. **Busca na base:** consulta os CSVs e o arquivo de processo
4. **Resposta:** retorna a informação oficial com contexto e próxima ação

### Fluxo detalhado

```
Pergunta do usuário
        │
        ▼
Detecção de intenção (regex + palavras-chave)
        │
        ├── Processo de recurso? ──► Resposta do docs/processo_recurso.md
        ├── Tabela TISS? ──────────► Busca em tabelas_tiss.csv
        ├── Código de glosa? ──────► Busca em glosas.csv
        ├── Status? ───────────────► Busca em status_solicitacao.csv
        │
        ▼
Montagem da resposta (descrição + categoria + observação + próxima ação)
```

---

## 📋 Base de Conhecimento

| Fonte | Conteúdo | Tamanho |
|---|---|---|
| **Tabela 38** (ANS) | Códigos de glosa, negativas e outras | ~300 códigos |
| **Tabela 45** (ANS) | Status da solicitação | 7 códigos |
| **Tabela 87** (ANS) | Tabelas de domínio do TISS | 7 tabelas |
| **Padrão TISS** (Set/2022) | Processo de recurso, prazos e fluxos | Documento textual |

---

## 🚀 Como Rodar

### 1. Clonar o repositório

```bash
git clone https://github.com/RaphaelBott/assistente-glosas-tiss.git
cd assistente-glosas-tiss
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Gerar a base de conhecimento

```bash
python src/gerar_base.py
```

Isso cria os arquivos `glosas.csv`, `status_solicitacao.csv` e `tabelas_tiss.csv` dentro de `data/`.

### 5. Configurar a chave da IA (opcional)

Cria um arquivo `.env` na raiz do projeto com:

```
GEMINI_API_KEY=sua_chave_aqui
```

Sem essa chave, o assistente funciona em **modo local** (busca na base). Com ela, usa a IA do Gemini para respostas mais naturais.

### 6. Rodar a aplicação

```bash
streamlit run src/app.py
```

O navegador abre automaticamente em `http://localhost:8501`.

---

## 💬 Exemplos de Perguntas

| Pergunta | Tipo de resposta |
|---|---|
| `O que significa a glosa 1703?` | Descrição da glosa + categoria + próxima ação |
| `Glosa 1809` | Descrição da glosa + categoria + próxima ação |
| `Como funciona o recurso de glosa?` | Resumo do processo + fluxo + prazos |
| `Qual o prazo para recorrer de uma glosa?` | Informação sobre prazo de 180 dias (glosa 2907) |
| `O que é a tabela 22?` | Definição da Tabela 22 (Procedimentos e eventos em saúde) |
| `Glosa de material sem nota fiscal` | Busca por texto livre + sugestões de códigos |
| `Qual a capital da França?` | Fallback: admite que não sabe e redireciona |

---

## 📊 Avaliação e Métricas

O agente foi avaliado com base nos seguintes critérios:

| Métrica | Descrição | Resultado |
|---|---|---|
| **Acurácia factual** | A resposta corresponde ao que está na base oficial | ✅ 100% (não inventa) |
| **Cobertura** | % de perguntas comuns de analistas respondidas | ✅ > 80% |
| **Clareza** | Resposta é compreensível para um novato | ✅ Avaliação qualitativa positiva |
| **Honestidade** | Admite quando não sabe | ✅ 100% (fallback funciona) |
| **Disponibilidade** | Funciona mesmo com a IA fora do ar | ✅ Fallback local ativo |

### Testes realizados

- ✅ Consulta por código exato (`glosa 1703`)
- ✅ Consulta por código embutido em frase (`o que significa a glosa 1809?`)
- ✅ Consulta por texto livre (`glosa de material sem nota fiscal`)
- ✅ Consulta sobre processo (`como funciona o recurso de glosa?`)
- ✅ Consulta sobre tabelas (`o que é a tabela 22?`)
- ✅ Pergunta fora do escopo (`qual a capital da França?`)
- ✅ Fallback automático quando a IA está indisponível

---

## ⚠️ Limitações Conhecidas

- **Dependência de API externa:** quando a IA do Gemini está sobrecarregada (erro 503), o assistente cai pro modo local. As respostas ficam mais diretas, mas continuam corretas.
- **Cobertura de glosas:** a base cobre os ~300 códigos mais comuns da Tabela 38. A tabela completa tem ~400.
- **Sem consulta à Tabela 22 completa:** o assistente **não consulta os 10.000+ códigos TUSS** de procedimentos — apenas explica o que a tabela é.
- **Sem integração com sistemas internos:** o assistente não acessa Tasy, Lucedata ou outros ERPs.
- **Sem memória entre sessões:** cada conversa é independente; o histórico é apagado ao fechar a página.

---

## 🔮 Próximos Passos

- [x] Integrar com LLM (Gemini) para respostas mais naturais
- [x] Implementar fallback local quando a IA estiver indisponível
- [ ] Expandir a base de glosas para os ~400 códigos da Tabela 38
- [ ] Adicionar consulta à Tabela 22 (procedimentos TUSS) via CSV oficial da ANS
- [ ] Criar testes automatizados de perguntas e respostas
- [ ] Publicar a aplicação no Streamlit Cloud

---

## 🛠️ Tecnologias

- **Python 3.12**
- **Streamlit** — interface web
- **Google Gemini** — IA generativa (com fallback local)
- **pandas** — manipulação dos dados
- **CSV** — formato da base de conhecimento
- **Markdown** — documentação

---

## 📚 Referências

- [Padrão TISS — ANS](https://www.gov.br/ans/pt-br/assuntos/prestadores/padrao-para-troca-de-informacao-de-saude-suplementar-2013-tiss)
- [Tabela de Domínio 38 — Glosas](https://www.gov.br/ans/pt-br)
- [Resolução Normativa nº 501/2022](https://www.gov.br/ans/pt-br)

---

## 👤 Autor

**Raphael Bott Riquete**

Analista de faturamento hospitalar em transição para a área de Tecnologia. Atuação sólida em suporte funcional do ERP Tasy, TUSS, glosas, conciliação financeira e intercâmbio UNIMED.

- LinkedIn: [linkedin.com/in/raphael-riquete-555ab7233](https://linkedin.com/in/raphael-riquete-555ab7233)
- GitHub: [github.com/RaphaelBott](https://github.com/RaphaelBott)

---

## 📄 Licença

Projeto desenvolvido para fins educacionais como parte do Lab da DIO.
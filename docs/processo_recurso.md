# Processo de Recurso de Glosa — Padrão TISS

Baseado no Componente Organizacional do Padrão TISS (ANS) — Setembro/2022.

---

## 1. O que é uma glosa?

**Glosa** é a recusa total ou parcial, por parte da operadora de plano de saúde, do pagamento de um procedimento, item ou serviço cobrado pelo prestador.

A glosa pode acontecer por diversos motivos, agrupados nas seguintes categorias (Tabela 38):

- **Beneficiário** (cadastro, elegibilidade)
- **Prestador** (credenciamento, habilitação)
- **Guia** (preenchimento, validade)
- **Autorização** (falta de senha, fora da cobertura)
- **Clínico** (CID, tipo de atendimento)
- **Financeiro** (valor, prazo, duplicidade)
- **Procedimento** (execução, compatibilidade)
- **Internação** (acomodação, diárias)
- **Material / Medicamento / OPME** (cobertura, quantidade)
- **Gases / Taxas** (uso, compatibilidade)
- **Série / Honorário / Exame / Pacote** (específicos por tipo)
- **Recurso** (problemas no próprio recurso)
- **Odontologia** (específicos)
- **Técnico** (comunicação TISS)

---

## 2. O que é recurso de glosa?

**Recurso de glosa** é o instrumento formal pelo qual o prestador contesta uma glosa aplicada pela operadora, solicitando reanálise da cobrança.

Está previsto no **Padrão TISS — Componente Organizacional, seção 58**, como um dos processos padronizados de troca de informações entre prestadores e operadoras.

---

## 3. Fluxo do processo de recurso

### 3.1 Envio pelo prestador

O prestador envia a mensagem **`RecursoGlosa`** à operadora, contendo:

- Identificação do beneficiário
- Identificação do prestador executante
- Procedimentos/itens assistenciais envolvidos
- Código(s) da(s) glosa(s) contestada(s)
- **Justificativa** (campo com até 500 caracteres)

### 3.2 Recebimento pela operadora

A operadora responde com a mensagem **`RecebimentoRecursoGlosa`**, contendo:

- Número de protocolo do recurso
- Confirmação de recebimento

### 3.3 Análise pela operadora

A operadora analisa o recurso e responde com a mensagem **`RespostaRecursoGlosa`**, que pode:

- **Acatar** o recurso (glosa revertida)
- **Não acatar** o recurso (glosa mantida)
- **Acatar parcialmente** (glosa revertida em parte)
- **Solicitar mais informações** (novo protocolo)

### 3.4 Consulta de status

A qualquer momento, o prestador pode enviar a mensagem **`SolicitacaoStatusRecursoGlosa`** para consultar a situação do recurso.

---

## 4. Prazos

### 4.1 Prazo para solicitar reanálise

Conforme o **código de glosa 2907**:

> **Prazo de 180 dias** para solicitação de reanálise, contados a partir da data de recebimento do demonstrativo de análise de conta.

### 4.2 Prazo prescricional

Conforme o **código de glosa 2909**:

> **Prazo para solicitação de recurso de glosa prescrito** — quando o prazo contratual ou regulatório é ultrapassado, o recurso não é aceito.

**Atenção:** Os prazos podem variar conforme o contrato entre prestador e operadora. Sempre verifique o contrato específico antes de recorrer.

---

## 5. Boas práticas ao recorrer de uma glosa

### 5.1 Antes de recorrer

1. **Identifique o código da glosa** e leia a descrição oficial
2. **Verifique a categoria** (beneficiário, guia, financeiro, etc.)
3. **Analise o contrato** com a operadora para verificar prazos e regras específicas
4. **Reúna as evidências** necessárias (prescrição, laudo, nota fiscal, prontuário, etc.)

### 5.2 Ao montar o recurso

1. **Seja específico:** cite o código da glosa e o motivo da contestação
2. **Anexe documentação:** quanto mais evidências, maior a chance de reversão
3. **Justificativa clara:** o campo aceita até 500 caracteres — use com objetividade
4. **Respeite o prazo:** recursos fora do prazo não são aceitos

### 5.3 Após enviar

1. **Acompanhe o protocolo** gerado pela operadora
2. **Verifique o status** periodicamente
3. **Se negado,** analise se cabe novo recurso ou se a glosa é definitiva

---

## 6. Mensagens do Padrão TISS relacionadas

| Mensagem | Origem | Descrição |
|---|---|---|
| `RecursoGlosa` | Prestador → Operadora | Envia recurso sobre glosa ocorrida em lote ou guias |
| `RecebimentoRecursoGlosa` | Operadora → Prestador | Envia protocolo de recebimento do recurso |
| `RespostaRecursoGlosa` | Operadora → Prestador | Resposta sobre o recurso (acata, não acata, etc.) |
| `SolicitacaoStatusRecursoGlosa` | Prestador → Operadora | Solicita informação sobre recurso enviado |
| `CancelamentoGuia` | Prestador → Operadora | Permite cancelar recurso de glosa enviado anteriormente |

---

## 7. Glosas mais comuns relacionadas ao próprio recurso

| Código | Descrição | O que verificar |
|---|---|---|
| 2901 | Revisão de glosa inválida | Conferir se o recurso foi enviado corretamente |
| 2902 | Glosa mantida | Glosa foi analisada e mantida pela operadora |
| 2903 | Pedido de revisão sem justificativa | Anexar justificativa técnica |
| 2904 | Mais de um recurso de glosa para a mesma guia/protocolo | Verificar duplicidade |
| 2905 | A guia não é de revisão | Verificar tipo de guia para recurso |
| 2906 | Número da guia inválido | Conferir número da guia |
| 2907 | Prazo de 180 dias ultrapassado para solicitação de reanálise | Verificar prazo regulatório |
| 2908 | Solicitação de reanálise efetuada de forma incorreta | Verificar formato da solicitação |
| 2909 | Prazo para solicitação de recurso de glosa prescrito | Verificar prazo de recurso |

---

## 8. Referências

- **Padrão TISS — Componente Organizacional** (ANS, Set/2022)
  - Seção 58: Processo de recurso de glosa
  - Seção 275+: Prazos
- **Tabela de Domínio 38** — Glosas, negativas e outras (ANS)
- **Resolução Normativa nº 501/2022** — Dispõe sobre o Padrão TISS

---

## 9. Limitações deste documento

Este resumo tem finalidade **educacional**. Para decisões operacionais:

- Consulte sempre o **Padrão TISS vigente** no site da ANS
- Verifique o **contrato específico** com cada operadora
- Confirme prazos com o **setor de faturamento** da sua instituição
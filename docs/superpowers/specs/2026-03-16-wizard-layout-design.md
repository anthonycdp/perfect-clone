# Wizard Layout Design - Component Extractor

**Data:** 2026-03-16
**Status:** Rascunho
**Contexto:** Alterar layout da aplicação para modo wizard full-screen cards

## Visão Geral

Substituir o layout de dois painéis (input à esquerda, resultado à direita) por um wizard estilo full-screen cards. Cada passo ocupa a tela inteira com foco em uma tarefa por vez, criando sensação de progresso guiado e melhor organização em telas menores.

### Motivação

- Criar sensação de progresso/guiado durante a configuração
- Organizar melhor a interface em telas menores (responsividade)
- Simplificar a experiência reduzindo carga cognitiva por tela

### Escopo

- Redesenhar fluxo de configuração em 4 passos wizard
- Manter todas as funcionalidades existentes
- Adicionar transições suaves entre estados

---

## Estrutura do Wizard

### Fluxo de Passos

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  1. URL  │ ─► │ 2. Modo  │ ─► │3.Estratég│ ─► │4. Query  │ ─► │ Progress │ ─► │ Resultado │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     ▲                                                                │
     └────────────────────────────────────────────────────────────────┘
```

**Total de passos:** 4 passos de configuração + 1 estado de progresso + 1 estado de resultado

---

## Detalhamento por Passo

### Passo 1: URL

**Objetivo:** Coletar a URL do site a ser extraído

**Elementos:**
- Indicador de passo: "1 de 4"
- Dots de progresso: ● ○ ○ ○
- Título: "Qual site você quer extrair?"
- Campo: Input de URL com placeholder "https://exemplo.com"
- Botão: "Continuar →"

**Validação:**
- URL obrigatória
- Formato válido (http/https)

---

### Passo 2: Modo de Extração

**Objetivo:** Definir o tipo de extração

**Elementos:**
- Indicador de passo: "2 de 4"
- Dots de progresso: ○ ● ○ ○
- Título: "O que você quer extrair?"
- Cards de seleção (radio cards):
  - **Componente único**: Um elemento específico da página
  - **Landing Page completa**: Toda a página inicial
- Botões: "← Voltar" | "Continuar →"

**Valor padrão:** Componente único

---

### Passo 3: Estratégia de Busca

**Objetivo:** Definir como localizar o componente

**Elementos:**
- Indicador de passo: "3 de 4"
- Dots de progresso: ○ ○ ● ○
- Título: "Como encontrar o componente?"
- Cards de seleção horizontal (4 opções):
  - **CSS** - Seletor CSS
  - **XPath** - Expressão XPath
  - **Texto** - Buscar por texto visível
  - **HTML** - Trecho de HTML
- Descrição da estratégia selecionada
- Botões: "← Voltar" | "Continuar →"

**Valor padrão:** Texto

**Nota:** Este passo pode ser simplificado ou ocultado no modo "Landing Page" (opcional - definir na implementação)

---

### Passo 4: Query + Executar

**Objetivo:** Definir a busca e iniciar extração

**Elementos:**
- Indicador de passo: "4 de 4"
- Dots de progresso: ○ ○ ○ ●
- Título: "O que você quer buscar?"
- Campo: Textarea com placeholder contextual baseado na estratégia
  - CSS: "Digite o seletor CSS (ex: .btn-primary)"
  - XPath: "Digite a expressão XPath"
  - Texto: "Digite o texto do botão, título ou elemento..."
  - HTML: "Cole o trecho HTML do elemento"
- Botões: "← Voltar" | "🚀 Extrair"

---

### Estado: Progresso (durante extração)

**Objetivo:** Mostrar progresso da extração

**Elementos:**
- Título: "Extraindo..."
- Progress bar: Barra visual com percentual
- Mensagem de status: Texto descritivo do passo atual
- Botão: "Cancelar"

**Transição:** O card atual transiciona suavemente para o estado de progresso

---

### Estado: Resultado

**Objetivo:** Exibir o resultado da extração

**Elementos:**
- Título: "✓ Extração concluída!"
- Abas de navegação: [Prompt] [JSON] [Assets]
- Conteúdo da aba ativa:
  - **Prompt**: Screenshot preview + texto do prompt + botão copiar
  - **JSON**: Árvore JSON formatada
  - **Assets**: Lista de assets extraídos
- Botão: "← Nova Extração"

---

## Navegação

### Regras

| Ação | Comportamento |
|------|---------------|
| Avançar | Valida passo atual, vai para próximo |
| Voltar | Sempre disponível, retorna ao passo anterior |
| Cancelar | Disponível apenas durante extração, interrompe processo |
| Nova Extração | Volta ao passo 1, mantém URL preenchida |

### Dots de Progresso

- Sempre visíveis na parte inferior do card
- Indicam progresso visual (preenchido = completo, vazio = pendente)
- Não são clicáveis (navegação apenas por botões)

---

## Layout e Responsividade

### Desktop (> 768px)

```
┌─────────────────────────────────────────────────────────────┐
│  Header fixo                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌───────────────────┐                   │
│                    │                   │                   │
│                    │   Card Content    │                   │
│                    │   (max 600px)     │                   │
│                    │                   │                   │
│                    └───────────────────┘                   │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Card centralizado com max-width de 600px
- Padding generoso ao redor
- Campos e botões com largura proporcional ao card

### Mobile (≤ 768px)

```
┌─────────────────────┐
│  Header fixo        │
├─────────────────────┤
│                     │
│                     │
│    Card Content     │
│    (100% width)     │
│                     │
│                     │
│                     │
└─────────────────────┘
```

- Card ocupa 100% da largura
- Campos e botões full-width
- Cards de seleção empilham verticalmente
- Fontes ajustadas para leitura mobile

---

## Transições

### Entre Passos

- Tipo: Slide horizontal (fade como fallback)
- Duração: 200-300ms
- Direção: Direita (avançar), Esquerda (voltar)

### Para Progresso

- Tipo: Fade + transform do conteúdo
- Duração: 300ms
- Botão "Extrair" transiciona para botão "Cancelar"

### Para Resultado

- Tipo: Fade in do novo conteúdo
- Duração: 300ms
- Progress bar desaparece, resultado aparece

---

## Componentes de UI

### Card de Seleção (Radio Card)

```css
/* Estado não selecionado */
border: 1px solid var(--border);
background: var(--bg-secondary);

/* Estado selecionado */
border: 2px solid var(--accent);
background: var(--bg-tertiary);
```

### Dots de Progresso

```css
/* Dot ativo */
width: 8px;
height: 8px;
border-radius: 50%;
background: var(--accent);

/* Dot inativo */
background: var(--border);
```

### Botões

- **Primário** (Continuar/Extrair): `background: var(--accent)`
- **Secundário** (Voltar): `background: transparent; border: 1px solid var(--border)`
- **Perigo** (Cancelar): `background: var(--error)` ou `color: var(--error)`

---

## Mudanças em Arquivos Existentes

### `server/static/index.html`

- Reestruturar layout de dois painéis para wizard single-card
- Adicionar container de navegação (dots)
- Adicionar estados: step-1, step-2, step-3, step-4, progress, result

### `server/static/styles.css`

- Adicionar estilos de wizard
- Adicionar transições CSS
- Ajustar media queries para responsividade

### `server/static/app.js`

- Adicionar estado de navegação (currentStep)
- Implementar funções: `goToStep()`, `nextStep()`, `prevStep()`
- Adaptar `startExtraction()` para transição de estados
- Adaptar `showResult()` para card de resultado

---

## Decisões de Design

| Aspecto | Decisão | Racional |
|---------|---------|----------|
| Número de passos | 4 | Equilíbrio entre granularidade e fricção |
| Navegação | Livre (sempre pode voltar) | Flexibilidade para corrigir erros |
| Progresso | No próprio card | Mantém contexto, transição suave |
| Resultado | Card no wizard | Sensação de jornada completa |
| Layout | Full-screen cards | Foco, sensação de progresso, mobile-friendly |
| Indicador | Dots simples | Minimalista, suficiente para 4 passos |

---

## Próximos Passos

Após aprovação deste documento, seguir para o plano de implementação usando a skill `writing-plans`.

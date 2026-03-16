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
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  1. URL  │ ─► │ 2. Modo  │ ─► │3.Estratég│ ─► │4. Query  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                               │
                                               ▼
                                          ┌──────────┐    ┌───────────┐
                                          │ Progress │ ─► │ Resultado │
                                          └──────────┘    └───────────┘
     ▲                                                                 │
     └─────────────────────────────────────────────────────────────────┘
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

**Comportamento no modo Landing Page:** Quando o usuário seleciona "Landing Page completa" no passo 2, este passo é pulado automaticamente (não se aplica - landing page não precisa de estratégia de busca). O fluxo vai direto do passo 2 para o passo 4, onde apenas confirma a extração.

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

### Comportamento do Cancelar

Quando o usuário clica em "Cancelar" durante a extração:

1. **Sem confirmação** - Cancelamento é imediato (extração pode ser reiniciada)
2. **Retorna ao passo 4** - Usuário pode ajustar a query e tentar novamente
3. **Estado preservado** - Todos os campos (URL, modo, estratégia, query) mantêm seus valores

### Comportamento do Nova Extração

Quando o usuário clica em "← Nova Extração" no resultado:

| Campo | Comportamento |
|-------|---------------|
| URL | Mantém preenchida |
| Modo | Mantém seleção |
| Estratégia | Mantém seleção |
| Query | Limpa (para nova busca) |
| Resultado | Descartado |

---

## Tratamento de Erros

### Erros de Validação (por passo)

Exibidos inline abaixo do campo com problema:

```
┌─────────────────────────────────────┐
│ https://url-invalida                │
└─────────────────────────────────────┘
⚠ Por favor, informe uma URL válida (http:// ou https://)
```

| Passo | Validação | Mensagem |
|-------|-----------|----------|
| 1 | URL vazia | "Por favor, informe uma URL" |
| 1 | URL inválida | "Por favor, informe uma URL válida (http:// ou https://)" |
| 4 | Query vazia | "Por favor, informe o que deseja buscar" |

### Erros Durante Extração

Quando a extração falha (erro de navegação, componente não encontrado, erro de API):

1. **Estado de progresso** transiciona para **estado de erro**
2. Mensagem de erro específica é exibida
3. Botões disponíveis: "← Voltar" (passo 4) ou "Tentar Novamente"

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                      ⚠ Erro                             │
│                                                         │
│         Não foi possível encontrar o componente        │
│         com o texto "Botão Submit"                      │
│                                                         │
│           [← Voltar]    [Tentar Novamente]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tipos de Erro

| Erro | Mensagem | Ação |
|------|----------|------|
| `NavigationError` | "Não foi possível acessar o site" | Voltar ao passo 1 |
| `TargetNotFoundError` | "Não foi possível encontrar o componente" | Voltar ao passo 4 |
| `APIError` | "Erro ao processar extração" | Tentar novamente |
| `CancellationError` | (silencioso) | Voltar ao passo 4 |

---

## Acessibilidade

### Navegação por Teclado

| Tecla | Ação |
|-------|------|
| `Tab` | Navega entre elementos focáveis |
| `Enter` | Avança para próximo passo (em botões e inputs) |
| `Escape` | Cancela extração (se em progresso) |
| `Arrow keys` | Navega entre radio cards (quando focado) |

### ARIA Labels

- **Dots de progresso**: `aria-label="Passo X de 4"` + `aria-current="step"` no dot ativo
- **Radio cards**: `role="radio"` + `aria-checked="true/false"`
- **Botões**: Labels descritivos (ex: "Continuar para próximo passo")
- **Progress bar**: `role="progressbar"` + `aria-valuenow`, `aria-valuemin`, `aria-valuemax`

### Reduced Motion

Respeitar preferência `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  .wizard-transition {
    transition: none;
  }
}
```

Quando reduzido, todas as transições são instantâneas (sem animação).

---

## Layout e Responsividade

### Desktop (> 1024px)

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

### Tablet (768px - 1024px)

- Card centralizado com max-width de 500px
- Cards de seleção (passo 2) em grid 2x2
- Layout híbrido entre desktop e mobile

### Mobile (< 768px)

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

- **Tipo:** Slide horizontal com fade
- **Duração:** 250ms
- **Timing function:** `ease-out`
- **Direção:** Direita (avançar), Esquerda (voltar)
- **Fallback:** Se `prefers-reduced-motion: reduce`, transição instantânea (0ms)

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

**Interação:**
- Clique em qualquer área do card seleciona a opção
- Hover: elevação sutil (`box-shadow`) ou mudança de borda
- Seleção: borda accent + background diferenciado

```css
/* Estado não selecionado */
border: 1px solid var(--border);
background: var(--bg-secondary);
cursor: pointer;

/* Estado hover */
border-color: var(--text-secondary);
box-shadow: 0 2px 8px rgba(0,0,0,0.1);

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

## Mudanças em Arquivos

> **Nota:** Os arquivos referenciados abaixo serão criados conforme o design de web-ui-migration (docs/superpowers/specs/2026-03-15-web-ui-migration-design.md). Este spec altera o layout desses arquivos de "dois painéis" para "wizard full-screen cards".

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

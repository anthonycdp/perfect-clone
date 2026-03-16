# Component Extractor

Ferramenta em Python para extrair um componente ou uma landing page completa a partir de uma URL, coletar contexto estrutural e visual com Playwright, normalizar esses dados e gerar um prompt estruturado via OpenAI para recriacao da interface.

O projeto roda com uma interface web em FastAPI e acompanha o progresso da extracao em tempo real via SSE.

## O que o projeto faz

- Extrai um componente unico ou uma pagina completa.
- Coleta DOM, estilos computados, interacoes, animacoes, assets, rich media e comportamento responsivo.
- Detecta bibliotecas externas carregadas na pagina.
- Normaliza a coleta em modelos Pydantic tipados.
- Envia o contexto para a OpenAI e gera uma saida estruturada para recriacao da UI.
- Empacota os artefatos da execucao em um `.zip` com `manifest.json`, `normalized.json`, screenshots e assets.

## Stack

- Python 3.10+
- Playwright
- FastAPI + Uvicorn
- Pydantic v2
- OpenAI Responses API
- Pillow
- OpenCV
- Pytest

## Requisitos

- Python `>= 3.10`
- Chromium instalado via Playwright
- Chave `OPENAI_API_KEY`

## Instalacao

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Se estiver em Linux ou macOS, ajuste apenas o comando de ativacao do ambiente virtual.

## Configuracao

Crie um arquivo `.env` na raiz do projeto com:

```env
OPENAI_API_KEY=sk-sua-chave
```

Existe um exemplo minimo em `.env.example`.

## Como executar

```bash
python main.py
```

O servidor sobe em `http://127.0.0.1:8000` e o navegador e aberto automaticamente.

## Como usar

Pela interface web:

1. Informe a URL.
2. Escolha o modo de extracao.
3. Se estiver em `component`, escolha a estrategia de busca.
4. Informe a busca e inicie a extracao.

Modos disponiveis:

- `component`: extrai um elemento especifico localizado por `css`, `xpath`, `text` ou `html_snippet`.
- `full_page`: extrai a pagina inteira, segmentando secoes e limitando a coleta por secao para manter o pacote gerado controlado.

## Pipeline

O fluxo principal do projeto e:

```text
URL -> Collector -> Normalizer -> Synthesizer -> SynthesisOutput
```

Etapas principais:

1. `collector/`: abre a pagina, encontra o alvo e coleta DOM, estilos, interacoes, animacoes, assets, rich media, bibliotecas e breakpoints.
2. `normalizer/`: transforma a coleta bruta em `NormalizedOutput` ou `FullPageNormalizedOutput`.
3. `synthesizer/`: envia o contexto para a OpenAI e gera `SynthesisOutput`.
4. `server/`: expoe a interface web, streaming de progresso, resultado final e download do pacote.

## API HTTP

Rotas principais do backend:

- `POST /api/extract`: inicia uma extracao.
- `GET /api/extract/{task_id}/progress`: stream SSE de progresso.
- `GET /api/extract/{task_id}/result`: retorna o resultado final em JSON.
- `GET /api/extract/{task_id}/package`: baixa o `.zip` da execucao.
- `GET /api/extract/{task_id}/artifacts/{artifact_path}`: serve artefatos temporarios da tarefa.
- `POST /api/extract/{task_id}/cancel`: cancela uma execucao em andamento.

Payload de inicio:

```json
{
  "url": "https://exemplo.com",
  "mode": "component",
  "strategy": "text",
  "query": "Get started"
}
```

Campos aceitos:

- `mode`: `component` ou `full_page`
- `strategy`: `css`, `xpath`, `text` ou `html_snippet`
- `query`: texto de busca; relevante principalmente para `component`

## Pacote gerado

Cada execucao concluida gera um pacote `.zip` com arquivos de apoio para uso posterior em outra IA ou pipeline.

Conteudo esperado:

- `README.md`: guia rapido do pacote
- `manifest.json`: inventario e resumo da coleta
- `normalized.json`: fonte estruturada de verdade da extracao
- `prompt.txt`: prompt final gerado para recriacao
- screenshots, assets, rich media e artefatos de animacao

Os artefatos temporarios ficam em um diretorio dentro da pasta temporaria do sistema, sob `component-extractor/`, e sao limpos automaticamente apos o TTL da tarefa.

## Estrutura do projeto

```text
.
|-- main.py
|-- orchestrator.py
|-- collector/
|-- models/
|-- normalizer/
|-- output/
|-- server/
|-- synthesizer/
`-- tests/
```

Resumo dos diretorios:

- `collector/`: modulos de coleta com Playwright.
- `models/`: enums e modelos Pydantic da extracao, normalizacao e sintese.
- `normalizer/`: transformacao da coleta bruta para estruturas normalizadas.
- `server/`: app FastAPI, tarefas, artefatos e frontend estatico.
- `synthesizer/`: cliente OpenAI e construcao do prompt.
- `tests/`: cobertura de coletores, modelos, servidor, normalizacao, sintetizador e orquestrador.

## Testes

Executar toda a suite:

```bash
pytest
```

Executar um arquivo especifico:

```bash
pytest tests/collector/test_dom_extractor.py
```

Executar um teste especifico:

```bash
pytest tests/collector/test_dom_extractor.py::TestDOMExtractor::test_extract_basic -v
```

## Observacoes

- A aplicacao depende de `OPENAI_API_KEY`; sem isso a extracao termina com erro antes da sintese.
- O sintetizador usa a OpenAI Responses API com saida estruturada.
- O modelo configurado atualmente em codigo e `gpt-5.4`.
- O frontend atual e implementado em HTML, CSS e JavaScript vanilla.

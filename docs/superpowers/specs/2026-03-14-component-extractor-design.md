# Component Extractor - Design Document

**Data:** 2026-03-14
**Status:** Rascunho
**Contexto:** Uso pessoal

## Visão Geral

Ferramenta desktop para extrair componentes/seções de websites e gerar prompts otimizados para recriação fiel. O pipeline possui três fases:

1. **Collector** - Coleta determinística via Playwright
2. **Normalizer** - Transformação em JSON estruturado
3. **Synthesizer** - Síntese do prompt via OpenAI GPT-5.4

---

## Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Interface | Tkinter (Python nativo) |
| Automação Browser | Playwright + Chromium |
| Validação de Dados | Pydantic v2 |
| IA | OpenAI Responses API + Structured Outputs |
| Modelo | GPT-5.4 |
| Processamento de Vídeo | OpenCV |
| Imagens | Pillow |

---

## Estrutura do Projeto

```
component-extractor/
├── main.py
├── requirements.txt
├── .env.example
│
├── gui/
│   ├── __init__.py
│   ├── app.py
│   ├── widgets/
│   │   ├── url_input.py
│   │   ├── selector_input.py
│   │   └── progress_display.py
│   └── panels/
│       ├── input_panel.py
│       └── result_panel.py
│
├── collector/
│   ├── __init__.py
│   ├── browser.py
│   ├── target_finder.py
│   ├── dom_extractor.py
│   ├── style_extractor.py
│   ├── interaction_mapper.py
│   ├── interaction_player.py
│   ├── asset_downloader.py
│   ├── animation_recorder.py
│   ├── library_detector.py
│   └── responsive_collector.py
│
├── normalizer/
│   ├── __init__.py
│   ├── context_builder.py
│   └── transformers/
│       ├── dom_transformer.py
│       ├── style_transformer.py
│       └── animation_transformer.py
│
├── synthesizer/
│   ├── __init__.py
│   ├── openai_client.py
│   └── prompts/
│       └── synthesis_prompt.py
│
├── models/
│   ├── __init__.py
│   ├── extraction.py
│   ├── normalized.py
│   └── synthesis.py
│
└── output/
    ├── assets/
    │   ├── images/
    │   ├── fonts/
    │   └── svgs/
    ├── animations/
    └── extractions/
```

---

## Módulos Detalhados

### 1. Collector (`collector/`)

Responsável pela extração de dados do browser.

#### `browser.py` - Classe `BrowserManager`
```python
class BrowserManager:
    def __init__(self, headless: bool = True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless

    def navigate(self, url: str, timeout: int = 30000) -> None:
        """Navega para URL e aguarda carregamento."""

    def resize_viewport(self, width: int, height: int) -> None:
        """Redimensiona viewport."""

    def close(self) -> None:
        """Fecha browser e libera recursos."""
```
- Inicializa Chromium com Playwright
- Gerencia navegação e ciclo de vida
- Controla redimensionamento de viewport

#### `target_finder.py`
Estratégias de identificação do componente:
- `find_by_css(selector)` - Seletor CSS
- `find_by_xpath(xpath)` - XPath
- `find_by_text(text)` - Busca por texto
- `find_by_html_snippet(html)` - Correspondência de HTML

#### `dom_extractor.py`
- HTML renderizado do componente
- Árvore DOM recursiva
- Bounding boxes
- Hierarquia de elementos

#### `style_extractor.py`
- Computed styles via `getComputedStyle()`
- Propriedades `animation-*` e `transition-*`
- Keyframes via CSSOM
- Transforms e opacity

#### `interaction_mapper.py`
Detecta automaticamente elementos interativos:
- Elementos com `cursor: pointer`
- Tags semânticas (`<button>`, `<a>`, `<input>`)
- Pseudo-classes `:hover`/`:focus`
- Event listeners

#### `interaction_player.py`
Executa interações e captura mudanças:
- Snapshot antes/depois
- `hover()`, `click()`, `focus()`, `scroll()`
- Aguarda `transitionend`
- Registra diferenças de estado

#### `animation_recorder.py`
Armazena gravações em `output/animations/`:
- `output/animations/{timestamp}/video.webm` - Gravação de tela
- `output/animations/{timestamp}/frames/` - Frames extraídos
- `output/animations/{timestamp}/key_frames/` - Frames importantes

Funcionalidades:
- Gravação de tela do componente
- Extração de frames com OpenCV
- Detecção de frames-chave (mudança visual significativa)
- Medição de timing real

#### `asset_downloader.py`
- Imagens (`<img>`, `background-image`)
- SVGs inline e externos
- Fontes (`@font-face`)
- Salva em `output/assets/{type}/`

#### `library_detector.py`
Detecta bibliotecas externas:
- GSAP, Lottie, Three.js, Swiper, etc.
- Scaneia `<script src>` e globais
- Extrai código de inicialização
- Captura snippets de uso

#### `responsive_collector.py`
Detecta e captura variantes responsivas:
```python
class ResponsiveCollector:
    def __init__(self, page: Page):
        self.page = page

    def detect_breakpoints(self) -> list[int]:
        """Extrai widths de media queries do CSS via CSSOM."""

    def collect_at_viewport(self, target: Locator, width: int, height: int) -> dict:
        """Captura estado do componente em viewport específica."""

    def collect_all(self, target: Locator) -> ResponsiveBehavior:
        """Detecta breakpoints e coleta estados em cada um."""
```
- Acessa `document.styleSheets` para encontrar media queries
- Extrai valores de `min-width` e `max-width`
- Redimensiona viewport para cada breakpoint detectado
- Captura diff de estilos entre breakpoints

---

### 2. Normalizer (`normalizer/`)

Transforma dados brutos em JSON estruturado.

#### `context_builder.py`
Orquestra a construção do `NormalizedOutput`.

#### Transformers:
- `dom_transformer.py` - Limpa e estrutura DOM
- `style_transformer.py` - Categoriza estilos (layout, spacing, typography, colors, effects)
- `animation_transformer.py` - Processa keyframes, timing, easing

---

### 3. Synthesizer (`synthesizer/`)

Gera o prompt final via OpenAI.

#### `openai_client.py`
```python
class OpenAISynthesizer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5.4"

    def synthesize(self, normalized_data: NormalizedOutput) -> SynthesisOutput:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(normalized_data)}
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "synthesis_output",
                    "schema": SynthesisOutput.model_json_schema()
                }
            }
        )
        return SynthesisOutput.model_validate_json(response.output_text)
```

#### System Prompt
```
Você é um especialista em engenharia de UI/UX. Sua tarefa é analisar dados
estruturados de um componente web e gerar um prompt detalhado que permita
recriar esse componente fielmente.

Você receberá:
- Estrutura DOM do componente
- Estilos computados organizados por categoria
- Dados de animações e transições (incluindo gravação)
- Interações observadas (hover, click, scroll)
- Comportamento responsivo
- Bibliotecas externas detectadas e como são usadas
- Assets (imagens, fontes, SVGs)

Seu output deve ser um JSON estruturado com:
1. Descrição técnica e visual do componente
2. Árvore de componentes sugerida
3. Comportamentos interativos
4. Regras responsivas
5. Dependências necessárias (com alternativas vanilla quando aplicável)
6. Prompt final otimizado para recriação fiel

O prompt final deve ser agnóstico de framework, focando em HTML/CSS/JS puro,
e conter detalhes suficientes para reproduzir comportamentos complexos.
```

---

### 4. GUI (`gui/`)

Interface Tkinter com layout de painéis.

#### `app.py`
Janela principal (900x700):
- Header com título
- Área principal dividida (input | resultado)
- Status bar

#### `panels/input_panel.py`
- Campo URL
- Radio buttons para estratégia (CSS/XPath/Texto/HTML)
- Área de texto para seletor/query
- Botão "Extrair Componente"
- Barra de progresso

#### `panels/result_panel.py`
Notebook com abas:
- **Prompt Final** - Texto + botão copiar
- **JSON Completo** - Dados normalizados
- **Assets** - Treeview com arquivos baixados
- **Animação** - Preview de frames com slider

#### `widgets/progress_display.py`
Etapas do pipeline:
1. Conectando ao browser
2. Localizando componente
3. Extraindo DOM
4. Extraindo estilos
5. Mapeando interações
6. Executando interações
7. Gravando animações
8. Baixando assets
9. Detectando bibliotecas
10. Normalizando dados
11. Gerando prompt com IA

---

### 5. Models (`models/`)

Schemas Pydantic para validação.

#### `extraction.py`
```python
class SelectorStrategy(str, Enum):
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    HTML_SNIPPET = "html_snippet"

class InteractionType(str, Enum):
    HOVER = "hover"
    CLICK = "click"
    FOCUS = "focus"
    SCROLL = "scroll"

class AssetType(str, Enum):
    IMAGE = "image"
    SVG = "svg"
    FONT = "font"
    VIDEO = "video"

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class AnimationData(BaseModel):
    name: Optional[str]
    duration: str
    delay: str
    timing_function: str
    iteration_count: str
    direction: str
    fill_mode: str
    keyframes: Optional[dict]

class TransitionData(BaseModel):
    property: str
    duration: str
    timing_function: str
    delay: str

class InteractionState(BaseModel):
    type: InteractionType
    selector: str
    before: dict
    after: dict
    duration_ms: float

class Asset(BaseModel):
    type: AssetType
    original_url: str
    local_path: str
    file_size_bytes: int
    dimensions: Optional[list[int]]  # [width, height]

class ExternalLibrary(BaseModel):
    name: str
    version: Optional[str]
    source_url: str
    usage_snippets: list[str]
    init_code: Optional[str]

class ResponsiveBreakpoint(BaseModel):
    width: int
    height: int
    source: str
    styles_diff: dict
    layout_changes: list[str]

class AnimationRecording(BaseModel):
    video_path: str
    duration_ms: float
    fps: int
    frames_dir: str
    key_frames: list[int]
```

#### `normalized.py`
```python
class PageInfo(BaseModel):
    url: str
    title: str
    viewport: dict
    loaded_scripts: list[str]
    loaded_stylesheets: list[str]

class TargetInfo(BaseModel):
    selector_used: str
    strategy: str
    html: str
    bounding_box: BoundingBox
    depth_in_dom: int

class DOMTree(BaseModel):
    tag: str
    attributes: dict
    children: list["DOMTree"]
    text_content: Optional[str]
    computed_styles: dict[str, str]

class StyleSummary(BaseModel):
    layout: dict
    spacing: dict
    typography: dict
    colors: dict
    effects: dict

class AnimationSummary(BaseModel):
    css_animations: list[AnimationData]
    css_transitions: list[TransitionData]
    scroll_effects: list[str]
    recording: AnimationRecording

class InteractionSummary(BaseModel):
    hoverable_elements: list[str]
    clickable_elements: list[str]
    focusable_elements: list[str]
    scroll_containers: list[str]
    observed_states: dict[str, InteractionState]

class ResponsiveBehavior(BaseModel):
    breakpoints: list[ResponsiveBreakpoint]
    is_fluid: bool
    has_mobile_menu: bool
    grid_changes: list[dict]

class NormalizedOutput(BaseModel):
    page: PageInfo
    target: TargetInfo
    dom: DOMTree
    styles: StyleSummary
    assets: list[Asset]
    interactions: InteractionSummary
    animations: AnimationSummary
    responsive_behavior: ResponsiveBehavior
    external_libraries: list[ExternalLibrary]

# Nota: scroll_effects está dentro de AnimationSummary
# Nota: observed_states está dentro de InteractionSummary
```

#### `synthesis.py`
```python
class ComponentDescription(BaseModel):
    technical: str
    visual: str
    purpose: str

class ComponentTree(BaseModel):
    name: str
    role: str
    children: list["ComponentTree"]

class InteractionBehavior(BaseModel):
    trigger: str
    effect: str
    animation: Optional[str]

class ResponsiveRule(BaseModel):
    breakpoint: str
    changes: list[str]

class Dependency(BaseModel):
    name: str
    reason: str
    alternative: Optional[str]

class SynthesisOutput(BaseModel):
    description: ComponentDescription
    component_tree: ComponentTree
    interactions: list[InteractionBehavior]
    responsive_rules: list[ResponsiveRule]
    dependencies: list[Dependency]
    recreation_prompt: str
```

---

### 6. Orchestrator

Coordena o pipeline completo.

```python
class ExtractionOrchestrator:
    def __init__(self, api_key: str, output_dir: str = "output"):
        self.api_key = api_key
        self.output_dir = output_dir
        self.browser = BrowserManager()
        self.synthesizer = OpenAISynthesizer(api_key)

    def extract(self, url: str, strategy: str, query: str,
                progress_callback=None, cancel_check=None) -> SynthesisOutput:

        cancel_check = cancel_check or (lambda: False)

        # 1: Navegar
        if cancel_check(): raise ExtractionError("Cancelado")
        self.browser.navigate(url)

        # 2: Encontrar alvo
        if cancel_check(): raise ExtractionError("Cancelado")
        target = TargetFinder(self.browser.page).find(strategy, query)

        # 3-9: Collector
        dom_data = DOMExtractor(self.browser.page).extract(target)
        style_data = StyleExtractor(self.browser.page).extract(target)
        interactions = InteractionMapper(self.browser.page).map(target)
        observed_states = InteractionPlayer(self.browser.page).play_all(target, interactions)
        animation_data = AnimationRecorder(self.browser.page, self.output_dir).record(target)
        assets = AssetDownloader(self.browser.page, self.output_dir).download_all(target)
        libraries = LibraryDetector(self.browser.page).detect()
        responsive_data = ResponsiveCollector(self.browser.page).collect_all(target)

        # 10: Normalizer
        normalized = ContextBuilder().build({...})

        # 11: Synthesizer
        if cancel_check(): raise ExtractionError("Cancelado")
        synthesis = self.synthesizer.synthesize(normalized)

        self.browser.close()
        return synthesis
```

---

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                         Tkinter GUI                             │
│  URL + Estratégia + Seletor  →  Botão Extrair                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator.extract()                      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Collector  │  →   │  Normalizer  │  →   │  Synthesizer │
│  (Playwright)│      │  (Pydantic)  │      │   (OpenAI)   │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ output/assets│      │ extraction_  │      │ Prompt Final │
│              │      │  timestamp   │      │  (copiado)   │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## Tratamento de Erros

### Estratégia de Erros

```python
class ExtractionError(Exception):
    """Erro base para extração."""
    pass

class NavigationError(ExtractionError):
    """Falha ao navegar para URL."""
    pass

class TargetNotFoundError(ExtractionError):
    """Seletor não encontrou elemento."""
    pass

class APIError(ExtractionError):
    """Falha na API OpenAI."""
    pass

class BrowserCrashError(ExtractionError):
    """Browser travou ou fechou inesperadamente."""
    pass
```

### Cenários Tratados

| Cenário | Ação |
|---------|------|
| URL inválida/network failure | Retry 3x com backoff, depois `NavigationError` |
| Seletor não encontra elemento | `TargetNotFoundError` com sugestões de seletores similares |
| API rate limit | Retry com backoff exponencial |
| API failure | `APIError` com opção de retry manual |
| Browser crash | Tentar reiniciar browser, se falhar `BrowserCrashError` |
| Timeout de operação | Configurável, default 30s, depois cancela |
| Asset download failure | Log warning, continua sem o asset |

---

## Modelo de Threading

Tkinter não é thread-safe. O pipeline roda em thread separada:

```python
import threading
import queue

class ExtractionWorker(threading.Thread):
    def __init__(self, orchestrator, url, strategy, query, callback_queue):
        super().__init__()
        self.orchestrator = orchestrator
        self.url = url
        self.strategy = strategy
        self.query = query
        self.callback_queue = callback_queue
        self._cancel_event = threading.Event()

    def run(self):
        try:
            result = self.orchestrator.extract(
                self.url, self.strategy, self.query,
                progress_callback=lambda step, msg: self.callback_queue.put(
                    ("progress", step, msg)
                ),
                cancel_check=self._cancel_event.is_set
            )
            self.callback_queue.put(("success", result))
        except ExtractionError as e:
            self.callback_queue.put(("error", str(e)))

    def cancel(self):
        self._cancel_event.set()
```

### GUI - Poll de Callbacks

```python
class ComponentExtractorApp:
    def __init__(self):
        self.callback_queue = queue.Queue()
        self.root.after(100, self._process_queue)

    def _process_queue(self):
        try:
            msg = self.callback_queue.get_nowait()
            self._handle_callback(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def _handle_callback(self, msg):
        msg_type = msg[0]
        if msg_type == "progress":
            _, step, text = msg
            self.progress_display.set_step(step, text)
        elif msg_type == "success":
            _, result = msg
            self.result_panel.display(result)
        elif msg_type == "error":
            _, error = msg
            messagebox.showerror("Erro", error)
```

---

## Suporte a Cancelamento

### Orchestrator com Cancelamento

```python
class ExtractionOrchestrator:
    def extract(self, url: str, strategy: str, query: str,
                progress_callback=None, cancel_check=None) -> SynthesisOutput:

        cancel_check = cancel_check or (lambda: False)

        # Check entre cada etapa
        if cancel_check():
            raise ExtractionError("Cancelado pelo usuário")

        self.browser.navigate(url)

        if cancel_check():
            raise ExtractionError("Cancelado pelo usuário")

        target = TargetFinder(self.browser.page).find(strategy, query)
        # ... continua com checks entre cada etapa
```

### GUI - Botão Cancelar

```python
def _on_extract(self):
    self.worker = ExtractionWorker(...)
    self.worker.start()
    self.extract_btn.config(text="Cancelar", command=self._on_cancel)
    self.cancel_btn.pack()

def _on_cancel(self):
    self.worker.cancel()
    self.status_label.config(text="Cancelando...")
```

---

## Notas sobre Pydantic v2

### Forward References

Modelos recursivos (`DOMTree`, `ComponentTree`) requerem `model_rebuild()`:

```python
from pydantic import BaseModel

class DOMTree(BaseModel):
    tag: str
    children: list["DOMTree"]

# Resolver forward reference
DOMTree.model_rebuild()
```

Isso deve ser feito em `models/__init__.py` após imports.

---

## Dependências (requirements.txt)

```
playwright>=1.40.0
pydantic>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
Pillow>=10.0.0
opencv-python>=4.8
```

---

## Configuração

### `.env.example`
```
OPENAI_API_KEY=sk-...
```

---

## Decisões de Design

| Aspecto | Decisão | Racional |
|---------|---------|----------|
| Interface | Tkinter | Nativo do Python, sem dependências extras |
| Modelo IA | GPT-5.4 | Maior capacidade de síntese |
| Estratégias de seleção | Múltiplas na v1 | Flexibilidade desde o início |
| Interações | Automático total | Mais poderoso, menos trabalho manual |
| Responsividade | Detecção automática de media queries | Preciso, captura pontos reais de mudança |
| Assets | Download local | Organização e trabalho offline |
| Animações | Screen recording + frames | Precisão total de timing |
| Bibliotecas externas | Detecta + extrai código de uso | Permite replicar comportamentos |
| Output prompt | Framework agnóstico | Versatilidade |
| API Key | Variável de ambiente | Segurança e simplicidade |

---

## Próximos Passos

Após aprovação deste documento, seguir para o plano de implementação usando a skill `writing-plans`.

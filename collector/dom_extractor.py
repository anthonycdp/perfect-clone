"""Extract DOM structure from elements."""

from playwright.async_api import Page, Locator


class DOMExtractor:
    """Extract DOM tree and related data from elements."""

    def __init__(self, page: Page):
        self.page = page

    async def extract(self, target: Locator) -> dict:
        """Extract complete DOM data from target element."""
        return {
            "html": await self._extract_html(target),
            "dom_tree": await self._extract_dom_tree(target),
            "bounding_box": await self._extract_bounding_box(target),
            "depth": await self._calculate_depth(target),
        }

    async def extract_page(self) -> dict:
        """Extract DOM data for the rendered page body."""
        return {
            "html": await self._extract_page_html(),
            "dom_tree": await self._extract_page_dom_tree(),
            "bounding_box": await self._extract_page_bounding_box(),
            "depth": 0,
        }

    async def _extract_html(self, target: Locator) -> str:
        """Get outer HTML of element."""
        return await target.evaluate("el => el.outerHTML")

    async def _extract_dom_tree(self, target: Locator) -> dict:
        """Build recursive DOM tree with attributes and styles."""
        return await target.evaluate(self._dom_tree_script())

    async def _extract_page_html(self) -> str:
        """Return the rendered body HTML for the current page."""
        return await self.page.evaluate(
            "() => document.body?.outerHTML || document.documentElement.outerHTML"
        )

    async def _extract_page_dom_tree(self) -> dict:
        """Build recursive DOM tree for the page body."""
        return await self.page.evaluate(
            f"""() => {{
                const root = document.body || document.documentElement;
                {self._build_tree_function()}
                return buildTree(root);
            }}"""
        )

    async def _extract_page_bounding_box(self) -> dict:
        """Return the full rendered page dimensions."""
        return await self.page.evaluate("""() => {
            const root = document.documentElement;
            const body = document.body;
            const width = Math.max(
                root.scrollWidth,
                root.clientWidth,
                body ? body.scrollWidth : 0,
                body ? body.clientWidth : 0
            );
            const height = Math.max(
                root.scrollHeight,
                root.clientHeight,
                body ? body.scrollHeight : 0,
                body ? body.clientHeight : 0
            );

            return { x: 0, y: 0, width, height };
        }""")

    async def _extract_bounding_box(self, target: Locator) -> dict:
        """Get element position and dimensions."""
        box = await target.bounding_box()
        if box is None:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        return {
            "x": box["x"],
            "y": box["y"],
            "width": box["width"],
            "height": box["height"],
        }

    async def _calculate_depth(self, target: Locator) -> int:
        """Calculate element depth in DOM tree."""
        return await target.evaluate("""el => {
            let depth = 0;
            let current = el;
            while (current.parentElement) {
                depth++;
                current = current.parentElement;
            }
            return depth;
        }""")

    def _dom_tree_script(self) -> str:
        """Return a reusable tree-building script for locator evaluation."""
        return f"""el => {{
            {self._build_tree_function()}
            return buildTree(el);
        }}"""

    def _build_tree_function(self) -> str:
        """Return the JS function that serializes a DOM subtree."""
        return """
            const relevantProps = [
                'display', 'position', 'flex-direction', 'grid-template-columns',
                'width', 'height', 'margin', 'padding', 'font-size', 'color',
                'background-color', 'border', 'opacity', 'transform'
            ];

            function buildShadowRootTree(shadowRoot) {
                const node = {
                    tag: '#shadow-root',
                    attributes: { mode: 'open' },
                    children: [],
                    text_content: null,
                    computed_styles: {},
                    shadow_root: null,
                };

                for (const child of shadowRoot.children) {
                    node.children.push(buildTree(child));
                }

                if (shadowRoot.children.length === 0) {
                    node.text_content = shadowRoot.textContent?.trim() || null;
                }

                return node;
            }

            function buildTree(element) {
                const node = {
                    tag: element.tagName.toLowerCase(),
                    attributes: {},
                    children: [],
                    text_content: null,
                    computed_styles: {},
                    shadow_root: null,
                };

                for (const attr of element.attributes) {
                    node.attributes[attr.name] = attr.value;
                }

                const styles = window.getComputedStyle(element);
                for (const prop of relevantProps) {
                    node.computed_styles[prop] = styles.getPropertyValue(prop);
                }

                for (const child of element.children) {
                    node.children.push(buildTree(child));
                }

                if (element.shadowRoot) {
                    node.shadow_root = buildShadowRootTree(element.shadowRoot);
                }

                if (element.children.length === 0 && !element.shadowRoot) {
                    node.text_content = element.textContent?.trim() || null;
                }

                return node;
            }
        """

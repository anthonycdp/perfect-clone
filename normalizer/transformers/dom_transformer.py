"""Transform raw DOM data into structured DOMTree."""

from models.normalized import DOMTree


class DOMTransformer:
    """Transform raw DOM extraction data."""

    IGNORED_ATTRIBUTES = {
        "data-reactid",
        "data-react-checksum",
        "data-testid",
        "ng-scope",
        "ng-binding",
    }

    def transform(self, raw_data: dict) -> DOMTree:
        """Transform raw DOM data into DOMTree model."""
        # Filter attributes
        filtered_attrs = {
            k: v
            for k, v in raw_data.get("attributes", {}).items()
            if k not in self.IGNORED_ATTRIBUTES
        }

        # Recursively transform children
        children = [
            self.transform(child) for child in raw_data.get("children", [])
        ]

        return DOMTree(
            tag=raw_data.get("tag", "div"),
            attributes=filtered_attrs,
            children=children,
            text_content=raw_data.get("text_content"),
            computed_styles=raw_data.get("computed_styles", {}),
        )

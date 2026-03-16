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
        filtered_attrs = self._filter_attributes(raw_data.get("attributes", {}))
        children = [self.transform(child) for child in raw_data.get("children", [])]
        shadow_root_data = raw_data.get("shadow_root")

        return DOMTree(
            tag=raw_data.get("tag", "div"),
            attributes=filtered_attrs,
            children=children,
            text_content=raw_data.get("text_content") or "",
            computed_styles=raw_data.get("computed_styles", {}),
            shadow_root=self.transform(shadow_root_data) if shadow_root_data else None,
        )

    def _filter_attributes(self, attributes: dict) -> dict:
        """Remove noisy framework attributes from a raw DOM node."""
        return {
            key: value
            for key, value in attributes.items()
            if key not in self.IGNORED_ATTRIBUTES
        }

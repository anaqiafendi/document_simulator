"""TemplateRegistry — maps (document_type, style_name) to DocumentTemplate instances.

Usage::

    from document_simulator.synthesis.template_registry import TemplateRegistry
    from document_simulator.synthesis.templates.receipt_thermal import receipt_thermal_template
    from document_simulator.synthesis.templates.receipt_a4 import receipt_a4_template

    registry = TemplateRegistry()
    registry.register("receipt", "thermal", receipt_thermal_template)
    registry.register("receipt", "a4", receipt_a4_template)

    tpl = registry.get("receipt", "thermal")
    styles = registry.list_styles("receipt")   # ["thermal", "a4"]
    types = registry.list_types()              # ["receipt"]
"""

from __future__ import annotations

from document_simulator.synthesis.document_template import DocumentTemplate


class TemplateRegistry:
    """A lightweight registry mapping (document_type, style_name) → DocumentTemplate.

    Each registry instance is independent; create one per application scope.
    For a project-wide shared registry, create a module-level instance and
    import it directly.

    Example::

        registry = TemplateRegistry()
        registry.register("receipt", "thermal", receipt_thermal_template)
        tpl = registry.get("receipt", "thermal")
    """

    def __init__(self) -> None:
        # _store: { document_type: { style_name: DocumentTemplate } }
        self._store: dict[str, dict[str, DocumentTemplate]] = {}

    def register(
        self,
        document_type: str,
        style_name: str,
        template: DocumentTemplate,
    ) -> None:
        """Register a template under (document_type, style_name).

        Overwrites any existing registration for the same key.

        Args:
            document_type: Logical document category (e.g. ``"receipt"``).
            style_name:    Visual variant name (e.g. ``"thermal"``).
            template:      The DocumentTemplate to register.
        """
        if document_type not in self._store:
            self._store[document_type] = {}
        self._store[document_type][style_name] = template

    def get(self, document_type: str, style_name: str) -> DocumentTemplate:
        """Retrieve a registered template.

        Args:
            document_type: Logical document category.
            style_name:    Visual variant name.

        Returns:
            The registered DocumentTemplate.

        Raises:
            KeyError: If no template is registered for (document_type, style_name).
        """
        if document_type not in self._store or style_name not in self._store[document_type]:
            raise KeyError(
                f"No template registered for document_type={document_type!r}, "
                f"style_name={style_name!r}. "
                f"Available: {self._available_str()}"
            )
        return self._store[document_type][style_name]

    def list_styles(self, document_type: str) -> list[str]:
        """Return all registered style names for a document type.

        Returns an empty list if the document type is unknown.
        """
        return list(self._store.get(document_type, {}).keys())

    def list_types(self) -> list[str]:
        """Return all registered document type names."""
        return list(self._store.keys())

    def _available_str(self) -> str:
        parts = []
        for dt, styles in self._store.items():
            for sn in styles:
                parts.append(f"({dt!r}, {sn!r})")
        return ", ".join(parts) if parts else "(none)"

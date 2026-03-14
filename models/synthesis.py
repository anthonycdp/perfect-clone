"""Pydantic models for synthesis output data."""

from typing import Optional

from pydantic import BaseModel


class ComponentDescription(BaseModel):
    """Human-readable description of the component."""

    technical: str
    visual: str
    purpose: str


class ComponentTree(BaseModel):
    """Recursive component tree structure.

    IMPORTANT: After defining this class, call ComponentTree.model_rebuild()
    to resolve the forward reference in the children field.
    """

    name: str
    role: str
    children: list["ComponentTree"]


# Rebuild the model to resolve forward references for recursive structure
ComponentTree.model_rebuild()


class InteractionBehavior(BaseModel):
    """Describes an interaction behavior of the component."""

    trigger: str
    effect: str
    animation: Optional[str] = None


class ResponsiveRule(BaseModel):
    """Responsive behavior rule at a specific breakpoint."""

    breakpoint: str
    changes: list[str]


class Dependency(BaseModel):
    """External dependency information."""

    name: str
    reason: str
    alternative: Optional[str] = None


class SynthesisOutput(BaseModel):
    """Combined synthesis output.

    Combines all synthesis models plus a recreation prompt
    for regenerating the component.
    """

    description: ComponentDescription
    component_tree: ComponentTree
    interactions: list[InteractionBehavior]
    responsive_rules: list[ResponsiveRule]
    dependencies: list[Dependency]
    recreation_prompt: str

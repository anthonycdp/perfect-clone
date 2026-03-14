"""Tests for synthesis data models."""

import pytest
from pydantic import ValidationError

from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    InteractionBehavior,
    ResponsiveRule,
    Dependency,
    SynthesisOutput,
)


class TestComponentDescription:
    """Tests for ComponentDescription model."""

    def test_component_description_with_all_fields(self):
        """ComponentDescription should accept all fields."""
        description = ComponentDescription(
            technical="A responsive card component using CSS Grid",
            visual="A white card with rounded corners and subtle shadow",
            purpose="Display product information in an e-commerce layout",
        )
        assert description.technical == "A responsive card component using CSS Grid"
        assert description.visual == "A white card with rounded corners and subtle shadow"
        assert description.purpose == "Display product information in an e-commerce layout"

    def test_component_description_requires_all_fields(self):
        """ComponentDescription should require all fields."""
        with pytest.raises(ValidationError):
            ComponentDescription(technical="Test")

        with pytest.raises(ValidationError):
            ComponentDescription(technical="Test", visual="Test")


class TestComponentTree:
    """Tests for ComponentTree model - RECURSIVE structure."""

    def test_component_tree_leaf_node(self):
        """ComponentTree should work as a leaf node without children."""
        tree = ComponentTree(
            name="Button",
            role="interactive element",
            children=[],
        )
        assert tree.name == "Button"
        assert tree.role == "interactive element"
        assert tree.children == []

    def test_component_tree_with_nested_children(self):
        """ComponentTree should support recursive nesting."""
        # Create nested structure: Card > CardBody > Text
        text = ComponentTree(
            name="Text",
            role="content",
            children=[],
        )
        card_body = ComponentTree(
            name="CardBody",
            role="container",
            children=[text],
        )
        card = ComponentTree(
            name="Card",
            role="container",
            children=[card_body],
        )

        assert card.name == "Card"
        assert len(card.children) == 1
        assert card.children[0].name == "CardBody"
        assert card.children[0].children[0].name == "Text"

    def test_component_tree_with_multiple_children(self):
        """ComponentTree should support multiple children."""
        icon = ComponentTree(name="Icon", role="decoration", children=[])
        title = ComponentTree(name="Title", role="heading", children=[])
        description = ComponentTree(name="Description", role="content", children=[])

        feature = ComponentTree(
            name="Feature",
            role="container",
            children=[icon, title, description],
        )

        assert feature.name == "Feature"
        assert len(feature.children) == 3
        assert feature.children[0].name == "Icon"
        assert feature.children[1].name == "Title"
        assert feature.children[2].name == "Description"

    def test_component_tree_deeply_nested(self):
        """ComponentTree should handle deeply nested structures."""
        leaf = ComponentTree(name="Leaf", role="element", children=[])
        level3 = ComponentTree(name="Level3", role="container", children=[leaf])
        level2 = ComponentTree(name="Level2", role="container", children=[level3])
        level1 = ComponentTree(name="Level1", role="container", children=[level2])
        root = ComponentTree(name="Root", role="root", children=[level1])

        assert root.children[0].children[0].children[0].children[0].name == "Leaf"

    def test_component_tree_requires_all_fields(self):
        """ComponentTree should require all fields."""
        with pytest.raises(ValidationError):
            ComponentTree(name="Test")


class TestInteractionBehavior:
    """Tests for InteractionBehavior model."""

    def test_interaction_behavior_with_animation(self):
        """InteractionBehavior should accept all fields including animation."""
        behavior = InteractionBehavior(
            trigger="click",
            effect="Opens modal dialog",
            animation="fade-in 0.3s ease-out",
        )
        assert behavior.trigger == "click"
        assert behavior.effect == "Opens modal dialog"
        assert behavior.animation == "fade-in 0.3s ease-out"

    def test_interaction_behavior_without_animation(self):
        """InteractionBehavior should work without optional animation."""
        behavior = InteractionBehavior(
            trigger="hover",
            effect="Shows dropdown menu",
        )
        assert behavior.trigger == "hover"
        assert behavior.effect == "Shows dropdown menu"
        assert behavior.animation is None

    def test_interaction_behavior_requires_trigger_and_effect(self):
        """InteractionBehavior should require trigger and effect."""
        with pytest.raises(ValidationError):
            InteractionBehavior(trigger="click")

        with pytest.raises(ValidationError):
            InteractionBehavior(effect="Does something")


class TestResponsiveRule:
    """Tests for ResponsiveRule model."""

    def test_responsive_rule_with_all_fields(self):
        """ResponsiveRule should accept all fields."""
        rule = ResponsiveRule(
            breakpoint="768px",
            changes=["Stack elements vertically", "Hide sidebar"],
        )
        assert rule.breakpoint == "768px"
        assert rule.changes == ["Stack elements vertically", "Hide sidebar"]

    def test_responsive_rule_with_empty_changes(self):
        """ResponsiveRule should work with empty changes list."""
        rule = ResponsiveRule(
            breakpoint="1024px",
            changes=[],
        )
        assert rule.breakpoint == "1024px"
        assert rule.changes == []

    def test_responsive_rule_requires_all_fields(self):
        """ResponsiveRule should require all fields."""
        with pytest.raises(ValidationError):
            ResponsiveRule(breakpoint="768px")


class TestDependency:
    """Tests for Dependency model."""

    def test_dependency_with_all_fields(self):
        """Dependency should accept all fields."""
        dependency = Dependency(
            name="GSAP",
            reason="Used for scroll-triggered animations",
            alternative="CSS scroll-timeline (limited browser support)",
        )
        assert dependency.name == "GSAP"
        assert dependency.reason == "Used for scroll-triggered animations"
        assert dependency.alternative == "CSS scroll-timeline (limited browser support)"

    def test_dependency_without_alternative(self):
        """Dependency should work without optional alternative."""
        dependency = Dependency(
            name="FontAwesome",
            reason="Icon library for social media icons",
        )
        assert dependency.name == "FontAwesome"
        assert dependency.reason == "Icon library for social media icons"
        assert dependency.alternative is None

    def test_dependency_requires_name_and_reason(self):
        """Dependency should require name and reason."""
        with pytest.raises(ValidationError):
            Dependency(name="Test")

        with pytest.raises(ValidationError):
            Dependency(reason="Some reason")


class TestSynthesisOutput:
    """Tests for SynthesisOutput model - combines all above + recreation_prompt."""

    def test_synthesis_output_with_all_fields(self):
        """SynthesisOutput should combine all synthesis models."""
        description = ComponentDescription(
            technical="A hero section with parallax effect",
            visual="Full-width image with centered text overlay",
            purpose="Landing page hero section to capture user attention",
        )
        child = ComponentTree(name="Heading", role="text", children=[])
        tree = ComponentTree(name="HeroSection", role="container", children=[child])
        behavior = InteractionBehavior(
            trigger="scroll",
            effect="Parallax movement of background",
            animation="transform 0.5s ease-out",
        )
        rule = ResponsiveRule(
            breakpoint="768px",
            changes=["Reduce text size", "Stack elements"],
        )
        dependency = Dependency(
            name="None",
            reason="All effects achieved with CSS",
        )

        output = SynthesisOutput(
            description=description,
            component_tree=tree,
            interaction_behaviors=[behavior],
            responsive_rules=[rule],
            dependencies=[dependency],
            recreation_prompt="Create a hero section with...",
        )

        assert output.description.technical == "A hero section with parallax effect"
        assert output.component_tree.name == "HeroSection"
        assert len(output.interaction_behaviors) == 1
        assert output.interaction_behaviors[0].trigger == "scroll"
        assert len(output.responsive_rules) == 1
        assert output.responsive_rules[0].breakpoint == "768px"
        assert len(output.dependencies) == 1
        assert output.dependencies[0].name == "None"
        assert output.recreation_prompt == "Create a hero section with..."

    def test_synthesis_output_with_empty_lists(self):
        """SynthesisOutput should work with empty lists for optional collections."""
        description = ComponentDescription(
            technical="Simple button",
            visual="Blue button with white text",
            purpose="Submit form",
        )
        tree = ComponentTree(name="Button", role="interactive", children=[])

        output = SynthesisOutput(
            description=description,
            component_tree=tree,
            interaction_behaviors=[],
            responsive_rules=[],
            dependencies=[],
            recreation_prompt="Create a simple blue button",
        )

        assert output.interaction_behaviors == []
        assert output.responsive_rules == []
        assert output.dependencies == []

    def test_synthesis_output_requires_all_fields(self):
        """SynthesisOutput should require all component models and recreation_prompt."""
        with pytest.raises(ValidationError):
            SynthesisOutput()

        description = ComponentDescription(
            technical="Test",
            visual="Test",
            purpose="Test",
        )
        tree = ComponentTree(name="Test", role="test", children=[])

        # Missing recreation_prompt
        with pytest.raises(ValidationError):
            SynthesisOutput(
                description=description,
                component_tree=tree,
                interaction_behaviors=[],
                responsive_rules=[],
                dependencies=[],
            )

    def test_synthesis_output_recreation_prompt_required(self):
        """SynthesisOutput must have recreation_prompt."""
        description = ComponentDescription(
            technical="Test",
            visual="Test",
            purpose="Test",
        )
        tree = ComponentTree(name="Test", role="test", children=[])

        output = SynthesisOutput(
            description=description,
            component_tree=tree,
            interaction_behaviors=[],
            responsive_rules=[],
            dependencies=[],
            recreation_prompt="This is required",
        )

        assert output.recreation_prompt == "This is required"

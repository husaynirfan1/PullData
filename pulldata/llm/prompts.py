"""
Prompt template system for PullData.

Provides flexible prompt templates for RAG-based question answering.
"""

from __future__ import annotations

from typing import Any, Optional


class PromptTemplate:
    """
    Represents a prompt template with variable substitution.
    """

    def __init__(
        self,
        template: str,
        input_variables: Optional[list[str]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize prompt template.

        Args:
            template: Template string with {variable} placeholders
            input_variables: List of variable names (auto-detected if None)
            name: Template name
            description: Template description
        """
        self.template = template
        self.name = name
        self.description = description

        # Auto-detect variables if not provided
        if input_variables is None:
            import re

            self.input_variables = list(set(re.findall(r"\{(\w+)\}", template)))
        else:
            self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        """
        Format template with provided variables.

        Args:
            **kwargs: Variable values

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing variables
        missing = set(self.input_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Format template
        return self.template.format(**kwargs)

    def __repr__(self) -> str:
        name = self.name or "PromptTemplate"
        return f"{name}(variables={self.input_variables})"


class PromptManager:
    """
    Manages a collection of prompt templates.
    """

    def __init__(self):
        """Initialize prompt manager."""
        self.templates: dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates for RAG."""

        # Basic Q&A template
        self.add_template(
            name="basic_qa",
            template="""Answer the following question based on the provided context.

Context:
{context}

Question: {query}

Answer:""",
            description="Basic question-answering template",
        )

        # Detailed Q&A template
        self.add_template(
            name="detailed_qa",
            template="""You are a helpful AI assistant. Answer the following question based on the provided context.
If the answer is not in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Please provide a detailed answer:""",
            description="Detailed question-answering with fallback",
        )

        # Extractive Q&A template
        self.add_template(
            name="extractive_qa",
            template="""Extract relevant information from the context to answer the question.
Quote directly from the context when possible.

Context:
{context}

Question: {query}

Answer (with quotes):""",
            description="Extractive Q&A with direct quotes",
        )

        # Summarization template
        self.add_template(
            name="summarize",
            template="""Summarize the following content in a clear and concise manner.

Content:
{context}

Summary:""",
            description="Content summarization",
        )

        # Multi-document Q&A template
        self.add_template(
            name="multi_doc_qa",
            template="""Answer the following question using information from multiple documents.
Cite the document sources when providing your answer.

Documents:
{context}

Question: {query}

Answer (with document citations):""",
            description="Multi-document question answering with citations",
        )

        # Conversational template
        self.add_template(
            name="conversational",
            template="""You are a helpful AI assistant. Use the provided context to answer the user's question.
Be conversational and friendly in your response.

Context:
{context}

User: {query}
Assistant: {response}""",
            description="Conversational assistant template",
        )

    def add_template(
        self,
        name: str,
        template: str,
        input_variables: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Add a new template.

        Args:
            name: Template name
            template: Template string
            input_variables: List of variable names (auto-detected if None)
            description: Template description
        """
        prompt_template = PromptTemplate(
            template=template,
            input_variables=input_variables,
            name=name,
            description=description,
        )
        self.templates[name] = prompt_template

    def get_template(self, name: str) -> PromptTemplate:
        """
        Get template by name.

        Args:
            name: Template name

        Returns:
            PromptTemplate object

        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            raise KeyError(f"Template not found: {name}")
        return self.templates[name]

    def list_templates(self) -> list[str]:
        """
        List all template names.

        Returns:
            List of template names
        """
        return list(self.templates.keys())

    def format_prompt(self, name: str, **kwargs) -> str:
        """
        Format a template by name.

        Args:
            name: Template name
            **kwargs: Variable values

        Returns:
            Formatted prompt string
        """
        template = self.get_template(name)
        return template.format(**kwargs)

    def __repr__(self) -> str:
        return f"PromptManager({len(self.templates)} templates)"

"""Built-in plugins that come with the system."""

from typing import Dict, Any, List
from .base import Plugin, PluginConfig
from .hooks import PluginHook
import re


class QueryCleanerPlugin(Plugin):
    """Cleans and normalizes user queries."""

    name = "QueryCleaner"
    version = "1.0.0"
    description = "Cleans and normalizes user queries (removes extra whitespace, fixes common typos)"
    author = "LLM Council"
    hooks = [PluginHook.ON_QUERY_RECEIVED.value]

    async def on_query_received(self, query: str, context: Dict[str, Any]) -> str:
        """Clean the query."""
        # Remove extra whitespace
        cleaned = ' '.join(query.split())

        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()

        # Fix common typos
        typo_fixes = self.config.settings.get('typo_fixes', {
            'teh': 'the',
            'recieve': 'receive',
            'occured': 'occurred',
        })
        for typo, fix in typo_fixes.items():
            cleaned = re.sub(r'\b' + typo + r'\b', fix, cleaned, flags=re.IGNORECASE)

        return cleaned


class ResponseFormatterPlugin(Plugin):
    """Formats the final response for better readability."""

    name = "ResponseFormatter"
    version = "1.0.0"
    description = "Formats the final synthesis for better readability"
    author = "LLM Council"
    hooks = [PluginHook.ON_SYNTHESIS_COMPLETE.value]

    async def on_synthesis_complete(
        self,
        query: str,
        synthesis: str,
        context: Dict[str, Any]
    ) -> str:
        """Format the synthesis."""
        formatted = synthesis

        # Add section headers if configured
        if self.config.settings.get('add_sections', False):
            # Simple heuristic: if there are multiple paragraphs, add headers
            paragraphs = formatted.split('\n\n')
            if len(paragraphs) > 2:
                formatted = "\n\n".join([
                    f"**Key Points:**\n{paragraphs[0]}" if i == 0 else p
                    for i, p in enumerate(paragraphs)
                ])

        # Add summary at the end if configured
        if self.config.settings.get('add_summary', False):
            if len(synthesis) > 500:
                formatted += "\n\n---\n*This response was synthesized from multiple AI perspectives.*"

        return formatted


class MetadataEnricherPlugin(Plugin):
    """Enriches responses with additional metadata."""

    name = "MetadataEnricher"
    version = "1.0.0"
    description = "Adds useful metadata to responses (word count, complexity score, etc.)"
    author = "LLM Council"
    hooks = [PluginHook.ON_RESPONSE_COMPLETE.value]

    async def on_response_complete(
        self,
        query: str,
        full_response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add metadata to the response."""
        synthesis = full_response.get('stage3', {}).get('response', '')

        # Calculate word count
        word_count = len(synthesis.split())

        # Calculate complexity score (simple heuristic)
        avg_word_length = sum(len(w) for w in synthesis.split()) / max(word_count, 1)
        complexity = 'simple' if avg_word_length < 5 else ('moderate' if avg_word_length < 7 else 'complex')

        # Add metadata
        if 'metadata' not in full_response:
            full_response['metadata'] = {}

        full_response['metadata']['plugin_enrichment'] = {
            'word_count': word_count,
            'complexity': complexity,
            'avg_word_length': round(avg_word_length, 2),
        }

        return full_response


class LanguageDetectorPlugin(Plugin):
    """Detects the language of queries and responses."""

    name = "LanguageDetector"
    version = "1.0.0"
    description = "Detects the language of queries (useful for multilingual support)"
    author = "LLM Council"
    hooks = [PluginHook.ON_QUERY_RECEIVED.value]

    # Common words by language
    LANGUAGE_MARKERS = {
        'en': ['the', 'is', 'are', 'what', 'how', 'why', 'can', 'do'],
        'es': ['el', 'la', 'es', 'que', 'como', 'por', 'una', 'los'],
        'fr': ['le', 'la', 'est', 'que', 'pour', 'une', 'les', 'des'],
        'de': ['der', 'die', 'das', 'ist', 'ein', 'eine', 'wie', 'was'],
    }

    async def on_query_received(self, query: str, context: Dict[str, Any]) -> str:
        """Detect language and add to context."""
        words = query.lower().split()

        scores = {}
        for lang, markers in self.LANGUAGE_MARKERS.items():
            score = sum(1 for w in words if w in markers)
            scores[lang] = score

        # Get the highest scoring language
        detected_lang = max(scores.keys(), key=lambda k: scores[k])

        # Add to context (note: context is mutable)
        context['detected_language'] = detected_lang

        return query


# Registry of built-in plugins
BUILTIN_PLUGINS = {
    'QueryCleaner': QueryCleanerPlugin,
    'ResponseFormatter': ResponseFormatterPlugin,
    'MetadataEnricher': MetadataEnricherPlugin,
    'LanguageDetector': LanguageDetectorPlugin,
}


def get_builtin_plugin(name: str):
    """Get a built-in plugin class by name."""
    return BUILTIN_PLUGINS.get(name)


def list_builtin_plugins():
    """List all available built-in plugins."""
    return [
        {
            'name': name,
            'version': cls.version,
            'description': cls.description,
            'hooks': cls.hooks,
        }
        for name, cls in BUILTIN_PLUGINS.items()
    ]

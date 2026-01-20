"""Constitution storage and persistence."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from ..config import CONSTITUTION_CONFIG
from .templates import get_default_constitution


class ConstitutionStore:
    """Manages constitution storage."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            CONSTITUTION_CONFIG.get('storage_path', 'data/constitution'),
            'constitution.json'
        )
        self.history_path = os.path.join(
            os.path.dirname(self.storage_path),
            'constitution_history.json'
        )
        self.constitution: Optional[Dict[str, Any]] = None
        self.history: List[Dict[str, Any]] = []
        self._ensure_storage_dir()
        self._load_constitution()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_constitution(self):
        """Load constitution from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.constitution = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading constitution: {e}")
                self.constitution = None

        # Load history
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r') as f:
                    self.history = json.load(f).get('history', [])
            except (json.JSONDecodeError, KeyError):
                self.history = []

        # Initialize with default if no constitution exists
        if self.constitution is None:
            self.constitution = get_default_constitution()
            self.constitution['ratified_at'] = datetime.utcnow().isoformat()
            self._save_constitution()

    def _save_constitution(self):
        """Save constitution to storage."""
        self._ensure_storage_dir()

        with open(self.storage_path, 'w') as f:
            json.dump(self.constitution, f, indent=2)

    def _save_history(self):
        """Save constitution history."""
        self._ensure_storage_dir()

        data = {
            'last_updated': datetime.utcnow().isoformat(),
            'history': self.history[-100:]  # Keep last 100 entries
        }
        with open(self.history_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_constitution(self) -> Dict[str, Any]:
        """Get the current constitution."""
        return self.constitution.copy()

    def update_constitution(self, updates: Dict[str, Any], reason: str = None):
        """
        Update the constitution.

        Args:
            updates: Fields to update
            reason: Reason for the update
        """
        # Record history
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'update',
            'reason': reason,
            'previous_version': self.constitution.get('version'),
            'changes': list(updates.keys())
        })

        # Apply updates
        self.constitution.update(updates)
        self.constitution['last_modified'] = datetime.utcnow().isoformat()

        self._save_constitution()
        self._save_history()

    def add_article(self, article: Dict[str, Any], reason: str = None):
        """
        Add a new article to the constitution.

        Args:
            article: Article dict
            reason: Reason for addition
        """
        articles = self.constitution.get('articles', [])

        # Set article number
        article['number'] = len(articles) + 1

        articles.append(article)

        # Record history
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'add_article',
            'article_id': article.get('id'),
            'article_title': article.get('title'),
            'reason': reason
        })

        self.constitution['articles'] = articles
        self.constitution['amendment_count'] = self.constitution.get('amendment_count', 0) + 1
        self.constitution['last_modified'] = datetime.utcnow().isoformat()

        self._save_constitution()
        self._save_history()

    def remove_article(self, article_id: str, reason: str = None) -> bool:
        """
        Remove an article from the constitution.

        Args:
            article_id: Article ID to remove
            reason: Reason for removal

        Returns:
            True if removed, False if not found
        """
        articles = self.constitution.get('articles', [])
        original_count = len(articles)

        # Find and remove article
        articles = [a for a in articles if a.get('id') != article_id]

        if len(articles) == original_count:
            return False

        # Renumber remaining articles
        for i, article in enumerate(articles, 1):
            article['number'] = i

        # Record history
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'remove_article',
            'article_id': article_id,
            'reason': reason
        })

        self.constitution['articles'] = articles
        self.constitution['amendment_count'] = self.constitution.get('amendment_count', 0) + 1
        self.constitution['last_modified'] = datetime.utcnow().isoformat()

        self._save_constitution()
        self._save_history()
        return True

    def update_article(
        self,
        article_id: str,
        updates: Dict[str, Any],
        reason: str = None
    ) -> bool:
        """
        Update an existing article.

        Args:
            article_id: Article ID to update
            updates: Fields to update
            reason: Reason for update

        Returns:
            True if updated, False if not found
        """
        articles = self.constitution.get('articles', [])

        for article in articles:
            if article.get('id') == article_id:
                # Record history
                self.history.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'update_article',
                    'article_id': article_id,
                    'previous_text': article.get('text'),
                    'reason': reason
                })

                # Apply updates (except id and number)
                for key, value in updates.items():
                    if key not in ['id', 'number']:
                        article[key] = value

                self.constitution['amendment_count'] = (
                    self.constitution.get('amendment_count', 0) + 1
                )
                self.constitution['last_modified'] = datetime.utcnow().isoformat()

                self._save_constitution()
                self._save_history()
                return True

        return False

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific article by ID."""
        for article in self.constitution.get('articles', []):
            if article.get('id') == article_id:
                return article.copy()
        return None

    def get_article_by_number(self, number: int) -> Optional[Dict[str, Any]]:
        """Get a specific article by number."""
        for article in self.constitution.get('articles', []):
            if article.get('number') == number:
                return article.copy()
        return None

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get constitution change history."""
        return self.history[-limit:]


# Singleton instance
_constitution_store: Optional[ConstitutionStore] = None


def get_constitution_store() -> ConstitutionStore:
    """Get the singleton constitution store."""
    global _constitution_store
    if _constitution_store is None:
        _constitution_store = ConstitutionStore()
    return _constitution_store


def get_constitution() -> Dict[str, Any]:
    """Get the current constitution."""
    return get_constitution_store().get_constitution()


def save_constitution(constitution: Dict[str, Any], reason: str = None):
    """Save a complete constitution."""
    store = get_constitution_store()
    store.update_constitution(constitution, reason)


def get_article(article_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific article."""
    return get_constitution_store().get_article(article_id)


def get_constitution_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get constitution change history."""
    return get_constitution_store().get_history(limit)

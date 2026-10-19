"""Experimental opt-in FTS5 fast path. Default MemoryStore behavior is unchanged.

Zero-hit fallback is not recall-equivalent to substring search: a nonempty exact
token result can omit other substring-only matches. No semantic retrieval.
"""
import sqlite3
from dataclasses import dataclass
from .store import MemoryStore


@dataclass(frozen=True)
class RetrievalResult:
    entries: list
    used_fallback: bool
    mode: str
    recall_warning: str = "FTS token hits can omit substring-only matches; use MemoryStore.search for original substring semantics."


class OptionalHybridIndex:
    """Explicitly creates a local index and insert trigger in the supplied DB.

    Supports the store's append/supersede API, not direct SQL edits/deletes.
    Search returns data and diagnostics; it does not automatically export context.
    """
    def __init__(self, store: MemoryStore):
        self.store = store
        self.available = False
        try:
            with store.db:
                store.db.execute('BEGIN IMMEDIATE')
                exists = store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pmk_hybrid_fts_v1'").fetchone()
                store.db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS pmk_hybrid_fts_v1 USING fts5(topic,content)')
                store.db.execute('''CREATE TRIGGER IF NOT EXISTS pmk_hybrid_insert_v1 AFTER INSERT ON entries BEGIN
                    INSERT INTO pmk_hybrid_fts_v1(rowid,topic,content) VALUES(new.id,new.topic,new.content);
                END''')
                if not exists:
                    store.db.execute('INSERT INTO pmk_hybrid_fts_v1(rowid,topic,content) SELECT id,topic,content FROM entries')
            self.available = True
        except sqlite3.OperationalError as exc:
            if 'no such module: fts5' not in str(exc).lower():
                raise

    def search(self, project, query):
        self.store._project(project)
        if not isinstance(query, str):
            raise ValueError('Query must be text')
        terms = query.split()
        if self.available and terms:
            match = ' AND '.join('"' + term.replace('"', '""') + '"' for term in terms)
            rows = self.store.db.execute('''SELECT e.* FROM pmk_hybrid_fts_v1
                JOIN entries e ON e.id=pmk_hybrid_fts_v1.rowid
                WHERE pmk_hybrid_fts_v1 MATCH ? AND e.project=?
                AND NOT EXISTS (SELECT 1 FROM entries n WHERE n.supersedes=e.id)
                ORDER BY e.id DESC''', (match, project)).fetchall()
            # FTS normalizes punctuation/diacritics. Remove candidates that do not
            # satisfy the original substring predicate before deciding fallback.
            lowered = [term.casefold() for term in terms]
            filtered = [dict(row) for row in rows if all(term in (row['topic'] + ' ' + row['content']).casefold() for term in lowered)]
            if filtered:
                return RetrievalResult(filtered, False, 'fts_token')
        return RetrievalResult(self.store.search(project, query), True, 'linear_substring')

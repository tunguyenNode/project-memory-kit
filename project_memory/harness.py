"""Explicit session hooks around the store, without model or agent coupling."""
from dataclasses import dataclass
import json
from .store import MemoryStore, check_text


@dataclass(frozen=True)
class Observation:
    topic: str
    content: str
    source: str
    author: str = "user"
    observed_at: str | None = None
    review_after: str | None = None


class Harness:
    """Caller controls project selection, approved writes and model integration.

    Hooks never ingest conversations automatically or grant action authority.
    session_start returns valid bounded JSON with a trust envelope.
    """

    def __init__(self, store: MemoryStore):
        self.store = store

    def session_start(self, project, query="", budget=8000):
        return self.store.export_context(project, query=query, max_chars=budget)

    def _record(self, project, observation, kind, **kwargs):
        if not isinstance(observation, Observation):
            raise ValueError("Use an explicit Observation with topic, content and source")
        return self.store.add(project, kind, observation.topic, observation.content,
                              observation.source, observation.author,
                              observed_at=observation.observed_at,
                              review_after=observation.review_after, **kwargs)

    def record_observation(self, project, observation):
        return self._record(project, observation, "fact")

    def record_decision(self, project, observation, *, supersedes=None, reason=""):
        return self._record(project, observation, "decision", supersedes=supersedes, reason=reason)

    def session_end(self, project, *, summary, next_step, source, author="user"):
        """Persist an explicitly reviewed checkpoint, replacing prior checkpoint.

        No raw chat is ingested automatically; callers supply reviewed summaries.
        """
        if any(not isinstance(v, str) or not v.strip() for v in (summary, next_step)):
            raise ValueError("Checkpoint needs explicit nonempty summary and next_step text")
        check_text(summary)
        check_text(next_step)
        existing = [row for row in self.store.search(project)
                    if row["kind"] == "fact" and row["topic"] == "session.checkpoint"]
        if len(existing) > 1:
            raise ValueError("Multiple active checkpoints; resolve them explicitly before saving")
        content = json.dumps({"summary": summary, "next_step": next_step}, ensure_ascii=True)
        return self._record(project, Observation("session.checkpoint", content, source, author), "fact",
                            supersedes=existing[0]["id"] if existing else None,
                            reason="Explicit next-session checkpoint" if existing else "")

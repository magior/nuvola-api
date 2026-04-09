import json
import os
from pathlib import Path
from typing import Optional

from nuvola.domain.models import SessionContext


class FileSessionStore:
    def __init__(self, path: Path = Path(".nuvola-session.json")):
        self.path = path

    def load(self) -> Optional[SessionContext]:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.clear()
            return None

        if not isinstance(payload, dict):
            self.clear()
            return None

        token = payload.get("token")
        backend = payload.get("backend")
        if not token or not backend:
            return None

        return SessionContext(
            backend=str(backend),
            token=str(token),
            student_id=str(payload["student_id"]) if payload.get("student_id") else None,
            tenant=str(payload["tenant"]) if payload.get("tenant") else None,
        )

    def save(self, session: SessionContext) -> None:
        payload = {
            "backend": session.backend,
            "token": session.token,
            "student_id": session.student_id,
            "tenant": session.tenant,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

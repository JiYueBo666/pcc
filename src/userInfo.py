from __future__ import annotations

from typing import Optional

from src.repositories.user_repository import UserRepository


class UserSessionManager:
    """
    Legacy compatibility wrapper.

    New code should use UserService/UserRepository directly.
    """

    def __init__(self):
        self._repository = UserRepository()
        self.mapping_file = self._repository.mapping_file
        self._mapping = self._repository._mapping

    def _load_mapping(self):
        return self._repository._load_mapping()

    def _save_mapping(self):
        self._repository._save_mapping()
        self._mapping = self._repository._mapping

    def bind_session_to_user(self, username: str, session_id: str) -> None:
        self._repository.bind_session_to_user(username=username, session_id=session_id)
        self._mapping = self._repository._mapping

    def get_user_sessions(self, username: Optional[str] = None) -> list[str]:
        return self._repository.get_user_sessions(username=username)

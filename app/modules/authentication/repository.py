"""Authentication — repository (data access for `users`)."""

from typing import Optional

from app.core.repository import BaseRepository
from app.modules.authentication.models import User


class UserRepository(BaseRepository):
    def find_active_by_username(self, username: str) -> Optional[User]:
        row = self._one(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
        )
        return User.from_row(row)

"""Always-allow / deny gates for unit tests (no Rich prompts)."""

from __future__ import annotations

import pytest


class AlwaysAllowGate:
    def confirm(self, prompt: str) -> bool:
        return True

    def show_diff(self, path: str, diff: str) -> None:
        return None

    def notify(self, message: str) -> None:
        return None


class AlwaysDenyGate:
    def confirm(self, prompt: str) -> bool:
        return False

    def show_diff(self, path: str, diff: str) -> None:
        return None

    def notify(self, message: str) -> None:
        return None


@pytest.fixture
def allow_gate() -> AlwaysAllowGate:
    return AlwaysAllowGate()


@pytest.fixture
def deny_gate() -> AlwaysDenyGate:
    return AlwaysDenyGate()

"""Fixtures communes : l'intégration personnalisée est chargeable dans les tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield

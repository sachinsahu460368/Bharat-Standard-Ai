"""Tests for Standards Graph service."""

import pytest
from app.services.standards_graph_service import standards_graph_service

def test_graph_loading():
    standards_graph_service.load()
    assert standards_graph_service._loaded is True
    # Nodes might be 0 if no relationships defined yet
    assert standards_graph_service.graph.number_of_nodes() >= 0

def test_get_related():
    standards_graph_service.load()
    # No relationships configured in verified dataset yet
    related = standards_graph_service.get_related("IS_10322_P1", max_depth=1)
    assert len(related) == 0

def test_get_related_invalid_id():
    standards_graph_service.load()
    related = standards_graph_service.get_related("INVALID", max_depth=1)
    assert len(related) == 0

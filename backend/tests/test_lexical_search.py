"""Tests for BM25 lexical search service (Phase 3)."""

from app.services.lexical_search_service import (
    BM25Index,
    LexicalSearchService,
    _tokenize,
    lexical_search_service,
)


# ------------------------------------------------------------------
# Tokenizer
# ------------------------------------------------------------------

class TestTokenizer:
    def test_basic_tokenization(self):
        tokens = _tokenize("LED luminaire outdoor IS 10322")
        assert "led" in tokens
        assert "luminaire" in tokens
        assert "outdoor" in tokens
        assert "10322" in tokens

    def test_stop_words_removed(self):
        tokens = _tokenize("the quick brown fox and a lazy dog")
        assert "the" not in tokens
        assert "and" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens

    def test_compound_tokens(self):
        tokens = _tokenize("IS/IEC 60947 self-ballasted")
        assert "is/iec" in tokens
        assert "self-ballasted" in tokens

    def test_empty_input(self):
        assert _tokenize("") == []

    def test_single_char_removed(self):
        """Single-char tokens are excluded (len > 1 filter)."""
        tokens = _tokenize("I a x 42 hello")
        assert "hello" in tokens
        assert "42" in tokens
        assert "x" not in tokens


# ------------------------------------------------------------------
# BM25Index
# ------------------------------------------------------------------

class TestBM25Index:
    def test_build_and_query(self):
        idx = BM25Index()
        docs = [
            ("IS_10322_P1", "Luminaires General Requirements and Tests"),
            ("IS_10322_P5_S3", "Road and Street Lighting Luminaires"),
            ("IS_16103_P1", "LED modules safety requirements"),
        ]
        idx.build(docs)
        results = idx.query("LED outdoor lighting", top_k=3)
        assert len(results) > 0
        assert results[0][0] in ["IS_10322_P5_S3", "IS_16103_P1"]

    def test_query_no_match(self):
        idx = BM25Index()
        idx.build([("d1", "hello world")])
        results = idx.query("zzzyyyxxx", top_k=5)
        assert results == []

    def test_empty_index(self):
        idx = BM25Index()
        idx.build([])
        assert idx.query("test") == []

    def test_top_k_limit(self):
        idx = BM25Index()
        docs = [(f"d{i}", f"word_{i} common") for i in range(20)]
        idx.build(docs)
        results = idx.query("common", top_k=5)
        assert len(results) <= 5


# ------------------------------------------------------------------
# LexicalSearchService (integration with real data)
# ------------------------------------------------------------------

class TestLexicalSearchService:
    """Integration tests using the module-level singleton with real data."""

    def test_service_is_built(self):
        assert lexical_search_service.is_built is True

    def test_search_led(self):
        results = lexical_search_service.search("LED luminaire outdoor", top_k=5)
        assert len(results) > 0
        numbers = [r.standard_number for r in results]
        assert any("10322" in n for n in numbers)

    def test_search_exact_is_number_boost(self):
        """Searching for an exact IS number should put that standard first."""
        results = lexical_search_service.search("IS 10322", top_k=5)
        assert len(results) > 0
        assert "IS 10322" in results[0].standard_number
        assert results[0].score == 1.0

    def test_search_results_have_evidence(self):
        results = lexical_search_service.search("road lighting", top_k=5)
        assert len(results) > 0
        for r in results:
            if r.evidence:
                assert r.evidence[0].source_type == "BIS"

    def test_search_scores_normalized(self):
        results = lexical_search_service.search("LED modules", top_k=5)
        assert len(results) > 0
        for r in results:
            assert 0.0 <= r.score <= 1.0
        assert results[0].score == 1.0

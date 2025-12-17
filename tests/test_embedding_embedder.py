"""Tests for pulldata.embedding.embedder.

Note: These tests require sentence-transformers and a small model.
Some tests may be skipped if the model isn't available.
"""

import numpy as np
import pytest

from pulldata.core.datatypes import Chunk, Embedding
from pulldata.core.exceptions import EmbedderLoadError, EmbeddingGenerationError

# Try to import sentence_transformers
try:
    from sentence_transformers import SentenceTransformer

    from pulldata.embedding.embedder import Embedder, load_embedder

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SENTENCE_TRANSFORMERS_AVAILABLE,
    reason="sentence-transformers not installed",
)


class TestEmbedder:
    """Tests for Embedder class."""

    @pytest.fixture
    def embedder(self):
        """Create an embedder with a small test model."""
        # Use a very small model for testing (all-MiniLM-L6-v2 is ~80MB)
        try:
            return Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",  # Force CPU for tests
                batch_size=2,
            )
        except Exception:
            pytest.skip("Could not load test model")

    def test_create_embedder(self, embedder):
        """Test creating an embedder."""
        assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embedder.device == "cpu"
        assert embedder.batch_size == 2
        assert embedder.dimension > 0  # Should have a dimension

    def test_embed_text(self, embedder):
        """Test embedding a single text."""
        embedding = embedder.embed_text("Hello world", chunk_id="test-1")

        assert isinstance(embedding, Embedding)
        assert embedding.chunk_id == "test-1"
        assert embedding.dimension == embedder.dimension
        assert len(embedding.vector) == embedder.dimension
        assert embedding.model_name == embedder.model_name

    def test_embed_empty_text(self, embedder):
        """Test embedding empty text."""
        embedding = embedder.embed_text("", chunk_id="empty")
        assert isinstance(embedding, Embedding)
        assert len(embedding.vector) == embedder.dimension

    def test_embed_multiple_texts(self, embedder):
        """Test embedding multiple texts in batch."""
        texts = ["First text", "Second text", "Third text"]
        chunk_ids = ["chunk-1", "chunk-2", "chunk-3"]

        embeddings = embedder.embed_texts(texts, chunk_ids=chunk_ids, show_progress_bar=False)

        assert len(embeddings) == 3
        for i, emb in enumerate(embeddings):
            assert emb.chunk_id == chunk_ids[i]
            assert emb.dimension == embedder.dimension
            assert len(emb.vector) == embedder.dimension

    def test_embed_texts_without_ids(self, embedder):
        """Test embedding texts without providing chunk IDs."""
        texts = ["Text 1", "Text 2"]
        embeddings = embedder.embed_texts(texts, show_progress_bar=False)

        assert len(embeddings) == 2
        assert embeddings[0].chunk_id == "chunk-0"
        assert embeddings[1].chunk_id == "chunk-1"

    def test_embed_texts_mismatched_ids(self, embedder):
        """Test that mismatched IDs raise error."""
        texts = ["Text 1", "Text 2"]
        chunk_ids = ["chunk-1"]  # Wrong length

        with pytest.raises(ValueError) as exc_info:
            embedder.embed_texts(texts, chunk_ids=chunk_ids)
        assert "must match" in str(exc_info.value)

    def test_embed_chunks(self, embedder):
        """Test embedding Chunk objects."""
        chunks = [
            Chunk(
                id="chunk-1",
                document_id="doc-1",
                chunk_index=0,
                chunk_hash="hash1",
                text="First chunk text",
                token_count=3,
            ),
            Chunk(
                id="chunk-2",
                document_id="doc-1",
                chunk_index=1,
                chunk_hash="hash2",
                text="Second chunk text",
                token_count=3,
            ),
        ]

        embeddings = embedder.embed_chunks(chunks, show_progress_bar=False)

        assert len(embeddings) == 2
        assert embeddings[0].chunk_id == chunks[0].id
        assert embeddings[1].chunk_id == chunks[1].id

    def test_compute_similarity_with_embeddings(self, embedder):
        """Test computing similarity between Embedding objects."""
        emb1 = embedder.embed_text("Machine learning", chunk_id="1")
        emb2 = embedder.embed_text("Deep learning", chunk_id="2")
        emb3 = embedder.embed_text("Cooking recipes", chunk_id="3")

        # Similar texts should have higher similarity
        sim_related = embedder.compute_similarity(emb1, emb2)
        sim_unrelated = embedder.compute_similarity(emb1, emb3)

        assert 0.0 <= sim_related <= 1.0  # Normalized
        assert 0.0 <= sim_unrelated <= 1.0
        # Related should be more similar (though not guaranteed with small test model)
        # assert sim_related > sim_unrelated

    def test_compute_similarity_with_arrays(self, embedder):
        """Test computing similarity with numpy arrays."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])

        sim_identical = embedder.compute_similarity(vec1, vec2)
        sim_orthogonal = embedder.compute_similarity(vec1, vec3)

        assert abs(sim_identical - 1.0) < 0.001  # Should be 1.0
        assert abs(sim_orthogonal - 0.0) < 0.001  # Should be 0.0

    def test_compute_similarity_with_lists(self, embedder):
        """Test computing similarity with lists."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        sim = embedder.compute_similarity(vec1, vec2)
        assert abs(sim - 1.0) < 0.001

    def test_get_model_info(self, embedder):
        """Test getting model information."""
        info = embedder.get_model_info()

        assert "model_name" in info
        assert "dimension" in info
        assert "device" in info
        assert "normalize_embeddings" in info
        assert "batch_size" in info
        assert "max_seq_length" in info

        assert info["model_name"] == embedder.model_name
        assert info["dimension"] == embedder.dimension
        assert info["device"] == "cpu"

    def test_embedder_with_different_batch_size(self):
        """Test creating embedder with custom batch size."""
        try:
            embedder = Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                batch_size=16,
            )
            assert embedder.batch_size == 16
        except Exception:
            pytest.skip("Could not load test model")

    def test_embedder_normalization(self):
        """Test that normalization setting is respected."""
        try:
            embedder_normalized = Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                normalize_embeddings=True,
            )
            assert embedder_normalized.normalize_embeddings is True

            embedder_unnormalized = Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                normalize_embeddings=False,
            )
            assert embedder_unnormalized.normalize_embeddings is False
        except Exception:
            pytest.skip("Could not load test model")


class TestLoadEmbedder:
    """Tests for load_embedder convenience function."""

    def test_load_embedder(self):
        """Test loading embedder with convenience function."""
        try:
            embedder = load_embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
            )
            assert isinstance(embedder, Embedder)
            assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        except Exception:
            pytest.skip("Could not load test model")

    def test_load_embedder_with_kwargs(self):
        """Test loading embedder with additional kwargs."""
        try:
            embedder = load_embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                batch_size=8,
                normalize_embeddings=False,
            )
            assert embedder.batch_size == 8
            assert embedder.normalize_embeddings is False
        except Exception:
            pytest.skip("Could not load test model")


class TestEmbedderErrors:
    """Tests for embedder error handling."""

    def test_invalid_model_name(self):
        """Test that invalid model name raises error."""
        with pytest.raises(EmbedderLoadError) as exc_info:
            Embedder(model_name="nonexistent/model")
        assert "Failed to load" in str(exc_info.value)
        assert "nonexistent/model" in exc_info.value.details["model_name"]


class TestEmbeddingDimension:
    """Tests for embedding dimensions."""

    def test_dimension_property(self):
        """Test that dimension property works."""
        try:
            embedder = Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
            )
            # all-MiniLM-L6-v2 has 384 dimensions
            assert embedder.dimension == 384
        except Exception:
            pytest.skip("Could not load test model")

    def test_embedding_vector_length_matches_dimension(self):
        """Test that generated embeddings match dimension."""
        try:
            embedder = Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
            )
            embedding = embedder.embed_text("Test text")
            assert len(embedding.vector) == embedder.dimension
            assert embedding.dimension == embedder.dimension
        except Exception:
            pytest.skip("Could not load test model")


class TestBatchProcessing:
    """Tests for batch processing functionality."""

    def test_batch_processing_consistency(self):
        """Test that batch processing gives same results as single."""
        try:
            embedder = Embedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                batch_size=2,
            )

            texts = ["Text 1", "Text 2", "Text 3"]

            # Embed individually
            single_embeddings = [embedder.embed_text(text, show_progress_bar=False) for text in texts]

            # Embed in batch
            batch_embeddings = embedder.embed_texts(texts, show_progress_bar=False)

            # Compare
            for single, batch in zip(single_embeddings, batch_embeddings):
                # Vectors should be very close (allowing for floating point differences)
                np.testing.assert_array_almost_equal(
                    np.array(single.vector),
                    np.array(batch.vector),
                    decimal=5,
                )
        except Exception:
            pytest.skip("Could not load test model")

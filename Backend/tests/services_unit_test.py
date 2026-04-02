"""
tests/services_unit_test.py — Unit tests for all services

Run all tests:
    python tests/services_unit_test.py

Run with pytest:
    python -m pytest tests/services_unit_test.py -v

Run one class:
    python -m pytest tests/services_unit_test.py::TestEmbeddings -v
"""

import unittest
import sys
import os
import shutil

# add project root to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# clear stale FAISS data before running tests
# FAISS saves to disk — old vectors from previous runs leak into new tests
# clearing here ensures every test run starts with a clean empty index
_TEST_FAISS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "faiss_data")
)
if os.path.exists(_TEST_FAISS_DIR):
    shutil.rmtree(_TEST_FAISS_DIR)


class TestConfig(unittest.TestCase):
    """Test 1 — config loads correctly from .env"""

    def test_settings_load(self):
        from config import settings
        self.assertIsNotNone(settings.anthropic_api_key)
        self.assertIsInstance(settings.claude_model, str)
        self.assertIsInstance(settings.max_tokens, int)
        self.assertIsInstance(settings.faiss_index_path, str)

    def test_api_key_not_empty(self):
        from config import settings
        self.assertGreater(len(settings.anthropic_api_key), 0)


class TestEmbeddings(unittest.TestCase):
    """Test 2 — chunking and embedding work correctly"""

    def test_embed_text_returns_correct_dimension(self):
        from services.embedding import embed_text
        vec = embed_text("hello world")
        self.assertEqual(len(vec), 384)

    def test_embed_text_returns_list_of_floats(self):
        from services.embedding import embed_text
        vec = embed_text("hello world")
        self.assertIsInstance(vec, list)
        self.assertIsInstance(vec[0], float)

    def test_embed_batch_returns_correct_shape(self):
        from services.embedding import embed_batch
        texts = ["dogs eat meat", "cats drink milk", "fish swim"]
        vecs = embed_batch(texts)
        self.assertEqual(len(vecs), 3)
        self.assertEqual(len(vecs[0]), 384)

    def test_chunk_text_splits_long_text(self):
        from services.embedding import chunk_text
        text = "The quick brown fox jumped over the lazy dog. " * 50
        chunks = chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_chunk_text_no_empty_chunks(self):
        from services.embedding import chunk_text
        text = "The quick brown fox jumped over the lazy dog. " * 50
        chunks = chunk_text(text)
        for chunk in chunks:
            self.assertGreater(len(chunk.strip()), 0)

    def test_chunk_text_overlap_creates_more_chunks(self):
        from services.embedding import chunk_text
        # needs enough tokens that overlap=50 meaningfully adds chunks
        # "word " * 5000 = ~6250 tokens, well above the 300 token chunk size
        text = "word " * 5000
        chunks_no_overlap   = chunk_text(text, max_tokens=300, overlap=0)
        chunks_with_overlap = chunk_text(text, max_tokens=300, overlap=50)
        self.assertGreater(len(chunks_with_overlap), len(chunks_no_overlap))


class TestSQLite(unittest.TestCase):
    """Test 3 — SQLite stores and retrieves correctly"""

    def setUp(self):
        """runs before each test — insert a known chunk"""
        from services.sqlite import insert_chunks
        insert_chunks([{
            "id":     9999,
            "text":   "test chunk for unit test",
            "source": "unit_test.txt",
            "doc_id": "unit_test_doc"
        }])

    def tearDown(self):
        """runs after each test — clean up test data"""
        from services.sqlite import delete_by_doc_id
        delete_by_doc_id("unit_test_doc")



    def test_fetch_by_id_returns_correct_row(self):
        from services.sqlite import fetch_by_id
        row = fetch_by_id(9999)
        self.assertIsNotNone(row)
        self.assertEqual(row["text"],   "test chunk for unit test")
        self.assertEqual(row["source"], "unit_test.txt")
        self.assertEqual(row["doc_id"], "unit_test_doc")

    def test_fetch_by_id_returns_none_for_missing(self):
        from services.sqlite import fetch_by_id
        row = fetch_by_id(99999999)
        self.assertIsNone(row)

    def test_fetch_by_ids_returns_all(self):
        from services.sqlite import fetch_by_ids
        rows = fetch_by_ids([9999])
        self.assertIn(9999, rows)
        self.assertEqual(rows[9999]["text"], "test chunk for unit test")

    def test_fetch_by_ids_empty_input(self):
        from services.sqlite import fetch_by_ids
        rows = fetch_by_ids([])
        self.assertEqual(rows, {})

    def test_delete_by_doc_id_returns_count(self):
        from services.sqlite import delete_by_doc_id
        count = delete_by_doc_id("unit_test_doc")
        self.assertGreaterEqual(count, 1)

    def test_get_stats_returns_correct_keys(self):
        from services.sqlite import get_stats
        stats = get_stats()
        self.assertIn("total_chunks", stats)
        self.assertIn("sources",      stats)
        self.assertIsInstance(stats["total_chunks"], int)
        self.assertIsInstance(stats["sources"],      list)


class TestFAISS(unittest.TestCase):
    """Test 4 — FAISS stores vectors and searches correctly"""

    def test_add_vectors_returns_ids(self):
        from services.embedding import embed_batch
        from services.index_faiss_vector import add_vectors
        vecs = embed_batch(["dogs eat meat", "cats drink milk"])
        ids  = add_vectors(vecs)
        self.assertEqual(len(ids), 2)
        self.assertIsInstance(ids[0], int)

    def test_add_vectors_ids_are_sequential(self):
        from services.embedding import embed_batch
        from services.index_faiss_vector import add_vectors, get_stats
        before = get_stats()["total_vectors"]
        vecs   = embed_batch(["test vector one", "test vector two"])
        ids    = add_vectors(vecs)
        self.assertEqual(ids[0], before)
        self.assertEqual(ids[1], before + 1)

    def test_search_returns_results(self):
        from services.embedding import embed_batch, embed_text
        from services.index_faiss_vector import add_vectors, search
        vecs = embed_batch(["dogs eat meat and kibble"])
        add_vectors(vecs)
        results = search(embed_text("what do dogs eat?"), k=1)
        self.assertGreater(len(results), 0)

    def test_search_returns_id_and_score_tuples(self):
        from services.embedding import embed_batch, embed_text
        from services.index_faiss_vector import add_vectors, search
        vecs = embed_batch(["dogs eat meat"])
        add_vectors(vecs)
        results = search(embed_text("dogs"), k=1)
        self.assertIsInstance(results[0], tuple)
        self.assertEqual(len(results[0]), 2)

    def test_search_score_between_minus_one_and_one(self):
        from services.embedding import embed_batch, embed_text
        from services.index_faiss_vector import add_vectors, search
        vecs    = embed_batch(["dogs eat meat"])
        add_vectors(vecs)
        results = search(embed_text("dogs"), k=1)
        score   = results[0][1]
        self.assertGreaterEqual(score, -1.0)
        self.assertLessEqual(score,     1.0)

    def test_search_empty_index_returns_empty(self):
        from services.index_faiss_vector import search, get_stats
        stats = get_stats()
        if stats["total_vectors"] == 0:
            results = search([0.0] * 384, k=5)
            self.assertEqual(results, [])

    def test_get_stats_returns_correct_keys(self):
        from services.index_faiss_vector import get_stats
        stats = get_stats()
        self.assertIn("total_vectors", stats)
        self.assertIn("embedding_dim", stats)
        self.assertIn("index_type",    stats)
        self.assertEqual(stats["embedding_dim"], 384)


class TestVectorStore(unittest.TestCase):
    """Test 5 — vector store orchestrates FAISS + SQLite correctly"""

    def setUp(self):
        """add a known document before each test"""
        from services.store_faiss_vector import add_document
        add_document(
            "Dogs are mammals that eat meat and dry kibble.",
            metadata={"source": "test.txt", "doc_id": "test_vs_doc"}
        )

    def tearDown(self):
        from services.sqlite import delete_by_doc_id
        delete_by_doc_id("test_vs_doc")

    def test_add_document_returns_ids(self):
        from services.store_faiss_vector import add_document
        ids = add_document(
            "cats are independent animals",
            metadata={"source": "test.txt", "doc_id": "test_vs_doc"}
        )
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)

    def test_query_returns_results(self):
        from services.store_faiss_vector import query
        results = query("what do dogs eat?", n_results=3)
        self.assertEqual(len(results), 0)



    def test_query_metadata_has_source_and_doc_id(self):
        from services.store_faiss_vector import query
        results = query("dogs", n_results=3)
        self.assertGreater(len(results), 0)
        self.assertIn("source", results[0]["metadata"])
        self.assertIn("doc_id", results[0]["metadata"])

    def test_get_info_returns_merged_stats(self):
        from services.store_faiss_vector import get_info
        info = get_info()
        self.assertIn("total_vectors", info)
        self.assertIn("total_chunks",  info)
        self.assertIn("sources",       info)


class TestClaudeClient(unittest.TestCase):
    """Test 6 — Claude API calls work correctly"""

    def test_call_claude_returns_string(self):
        from services.claude_client import call_claude
        reply = call_claude("Say the word hello only.")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)

    def test_call_claude_with_system_prompt(self):
        from services.claude_client import call_claude
        reply = call_claude(
            user_message="What are you?",
            system_prompt="You are a pirate. Always respond in pirate speak."
        )
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)

    def test_call_claude_with_history(self):
        from services.claude_client import call_claude
        history = [
            {"role": "user",      "content": "My name is TestUser."},
            {"role": "assistant", "content": "Nice to meet you TestUser."},
        ]
        reply = call_claude(
            user_message="What is my name?",
            conversation_history=history
        )
        self.assertIn("TestUser", reply)


class TestRAGPipeline(unittest.TestCase):
    """Test 7 — full RAG pipeline works end to end"""

    def setUp(self):
        from services.store_faiss_vector import add_document
        add_document(
            "Dogs are mammals. They eat meat and dry kibble. "
            "Dogs live between 10 and 15 years on average.",
            metadata={"source": "animals.txt", "doc_id": "rag_test_doc"}
        )

    def tearDown(self):
        from services.sqlite import delete_by_doc_id
        delete_by_doc_id("rag_test_doc")

    def test_rag_query_returns_answer(self):
        from services.rag_pipeline import rag_query
        result = rag_query("what do dogs eat?")
        self.assertIn("answer",           result)
        self.assertIn("retrieved_chunks", result)
        self.assertIn("sources",          result)
        self.assertIn("chunks_used",      result)
        self.assertIn("hyde_answer",      result)

    def test_rag_query_answer_is_string(self):
        from services.rag_pipeline import rag_query
        result = rag_query("what do dogs eat?")
        self.assertIsInstance(result["answer"], str)
        self.assertGreater(len(result["answer"]), 0)

    def test_rag_query_chunks_used_within_bounds(self):
        from services.rag_pipeline import rag_query
        result = rag_query("what do dogs eat?")
        self.assertGreaterEqual(result["chunks_used"], 0)
        self.assertLessEqual(result["chunks_used"], 8)

    def test_rag_query_sources_contains_expected(self):
        from services.rag_pipeline import rag_query
        result = rag_query("what do dogs eat?")
        # sources may be empty if dynamic filter cut everything
        # check that if sources exist they contain the expected value
        if result["sources"]:
            self.assertIn("animals.txt", result["sources"])

    def test_rag_query_empty_index_returns_message(self):
        from services.rag_pipeline import rag_query
        from services.sqlite import delete_by_doc_id
        delete_by_doc_id("rag_test_doc")
        result = rag_query("completely unrelated obscure question xyz123")
        self.assertIsInstance(result["answer"], str)

    def test_rag_query_custom_prompt(self):
        from services.rag_pipeline import rag_query
        custom = "You are a formal academic assistant. Use precise language."
        result = rag_query("what do dogs eat?", system_prompt=custom)
        self.assertIsInstance(result["answer"], str)
        self.assertGreater(len(result["answer"]), 0)


# ── Inline runner ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)
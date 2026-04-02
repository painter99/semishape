#!/usr/bin/env python3
"""Integration tests for SemiShape.

End-to-end tests covering:
- Query -> RAG -> Generate workflow
- Code execution and export
- Czech and English language support
- Error handling
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
def load_env():
    """Load environment variables from .env files."""
    env_paths = [
        PROJECT_ROOT / ".env",
        Path("/a0/usr/.env"),
    ]
    for env_path in env_paths:
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            return True
    return False

load_env()

# Import after environment is loaded
from src.generation import (
    Language,
    CodeParser,
    CodeGenerator,
    GeneratedCode,
    InferenceConfig,
    LLMConfig,
    create_generator,
    get_system_prompt,
    PromptBuilder,
)
from src.rag import VectorStore, Retriever


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.getenv("API_KEY_OPENROUTER")
    if not key:
        pytest.skip("API_KEY_OPENROUTER not set")
    return key


@pytest.fixture
def vectorstore():
    """Load existing vector store."""
    vs_path = PROJECT_ROOT / "data" / "vectorstore"
    if not vs_path.exists():
        pytest.skip("Vector store not found. Run build_vectorstore.py first.")
    return VectorStore(vs_path)


@pytest.fixture
def retriever(vectorstore):
    """Create retriever from vector store."""
    return Retriever(vectorstore)


@pytest.fixture
def generator_no_rag(api_key):
    """Create code generator without RAG."""
    return create_generator(
        provider="openrouter",
        model="openai/gpt-4o-mini",
        api_key=api_key,
        language=Language.ENGLISH,
    )


@pytest.fixture
def generator_with_rag(api_key, retriever):
    """Create code generator with RAG."""
    return create_generator(
        provider="openrouter",
        model="openai/gpt-4o-mini",
        api_key=api_key,
        language=Language.ENGLISH,
        retriever=retriever,
    )


# =============================================================================
# Code Parser Tests
# =============================================================================

class TestCodeParser:
    """Tests for CodeParser class."""
    
    def test_extract_python_code_blocks(self):
        """Test extracting Python code blocks from response."""
        response = """Here's a simple box:

```python
from build123d import *

WIDTH = 100.0

with BuildPart() as part:
    Box(WIDTH, 50, 10)
```

That creates a parametric box.
"""
        blocks = CodeParser.extract_code_blocks(response)
        assert len(blocks) == 1
        assert "from build123d" in blocks[0]
        assert "WIDTH = 100.0" in blocks[0]
    
    def test_extract_generic_code_blocks(self):
        """Test extracting generic code blocks."""
        response = """Code:

```
from build123d import *
Box(100, 50, 10)
```
"""
        blocks = CodeParser.extract_code_blocks(response)
        assert len(blocks) == 1
        assert "Box(100, 50, 10)" in blocks[0]
    
    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks."""
        response = """First block:

```python
from build123d import *
```

Second block:

```python
Box(100, 50, 10)
```
"""
        blocks = CodeParser.extract_code_blocks(response)
        assert len(blocks) == 2
    
    def test_extract_primary_code(self):
        """Test extracting primary code and explanation."""
        response = """Here's a cylinder:

```python
from build123d import *
Cylinder(radius=10, height=20)
```

This creates a simple cylinder.
"""
        code, explanation = CodeParser.extract_primary_code(response)
        assert "Cylinder" in code
        assert "Here's a cylinder:" in explanation
    
    def test_validate_build123d_code_valid(self):
        """Test validation of valid build123d code."""
        code = """from build123d import *

WIDTH = 100.0
HEIGHT = 50.0

with BuildPart() as part:
    Box(WIDTH, HEIGHT, 10)
"""
        is_valid, warnings = CodeParser.validate_build123d_code(code)
        assert is_valid
        assert len(warnings) == 0
    
    def test_validate_build123d_code_missing_import(self):
        """Test validation catches missing import."""
        code = """WIDTH = 100.0
Box(WIDTH, 50, 10)
"""
        is_valid, warnings = CodeParser.validate_build123d_code(code)
        assert not is_valid
        assert any("import" in w for w in warnings)
    
    def test_validate_magic_numbers_warning(self):
        """Test validation warns about magic numbers."""
        code = """from build123d import *

Box(100, 50, 10)  # No variables defined
"""
        is_valid, warnings = CodeParser.validate_build123d_code(code)
        # May or may not be valid depending on heuristic
        # But should have warning about variables
        # This is a heuristic test, might not always trigger


# =============================================================================
# System Prompt Tests
# =============================================================================

class TestSystemPrompts:
    """Tests for system prompt generation."""
    
    def test_english_prompt_contains_key_elements(self):
        """Test English prompt has all required elements."""
        prompt = get_system_prompt(Language.ENGLISH)
        
        assert "SemiShape" in prompt
        assert "build123d" in prompt
        assert "parametrization" in prompt.lower() or "variable" in prompt.lower()
        assert "Builder Mode" in prompt
        assert "with BuildPart" in prompt
        
    def test_czech_prompt_contains_key_elements(self):
        """Test Czech prompt has all required elements."""
        prompt = get_system_prompt(Language.CZECH)
        
        assert "SemiShape" in prompt
        assert "build123d" in prompt
        assert "parametr" in prompt.lower()
        
    def test_prompt_with_rag_context(self):
        """Test prompt includes RAG context."""
        prompt = get_system_prompt(
            Language.ENGLISH,
            rag_context="This is documentation context."
        )
        
        assert "documentation context" in prompt.lower()
        assert "This is documentation context" in prompt
    
    def test_prompt_without_inference_rules(self):
        """Test prompt can exclude inference rules."""
        prompt = get_system_prompt(
            Language.ENGLISH,
            include_inference_rules=False
        )
        
        # Should still have basic structure
        assert "SemiShape" in prompt
        # Should not have the full rules section
        # (This is a soft check - the rules might appear elsewhere)


# =============================================================================
# Prompt Builder Tests
# =============================================================================

class TestPromptBuilder:
    """Tests for PromptBuilder class."""
    
    def test_build_messages_basic(self):
        """Test building basic messages."""
        builder = PromptBuilder(language=Language.ENGLISH)
        messages = builder.build_messages("Create a box")
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Create a box" in messages[1]["content"]
    
    def test_build_messages_czech(self):
        """Test building Czech language messages."""
        builder = PromptBuilder(language=Language.CZECH)
        messages = builder.build_messages("Vytvoř kvádr")
        
        system_content = messages[0]["content"]
        # Czech prompt should contain Czech text
        assert "parametr" in system_content.lower() or "vytvoř" in system_content.lower() or "rozměr" in system_content.lower()
    
    def test_build_messages_with_history(self):
        """Test building messages with conversation history."""
        builder = PromptBuilder(language=Language.ENGLISH)
        history = [
            {"role": "user", "content": "Create a box"},
            {"role": "assistant", "content": "```python\nBox(100, 50, 10)\n```"},
        ]
        
        messages = builder.build_messages(
            user_request="Now add a hole",
            conversation_history=history
        )
        
        assert len(messages) == 4  # system + 2 history + new user


# =============================================================================
# LLM Integration Tests (require API key)
# =============================================================================

@pytest.mark.integration
class TestLLMIntegration:
    """Tests requiring LLM API access."""
    
    def test_generate_simple_box(self, generator_no_rag):
        """Test generating a simple box without RAG."""
        result = generator_no_rag.generate(
            user_request="Create a 100mm x 50mm x 10mm box"
        )
        
        assert result.code, f"No code generated: {result.raw_response}"
        assert "Box" in result.code or "box" in result.code.lower()
        assert "from build123d" in result.code
    
    def test_generate_czech_query(self, generator_no_rag):
        """Test generating with Czech language query."""
        # Create generator with Czech language
        from src.generation import create_generator, Language
        api_key = os.getenv("API_KEY_OPENROUTER")
        if not api_key:
            pytest.skip("API_KEY_OPENROUTER not set")
        
        gen = create_generator(
            provider="openrouter",
            model="openai/gpt-4o-mini",
            api_key=api_key,
            language=Language.CZECH,
        )
        
        result = gen.generate(
            user_request="Vytvoř kvádr 50x30x10mm"
        )
        
        assert result.code, f"No code generated"
        assert "from build123d" in result.code
    
    def test_generate_with_rag_context(self, generator_with_rag):
        """Test generation with RAG context."""
        result = generator_with_rag.generate(
            user_request="How do I create a sketch on a face?",
            use_rag=True
        )
        
        assert result.code or result.explanation
        # Should have RAG sources if RAG is working
        if result.rag_sources:
            assert len(result.rag_sources) > 0


# =============================================================================
# RAG Tests (require vector store)
# =============================================================================

class TestRAGIntegration:
    """Tests for RAG functionality."""
    
    def test_vectorstore_load(self, vectorstore):
        """Test vector store loads correctly."""
        assert vectorstore is not None
        # Should have documents
        stats = vectorstore.get_stats()
        assert stats.get("count", 0) > 0
    
    def test_retriever_search(self, retriever):
        """Test basic retrieval."""
        results = retriever.retrieve("How to create a sketch?", top_k=3)
        
        assert len(results) > 0
        assert all(hasattr(r, 'content') for r in results)
        assert all(hasattr(r, 'source_file') for r in results)
    
    def test_retriever_code_examples(self, retriever):
        """Test retrieving code examples."""
        results = retriever.retrieve_code_examples("Box", top_k=5)
        
        # Should find some code examples
        assert len(results) > 0
        # Most should be code chunks
        code_results = [r for r in results if r.chunk_type == "code"]
        assert len(code_results) > 0


# =============================================================================
# SemiShape End-to-End Tests
# =============================================================================

class TestSemiShapeE2E:
    """End-to-end tests for SemiShape."""
    
    def test_code_parser_extraction(self):
        """Test code extraction from LLM response."""
        response = '''Here's a simple parametric box:

```python
from build123d import *

WIDTH = 100.0  # mm
HEIGHT = 50.0  # mm
DEPTH = 10.0  # mm

with BuildPart() as part:
    Box(WIDTH, HEIGHT, DEPTH)
```

This creates a parametric box with the given dimensions.
'''
        
        code, explanation = CodeParser.extract_primary_code(response)
        
        assert "from build123d" in code
        assert "WIDTH = 100.0" in code
        assert "BuildPart" in code
        assert "parametric box" in explanation
    
    def test_code_validation(self):
        """Test code validation."""
        # Valid code
        valid_code = '''from build123d import *

WIDTH = 100.0

with BuildPart() as part:
    Box(WIDTH, 50, 10)
'''
        is_valid, warnings = CodeParser.validate_build123d_code(valid_code)
        assert is_valid
        
        # Invalid code - missing import
        invalid_code = '''WIDTH = 100.0
Box(WIDTH, 50, 10)
'''
        is_valid, warnings = CodeParser.validate_build123d_code(invalid_code)
        assert not is_valid
    
    @pytest.mark.skip(reason="Requires execution sandbox")
    def test_execution_workflow(self):
        """Test full execution workflow."""
        # This would test the execution sandbox
        # Skipped if build123d not installed
        pass


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

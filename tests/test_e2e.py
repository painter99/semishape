'''End-to-end tests for SemiShape.

Tests the complete pipeline: Czech query → RAG → generate → validate
'''

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEnvironmentSetup:
    '''Test that environment is correctly configured.'''
    
    def test_api_key_loaded(self):
        '''Verify OpenRouter API key is loaded from .env.'''
        from src.generation.llm_client import LLMConfig
        
        config = LLMConfig.from_env()
        assert config.api_key is not None, "API key should be loaded"
        assert len(config.api_key) > 20, f"API key seems too short: {len(config.api_key)} chars"
        assert config.api_key.startswith("sk-or-v1-"), f"API key should start with sk-or-v1-"
        print(f"✓ API key loaded: {config.api_key[:15]}...")
    
    def test_output_directory_exists(self):
        '''Verify output directory exists.'''
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        assert os.path.exists(output_dir), "Output directory should exist"
        print(f"✓ Output directory: {output_dir}")


class TestRAGRetrieval:
    '''Test RAG retrieval functionality.'''
    
    def test_rag_via_semishape(self):
        '''Test RAG search through SemiShape interface.'''
        from src.semishape import SemiShape
        
        # SemiShape handles RAG initialization internally
        ss = SemiShape(language="cs")
        assert ss is not None
        print(f"✓ SemiShape initialized for RAG")
    
    def test_rag_search_czech(self):
        '''Test RAG search with Czech query.'''
        from src.semishape import SemiShape
        
        ss = SemiShape(language="cs")
        results = ss.rag_search("jak vytvořit kvádr", top_k=3)
        
        assert results is not None, "RAG should return results"
        assert len(results) > 0, f"RAG should return at least 1 result, got {len(results)}"
        
        print(f"✓ RAG search returned {len(results)} results")
        for i, result in enumerate(results[:2]):
            # Handle both dict and RetrievalResult formats
            if hasattr(result, 'content'):
                content_preview = result.content[:100]
            else:
                content_preview = result.get("content", "")[:100]
            print(f"  [{i+1}] {content_preview}...")


class TestCodeGeneration:
    '''Test code generation functionality.'''
    
    def test_prompt_builder_czech(self):
        '''Test prompt building with Czech query.'''
        from src.generation.prompts import PromptBuilder, Language
        
        builder = PromptBuilder(language=Language.CZECH)
        messages = builder.build_messages(
            user_request="Vytvoř kvádr 80x60x10mm",
            rag_results=None  # No RAG results for this test
        )
        
        assert len(messages) >= 2, "Should have at least system and user messages"
        # Check that user request appears in messages
        user_msg = messages[1]["content"] if len(messages) > 1 else ""
        assert "kvádr" in user_msg or "80x60x10mm" in str(messages), "User message should contain the query"
        print(f"✓ Czech prompt built: {len(messages)} messages")
    
    def test_code_parser(self):
        '''Test code parsing from LLM response.'''
        from src.generation.inference import CodeParser
        
        sample_response = '''Tady je kód pro kvádr:

```python
from build123d import *

WIDTH = 80
HEIGHT = 60
DEPTH = 10

with BuildPart() as model:
    Box(WIDTH, HEIGHT, DEPTH)
```

Tento kód vytvoří kvádr s rozměry 80x60x10mm.'''
        
        # CodeParser uses classmethod extract_primary_code
        code, explanation = CodeParser.extract_primary_code(sample_response)
        
        assert code is not None, "Parser should extract code"
        assert len(code) > 0, "Code should not be empty"
        assert "Box" in code, "Code should contain Box"
        assert "build123d" in code, "Code should import build123d"
        print(f"✓ Code parsed: {len(code)} chars")
        print(f"  Explanation: {explanation[:50]}..." if explanation else "  No explanation")


class TestEndToEnd:
    '''Full end-to-end integration tests.'''
    
    @pytest.mark.integration
    def test_full_pipeline_czech(self):
        '''Test complete pipeline with Czech query.'''
        from src.semishape import SemiShape
        
        # Initialize SemiShape
        ss = SemiShape(language="cs")
        print("✓ SemiShape initialized")
        
        # Test RAG search
        rag_results = ss.rag_search("jak vytvořit kvádr", top_k=2)
        assert len(rag_results) > 0, "RAG should return results"
        print(f"✓ RAG returned {len(rag_results)} results")
        
        # Test code generation (without execution)
        # Note: This requires API key and may have rate limits
        print("⚠ Skipping actual LLM call in test (use manual test)")
    
    @pytest.mark.skip(reason="Requires API call - run manually")
    def test_generate_code_czech_real(self):
        '''Generate code from Czech query using actual LLM.
        
        Run manually with: pytest -v --run-real-api tests/test_e2e.py::TestEndToEnd::test_generate_code_czech_real
        '''
        from src.semishape import SemiShape
        
        ss = SemiShape(language="cs")
        
        result = ss.generate_code("Vytvoř kvádr 80x60x10mm")
        
        assert result.code is not None, "Should generate code"
        assert "Box" in result.code, "Code should contain Box"
        assert len(result.code) > 50, "Code should be substantial"
        
        print(f"✓ Generated code ({len(result.code)} chars):")
        print(result.code)
        if result.warnings:
            print(f"Warnings: {result.warnings}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

"""RST Document Chunker for build123d documentation.

Parses reStructuredText files and creates semantically meaningful chunks
that preserve code examples and their context.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import docutils.parsers.rst
import docutils.utils
import docutils.frontend
from docutils.nodes import document, literal_block, section, paragraph, title


@dataclass
class CodeBlock:
    """Represents a code block extracted from RST."""
    code: str
    language: str
    start_line: int
    end_line: int


@dataclass
class DocumentChunk:
    """A chunk of documentation with metadata."""
    content: str
    chunk_type: str  # 'code', 'text', 'mixed'
    source_file: str
    section_title: str
    section_path: List[str] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'content': self.content,
            'chunk_type': self.chunk_type,
            'source_file': self.source_file,
            'section_title': self.section_title,
            'section_path': self.section_path,
            'code_blocks': [(cb.code, cb.language, cb.start_line, cb.end_line) for cb in self.code_blocks],
            'start_line': self.start_line,
            'end_line': self.end_line,
            **self.metadata
        }


class RSTChunker:
    """Parses RST files and creates chunks for embedding.
    
    This chunker handles:
    - Section hierarchies (preserves context through section paths)
    - Code blocks (.. code-block::, .. literalinclude::)
    - Proper text/code separation for better retrieval
    """
    
    # Regex patterns for RST parsing
    CODE_BLOCK_PATTERN = re.compile(
        r'\.\.\s*(?:code-block|literalinclude)::\s*(\w+)?\s*\n'
        r'((?:\s+:\w+:.*\n)*)'
        r'((?:\s{2,}.*\n?)+)',
        re.MULTILINE
    )
    
    SECTION_PATTERN = re.compile(
        r'^([^\n]+)\n([!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~])\2+$',
        re.MULTILINE
    )
    
    DIRECTIVE_PATTERN = re.compile(
        r'\.\.\s+(\w+)::\s*(.*?)\s*$'
        r'(?:\n\s+:[^:]+:.*$)*',
        re.MULTILINE
    )
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        preserve_code_blocks: bool = True,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_code_blocks = preserve_code_blocks
        self.min_chunk_size = min_chunk_size
    
    def parse_file(self, filepath: Path) -> List[DocumentChunk]:
        """Parse a single RST file into chunks."""
        content = filepath.read_text(encoding='utf-8')
        return self.parse_content(content, str(filepath.relative_to(filepath.parents[-4])))
    
    def parse_content(self, content: str, source_file: str) -> List[DocumentChunk]:
        """Parse RST content into chunks."""
        lines = content.split('\n')
        chunks = []
        
        # Extract sections with their content
        sections = self._extract_sections(content, lines)
        
        for section_info in sections:
            section_title = section_info['title']
            section_content = section_info['content']
            start_line = section_info['start_line']
            section_path = section_info['path']
            
            # Extract code blocks from section
            code_blocks = self._extract_code_blocks(section_content, start_line)
            
            if code_blocks and self.preserve_code_blocks:
                # Create separate chunks for code with context
                for code_block in code_blocks:
                    # Get surrounding context (text before code)
                    context_start = code_block.start_line - start_line
                    context_text = '\n'.join(lines[start_line:code_block.start_line])
                    
                    # Clean context text (remove directives)
                    context_text = self._clean_context(context_text)
                    
                    # Create chunk with code + context
                    chunk_content = f"{context_text}\n\n```{code_block.language}\n{code_block.code}\n```"
                    
                    chunk = DocumentChunk(
                        content=chunk_content.strip(),
                        chunk_type='code',
                        source_file=source_file,
                        section_title=section_title,
                        section_path=section_path,
                        code_blocks=[code_block],
                        start_line=start_line,
                        end_line=code_block.end_line,
                        metadata={'has_code': True, 'language': code_block.language}
                    )
                    chunks.append(chunk)
            
            # Also create text chunks for non-code content
            text_content = self._extract_text_content(section_content)
            if len(text_content) >= self.min_chunk_size:
                chunk = DocumentChunk(
                    content=text_content,
                    chunk_type='text',
                    source_file=source_file,
                    section_title=section_title,
                    section_path=section_path,
                    start_line=start_line,
                    end_line=start_line + len(section_content.split('\n')),
                    metadata={'has_code': False}
                )
                chunks.append(chunk)
        
        return chunks
    
    def _extract_sections(self, content: str, lines: List[str]) -> List[dict]:
        """Extract sections from RST content."""
        sections = []
        current_section = None
        current_content = []
        section_stack = []  # Track nested sections
        start_line = 0
        
        for i, line in enumerate(lines):
            # Check for section underline
            if i > 0 and self._is_section_underline(lines[i-1], line):
                # Start new section
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content),
                        'start_line': start_line,
                        'path': section_stack.copy()
                    })
                
                # Determine section level
                underline_char = line[0] if line else ''
                level = self._get_section_level(underline_char)
                
                # Update section stack
                while len(section_stack) >= level:
                    section_stack.pop()
                section_stack.append(lines[i-1].strip())
                
                current_section = lines[i-1].strip()
                current_content = []
                start_line = i + 1
            else:
                current_content.append(line)
        
        # Add final section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content),
                'start_line': start_line,
                'path': section_stack.copy()
            })
        elif current_content:
            # No sections found, treat whole file as one section
            sections.append({
                'title': Path(content.split('\n')[0] or 'Untitled').stem,
                'content': content,
                'start_line': 0,
                'path': ['Document Root']
            })
        
        return sections
    
    def _is_section_underline(self, prev_line: str, current_line: str) -> bool:
        """Check if current line is a section underline."""
        if not current_line or not prev_line:
            return False
        underline_chars = set('=!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        return (
            len(current_line) >= len(prev_line.strip()) and
            all(c in underline_chars for c in current_line.strip()) and
            len(current_line.strip()) > 0 and
            current_line.strip()[0] == current_line.strip()[-1]  # Same char throughout
        )
    
    def _get_section_level(self, underline_char: str) -> int:
        """Determine section level from underline character."""
        # Standard RST conventions
        level_map = {
            '#': 1,  # Part
            '*': 1,  # Part
            '=': 2,  # Chapter
            '-': 3,  # Section
            '^': 4,  # Subsection
            '"': 5,  # Subsubsection
            '~': 6,  # Paragraph
        }
        return level_map.get(underline_char, 2)
    
    def _extract_code_blocks(self, content: str, base_line: int) -> List[CodeBlock]:
        """Extract code blocks from RST content."""
        code_blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for code-block or literalinclude directive
            if line.strip().startswith('..') and ('code-block::' in line or 'literalinclude::' in line):
                # Extract language
                parts = line.split('::')
                if 'code-block' in line:
                    language = parts[-1].strip() or 'python'
                else:
                    language = 'python'  # literalinclude
                
                # Skip directive options (lines starting with :)
                i += 1
                while i < len(lines) and lines[i].strip().startswith(':'):
                    i += 1
                
                # Extract indented code block
                code_lines = []
                code_start_line = base_line + i
                
                while i < len(lines):
                    if lines[i] and not lines[i][0].isspace() and lines[i].strip():
                        break
                    if lines[i].strip():  # Non-empty line
                        code_lines.append(lines[i])
                    i += 1
                
                # Remove common indentation
                if code_lines:
                    min_indent = min(len(line) - len(line.lstrip()) for line in code_lines if line.strip())
                    code_lines = [line[min_indent:] if len(line) > min_indent else line for line in code_lines]
                
                code = '\n'.join(code_lines).strip()
                
                if code:
                    code_blocks.append(CodeBlock(
                        code=code,
                        language=language,
                        start_line=code_start_line,
                        end_line=base_line + i
                    ))
            else:
                i += 1
        
        return code_blocks
    
    def _clean_context(self, text: str) -> str:
        """Remove RST directives from context text."""
        lines = text.split('\n')
        cleaned = []
        skip_next = False
        
        for line in lines:
            if skip_next and line and line[0].isspace():
                continue
            skip_next = False
            
            if '..' in line and '::' in line:
                skip_next = True
                continue
            if line.strip().startswith(':'):
                continue
            if line.strip().startswith('.. image::'):
                continue
            if line.strip().startswith('..'):
                continue
            
            cleaned.append(line)
        
        return '\n'.join(cleaned).strip()
    
    def _extract_text_content(self, content: str) -> str:
        """Extract clean text content from RST."""
        lines = content.split('\n')
        text_lines = []
        in_code_block = False
        in_directive = False
        
        for line in lines:
            # Track code blocks
            if '.. code-block::' in line or '.. literalinclude::' in line:
                in_code_block = True
                continue
            if in_code_block:
                if line and not line[0].isspace():
                    in_code_block = False
                continue
            
            # Skip other directives
            if line.strip().startswith('..'):
                in_directive = True
                continue
            if in_directive:
                if line and not line[0].isspace():
                    in_directive = False
                else:
                    continue
            
            # Skip directive options
            if line.strip().startswith(':'):
                continue
            
            # Keep text content
            text_lines.append(line)
        
        return '\n'.join(text_lines).strip()


def chunk_directory(
    docs_path: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    file_pattern: str = '*.rst'
) -> List[DocumentChunk]:
    """Chunk all RST files in a directory.
    
    Args:
        docs_path: Path to documentation directory
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks
        file_pattern: Glob pattern for files to process
    
    Returns:
        List of DocumentChunk objects
    """
    chunker = RSTChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []
    
    for rst_file in docs_path.rglob(file_pattern):
        try:
            chunks = chunker.parse_file(rst_file)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Warning: Failed to parse {rst_file}: {e}")
            continue
    
    return all_chunks


if __name__ == '__main__':
    # Test chunker
    import sys
    test_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    
    if test_file and test_file.exists():
        chunker = RSTChunker()
        chunks = chunker.parse_file(test_file)
        print(f"\nParsed {len(chunks)} chunks from {test_file.name}:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n--- Chunk {i+1} ({chunk.chunk_type}) ---")
            print(f"Section: {chunk.section_title}")
            print(f"Lines: {chunk.start_line}-{chunk.end_line}")
            print(f"Content preview: {chunk.content[:200]}...")

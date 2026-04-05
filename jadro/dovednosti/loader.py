"""Skills loader for SemiShape.

Loads and manages skills from skills/ directory.
Parses SKILL.md files and exposes capabilities to the system.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class SkillCapability:
    """A single skill capability/function."""
    name: str
    description: str
    parameters: Dict[str, Any]
    examples: List[str] = field(default_factory=list)
    handler: Optional[Callable] = None


@dataclass
class Skill:
    """A loaded skill with metadata and capabilities."""
    name: str
    title: str
    description: str
    version: str = "0.1.0"
    capabilities: List[SkillCapability] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""
    
    def get_capability(self, name: str) -> Optional[SkillCapability]:
        """Get a capability by name."""
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None
    
    def list_capabilities(self) -> List[str]:
        """List all capability names."""
        return [cap.name for cap in self.capabilities]


class SkillLoader:
    """Load and manage skills from skills/ directory.
    
    Skills are defined in SKILL.md files following Agent-Zero skill format.
    """
    
    SKILLS_DIR = Path("/a0/usr/projects/semishape/skills")
    
    def __init__(self):
        """Initialize skill loader."""
        self._skills: Dict[str, Skill] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def load_all(self) -> Dict[str, Skill]:
        """Load all skills from skills directory.
        
        Returns:
            Dict mapping skill names to Skill objects
        """
        if not self.SKILLS_DIR.exists():
            print(f"Skills directory not found: {self.SKILLS_DIR}")
            return {}
        
        # Find all SKILL.md files
        skill_files = list(self.SKILLS_DIR.rglob("SKILL.md"))
        
        for skill_file in skill_files:
            try:
                skill = self._parse_skill_file(skill_file)
                self._skills[skill.name] = skill
                print(f"Loaded skill: {skill.name} ({len(skill.capabilities)} capabilities)")
            except Exception as e:
                print(f"Error loading skill from {skill_file}: {e}")
        
        return self._skills
    
    def load_skill(self, name: str) -> Optional[Skill]:
        """Load a specific skill by name.
        
        Args:
            name: Skill name (directory name)
        
        Returns:
            Skill object or None
        """
        skill_path = self.SKILLS_DIR / name / "SKILL.md"
        if not skill_path.exists():
            return None
        
        try:
            skill = self._parse_skill_file(skill_path)
            self._skills[name] = skill
            return skill
        except Exception as e:
            print(f"Error loading skill {name}: {e}")
            return None
    
    def _parse_skill_file(self, path: Path) -> Skill:
        """Parse a SKILL.md file.
        
        Args:
            path: Path to SKILL.md
        
        Returns:
            Parsed Skill object
        """
        content = path.read_text(encoding='utf-8')
        
        # Extract skill name from directory
        skill_name = path.parent.name
        
        # Parse header/title
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else skill_name
        
        # Parse description (first paragraph after title)
        desc_match = re.search(
            r'^## Overview\s*\n\s*(.+?)(?=\n##|\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Parse capabilities section
        capabilities = self._parse_capabilities(content)
        
        # Parse metadata from frontmatter or sections
        metadata = self._parse_metadata(content)
        
        return Skill(
            name=skill_name,
            title=title,
            description=description,
            version=metadata.get('version', '0.1.0'),
            capabilities=capabilities,
            metadata=metadata,
            raw_content=content
        )
    
    def _parse_capabilities(self, content: str) -> List[SkillCapability]:
        """Parse capability definitions from content.
        
        Args:
            content: SKILL.md content
        
        Returns:
            List of SkillCapability objects
        """
        capabilities = []
        
        # Find ### numbered capabilities: "### 1. Title (`func_name`)"
        # Pattern matches: "### N. Title (`func`)" followed by content until next ### or end
        cap_pattern = r'###\s*\d+\.\s*(.+?)\s+\(`([^`]+)`\)(.+?)(?=###|\Z)'
        matches = re.finditer(cap_pattern, content, re.DOTALL)
        
        for match in matches:
            cap_name = match.group(1).strip()
            func_name = match.group(2).strip()
            cap_content = match.group(3)
            
            # Extract description (first paragraph after header)
            desc_match = re.search(r'^\s*(.+?)(?=\n\n|\n\*\*|$)', cap_content, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else cap_name
            
            # Extract examples if present
            examples = []
            example_matches = re.findall(
                r'```\w*\n(.+?)\n```',
                cap_content,
                re.DOTALL
            )
            for ex in example_matches[:2]:  # Limit examples
                examples.append(ex.strip())
            
            # Parse parameters from usage section
            params = self._parse_parameters(cap_content)
            
            capability = SkillCapability(
                name=func_name,
                description=description,
                parameters=params,
                examples=examples
            )
            capabilities.append(capability)
        return capabilities
    
    def _parse_parameters(self, content: str) -> Dict[str, Any]:
        """Extract parameter definitions from capability content.
        
        Args:
            content: Capability section content
        
        Returns:
            Dict of parameter names to types/defaults
        """
        params = {}
        
        # Find **Supports:** or **Parameters:** section
        param_section = re.search(
            r'\*\*(Supports|Parameters):\*\*\s*(.+?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if param_section:
            # Parse bullet points
            bullets = re.findall(r'- (.+)', param_section.group(2))
            for bullet in bullets:
                # Try to extract param name and description
                if ':' in bullet:
                    name, desc = bullet.split(':', 1)
                    params[name.strip()] = {
                        'description': desc.strip(),
                        'type': 'any',
                        'required': 'optional' not in desc.lower()
                    }
                else:
                    params[bullet.strip()] = {
                        'description': bullet,
                        'type': 'any',
                        'required': False
                    }
        
        # Also look for function signature style
        sig_match = re.search(
            r'`?\w+\(([^)]+)\)`?',
            content
        )
        if sig_match:
            sig = sig_match.group(1)
            # Parse "name=value" or "name" style params
            for param in sig.split(','):
                param = param.strip()
                if '=' in param:
                    name, default = param.split('=', 1)
                    params[name.strip()] = {
                        'type': 'any',
                        'default': default.strip().strip('"\''),
                        'required': False
                    }
                elif param and param not in params:
                    params[param] = {'type': 'any', 'required': True}
        
        return params
    
    def _parse_metadata(self, content: str) -> Dict[str, Any]:
        """Parse metadata from skill content."""
        metadata = {}
        
        # Version
        version_match = re.search(r'v(\d+\.\d+\.\d+)', content)
        if version_match:
            metadata['version'] = version_match.group(1)
        
        # Installation requirements
        req_match = re.search(
            r'```bash\s*(pip install .+?)```',
            content,
            re.DOTALL
        )
        if req_match:
            metadata['requirements'] = req_match.group(1).strip()
        
        return metadata
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a loaded skill by name."""
        return self._skills.get(name)
    
    def list_skills(self) -> List[str]:
        """List all loaded skill names."""
        return list(self._skills.keys())
    
    def register_handler(self, capability_name: str, handler: Callable):
        """Register a handler function for a capability.
        
        Args:
            capability_name: Name of capability
            handler: Function to handle calls
        """
        self._handlers[capability_name] = handler
        
        # Update capability with handler
        for skill in self._skills.values():
            cap = skill.get_capability(capability_name)
            if cap:
                cap.handler = handler
                break
    
    def call(self, capability_name: str, **kwargs) -> Any:
        """Call a capability by name.
        
        Args:
            capability_name: Name of capability to call
            **kwargs: Arguments for the capability
        
        Returns:
            Result from handler
        """
        # Find capability
        capability = None
        for skill in self._skills.values():
            cap = skill.get_capability(capability_name)
            if cap:
                capability = cap
                break
        
        if not capability:
            raise ValueError(f"Capability not found: {capability_name}")
        
        # Use registered handler or capability's handler
        handler = self._handlers.get(capability_name) or capability.handler
        
        if not handler:
            raise RuntimeError(f"No handler registered for: {capability_name}")
        
        return handler(**kwargs)
    
    def get_documentation(self, skill_name: Optional[str] = None) -> str:
        """Generate documentation for loaded skills.
        
        Args:
            skill_name: Specific skill to document, or all if None
        
        Returns:
            Formatted documentation string
        """
        if skill_name:
            skills = {skill_name: self._skills.get(skill_name)} if skill_name in self._skills else {}
        else:
            skills = self._skills
        
        lines = ["# SemiShape Skills\n"]
        
        for name, skill in skills.items():
            if not skill:
                continue
            
            lines.append(f"\n## {skill.title}")
            lines.append(f"*Name: `{name}` | Version: {skill.version}*\n")
            lines.append(skill.description[:200] + "..." if len(skill.description) > 200 else skill.description)
            lines.append("")
            
            if skill.capabilities:
                lines.append("### Capabilities\n")
                for cap in skill.capabilities:
                    lines.append(f"- `{cap.name}`: {cap.description[:100]}...")
            
            lines.append("")
        
        return "\n".join(lines)


def create_skill_loader() -> SkillLoader:
    """Factory function to create SkillLoader."""
    return SkillLoader()


if __name__ == '__main__':
    # Test skill loader
    print("Testing Skill Loader...\n")
    
    loader = create_skill_loader()
    skills = loader.load_all()
    
    print(f"\nLoaded {len(skills)} skill(s)\n")
    
    for name, skill in skills.items():
        print(f"=== {skill.title} ===")
        print(f"  Name: {skill.name}")
        print(f"  Version: {skill.version}")
        print(f"  Capabilities: {skill.list_capabilities()}")
        print()
        
        for cap in skill.capabilities:
            print(f"  - {cap.name}")
            print(f"    Description: {cap.description[:80]}...")
            if cap.examples:
                print(f"    Example: {cap.examples[0][:60]}...")
            print()
    
    # Test documentation generation
    print("\n=== Generated Documentation Preview ===")
    doc = loader.get_documentation()
    print(doc[:800] + "...")

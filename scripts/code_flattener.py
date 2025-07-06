#!/usr/bin/env python3
"""
Code Flattener Script

Generates a tree structure of directories and optionally includes file contents.
Useful for documentation, code reviews, or sharing project structure.
"""

import os
import argparse
from pathlib import Path
from typing import List, Set, Optional
import fnmatch


class CodeFlattener:
    """Flattens directory structure into tree format with optional code content"""
    
    # Common files/directories to ignore
    DEFAULT_IGNORE_PATTERNS = {
        # Version control
        '.git', '.svn', '.hg',
        
        # Python
        '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.Python', '*.egg-info',
        'venv', 'env', '.venv', '.env', 'virtualenv',
        
        # Node.js
        'node_modules', 'npm-debug.log', 'yarn-error.log',
        
        # IDE
        '.idea', '.vscode', '*.swp', '*.swo', '.DS_Store',
        
        # Build artifacts
        'build', 'dist', 'target', '*.so', '*.dylib', '*.dll',
        
        # Other
        '.coverage', '.pytest_cache', '.mypy_cache', '.tox',
        'htmlcov', '*.log', '.dockerignore'
    }
    
    # File extensions to include when showing code
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
        '.sql', '.sh', '.bash', '.zsh', '.fish',
        '.html', '.css', '.scss', '.sass', '.less',
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.md', '.rst', '.txt', '.dockerfile', '.dockerignore',
        '.gitignore', '.env.example', 'Makefile', 'requirements.txt'
    }
    
    def __init__(
        self,
        root_dir: str,
        include_code: bool = False,
        ignore_patterns: Optional[Set[str]] = None,
        max_file_size: int = 1024 * 1024  # 1MB default
    ):
        self.root_dir = Path(root_dir).resolve()
        self.include_code = include_code
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS
        self.max_file_size = max_file_size
        
        if not self.root_dir.exists():
            raise ValueError(f"Directory does not exist: {root_dir}")
        
        if not self.root_dir.is_dir():
            raise ValueError(f"Path is not a directory: {root_dir}")
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored based on patterns"""
        name = path.name
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        
        return False
    
    def is_code_file(self, path: Path) -> bool:
        """Check if file should have its content included"""
        if not path.is_file():
            return False
        
        # Check by extension
        if path.suffix.lower() in self.CODE_EXTENSIONS:
            return True
        
        # Check by full name (for files without extensions)
        if path.name in {'Makefile', 'Dockerfile', 'requirements.txt', 'package.json'}:
            return True
        
        return False
    
    def get_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content if it's not too large"""
        try:
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                return f"[File too large: {file_path.stat().st_size:,} bytes]"
            
            # Try to read as text
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "[Binary file]"
        except Exception as e:
            return f"[Error reading file: {e}]"
    
    def generate_tree(
        self,
        directory: Path,
        prefix: str = "",
        is_last: bool = True,
        is_root: bool = True
    ) -> List[str]:
        """Generate tree structure recursively"""
        lines = []
        
        if is_root:
            lines.append(f"{directory.name}/")
        
        # Get all items in directory
        try:
            items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
            return lines
        
        # Filter out ignored items
        items = [item for item in items if not self.should_ignore(item)]
        
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            
            # Create prefix for this item
            if is_root:
                item_prefix = ""
                child_prefix = ""
            else:
                item_prefix = prefix + ("└── " if is_last_item else "├── ")
                child_prefix = prefix + ("    " if is_last_item else "│   ")
            
            if item.is_dir():
                # Directory
                lines.append(f"{item_prefix}{item.name}/")
                # Recursively process subdirectory
                lines.extend(
                    self.generate_tree(item, child_prefix, is_last_item, is_root=False)
                )
            else:
                # File
                lines.append(f"{item_prefix}{item.name}")
                
                # Include file content if requested
                if self.include_code and self.is_code_file(item):
                    content = self.get_file_content(item)
                    if content:
                        lines.append(f"{child_prefix}")
                        lines.append(f"{child_prefix}```{item.suffix[1:] if item.suffix else ''}")
                        # Add content with proper indentation
                        for line in content.splitlines():
                            lines.append(f"{child_prefix}{line}")
                        lines.append(f"{child_prefix}```")
                        lines.append(f"{child_prefix}")
        
        return lines
    
    def flatten(self) -> str:
        """Generate the complete flattened output"""
        lines = []
        
        # Add header
        lines.append("=" * 80)
        lines.append(f"Directory Structure: {self.root_dir}")
        lines.append("=" * 80)
        lines.append("")
        
        # Generate tree
        tree_lines = self.generate_tree(self.root_dir)
        lines.extend(tree_lines)
        
        # Add footer
        lines.append("")
        lines.append("=" * 80)
        
        # Add statistics
        if self.include_code:
            lines.append("Output includes file contents")
        else:
            lines.append("Output shows tree structure only (use --code to include file contents)")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate a tree structure of directories with optional file contents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate tree structure (saves to scripts/output/src_tree.txt)
  python scripts/code_flattener.py --dir ./src
  
  # Include file contents (saves to scripts/output/src_tree_with_code.txt)
  python scripts/code_flattener.py --dir ./src --code
  
  # Custom ignore patterns
  python scripts/code_flattener.py --dir ./src --ignore "*.test.py" --ignore "temp_*"
  
  # Print to stdout instead of file
  python scripts/code_flattener.py --dir ./src --stdout
        """
    )
    
    parser.add_argument(
        '--dir',
        type=str,
        required=True,
        help='Directory to start from (root starting point)'
    )
    
    parser.add_argument(
        '--code',
        action='store_true',
        help='Include file contents in addition to tree structure'
    )
    
    parser.add_argument(
        '--ignore',
        action='append',
        default=[],
        help='Additional patterns to ignore (can be used multiple times)'
    )
    
    parser.add_argument(
        '--max-size',
        type=int,
        default=1024 * 1024,  # 1MB
        help='Maximum file size to include (in bytes, default: 1MB)'
    )
    
    parser.add_argument(
        '--stdout',
        action='store_true',
        help='Print to stdout instead of saving to file'
    )
    
    args = parser.parse_args()
    
    try:
        # Create flattener with custom ignore patterns
        ignore_patterns = CodeFlattener.DEFAULT_IGNORE_PATTERNS.copy()
        ignore_patterns.update(args.ignore)
        
        flattener = CodeFlattener(
            root_dir=args.dir,
            include_code=args.code,
            ignore_patterns=ignore_patterns,
            max_file_size=args.max_size
        )
        
        # Generate output
        output = flattener.flatten()
        
        # Determine output handling
        if args.stdout:
            print(output)
        else:
            # Create output directory if it doesn't exist
            script_dir = Path(__file__).parent
            output_dir = script_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename based on input directory
            dir_path = Path(args.dir).resolve()
            dir_name = dir_path.name.replace('/', '_').replace('\\', '_').replace('.', '_')
            if not dir_name:  # Handle root directory
                dir_name = "root"
            
            # Add suffix based on whether code is included
            suffix = "_tree_with_code" if args.code else "_tree"
            output_file = output_dir / f"{dir_name}{suffix}.txt"
            
            # Write output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            
            print(f"Output written to: {output_file}")
            print(f"File size: {output_file.stat().st_size:,} bytes")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
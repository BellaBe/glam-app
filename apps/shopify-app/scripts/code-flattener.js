#!/usr/bin/env node
/**
 * Code Flattener Script
 * 
 * Generates a tree structure of directories and optionally includes file contents.
 * Useful for documentation, code reviews, or sharing project structure.
 * node scripts/code-flattener.js --dir ./app --code
 * # Basic usage
 * node scripts/code-flattener.js --dir ./app
 * # With code content
 * node scripts/code-flattener.js --dir ./app --code
 * # See help
 * node scripts/code-flattener.js --help
 * # Output to console
 * node scripts/code-flattener.js --dir ./app --stdout

 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ES module equivalents of __filename and __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class CodeFlattener {
    /**
     * Flattens directory structure into tree format with optional code content
     */
    
    // Common files/directories to ignore
    static DEFAULT_IGNORE_PATTERNS = new Set([
        // Version control
        '.git', '.svn', '.hg',
        
        // Python
        '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.Python', '*.egg-info',
        'venv', 'env', '.venv', '.env', 'virtualenv',
        
        // Node.js
        'node_modules', 'npm-debug.log', 'yarn-error.log',
        
        // IDE
        '.idea', '.vscode', '*.swp', '*.swo', '.DS_Store',
        
        // Build artifacts
        'build', 'dist', 'target', '*.so', '*.dylib', '*.dll',
        
        // Other
        '.coverage', '.pytest_cache', '.mypy_cache', '.tox',
        'htmlcov', '*.log', '.dockerignore'
    ]);
    
    // File extensions to include when showing code
    static CODE_EXTENSIONS = new Set([
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
        '.sql', '.sh', '.bash', '.zsh', '.fish',
        '.html', '.css', '.scss', '.sass', '.less',
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.md', '.rst', '.txt', '.dockerfile', '.dockerignore',
        '.gitignore', '.env.example'
    ]);
    
    static SPECIAL_FILES = new Set([
        'Makefile', 'Dockerfile', 'requirements.txt', 'package.json', 'package-lock.json'
    ]);
    
    constructor(rootDir, options = {}) {
        this.rootDir = path.resolve(rootDir);
        this.includeCode = options.includeCode || false;
        this.ignorePatterns = options.ignorePatterns || new Set(CodeFlattener.DEFAULT_IGNORE_PATTERNS);
        this.maxFileSize = options.maxFileSize || 1024 * 1024; // 1MB default
        
        if (!fs.existsSync(this.rootDir)) {
            throw new Error(`Directory does not exist: ${rootDir}`);
        }
        
        if (!fs.statSync(this.rootDir).isDirectory()) {
            throw new Error(`Path is not a directory: ${rootDir}`);
        }
    }
    
    /**
     * Check if path should be ignored based on patterns
     */
    shouldIgnore(filePath) {
        const name = path.basename(filePath);
        
        for (const pattern of this.ignorePatterns) {
            if (this.matchPattern(name, pattern)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Simple pattern matching (supports * wildcards)
     */
    matchPattern(str, pattern) {
        if (!pattern.includes('*')) {
            return str === pattern;
        }
        
        const regexPattern = pattern
            .replace(/\./g, '\\.')
            .replace(/\*/g, '.*');
        
        return new RegExp(`^${regexPattern}$`).test(str);
    }
    
    /**
     * Check if file should have its content included
     */
    isCodeFile(filePath) {
        if (!fs.statSync(filePath).isFile()) {
            return false;
        }
        
        const ext = path.extname(filePath).toLowerCase();
        const name = path.basename(filePath);
        
        // Check by extension
        if (CodeFlattener.CODE_EXTENSIONS.has(ext)) {
            return true;
        }
        
        // Check by full name (for files without extensions)
        if (CodeFlattener.SPECIAL_FILES.has(name)) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Read file content if it's not too large
     */
    getFileContent(filePath) {
        try {
            const stats = fs.statSync(filePath);
            
            // Check file size
            if (stats.size > this.maxFileSize) {
                return `[File too large: ${stats.size.toLocaleString()} bytes]`;
            }
            
            // Try to read as text
            return fs.readFileSync(filePath, 'utf8');
        } catch (error) {
            if (error.code === 'EISDIR') {
                return '[Directory]';
            }
            return `[Error reading file: ${error.message}]`;
        }
    }
    
    /**
     * Generate tree structure recursively (structure only, no file contents)
     */
    generateTree(directory, prefix = "", isLast = true, isRoot = true) {
        const lines = [];
        
        if (isRoot) {
            lines.push(`${path.basename(directory)}/`);
        }
        
        // Get all items in directory
        let items;
        try {
            items = fs.readdirSync(directory);
        } catch (error) {
            lines.push(`${prefix}[Permission Denied]`);
            return lines;
        }
        
        // Filter out ignored items and sort
        items = items
            .map(item => path.join(directory, item))
            .filter(item => !this.shouldIgnore(item))
            .sort((a, b) => {
                const aIsFile = fs.statSync(a).isFile();
                const bIsFile = fs.statSync(b).isFile();
                
                // Directories first, then files
                if (aIsFile !== bIsFile) {
                    return aIsFile ? 1 : -1;
                }
                
                // Alphabetical within same type
                return path.basename(a).toLowerCase().localeCompare(path.basename(b).toLowerCase());
            });
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const isLastItem = i === items.length - 1;
            const itemName = path.basename(item);
            
            // Create prefix for this item
            let itemPrefix, childPrefix;
            if (isRoot) {
                itemPrefix = "";
                childPrefix = "";
            } else {
                itemPrefix = prefix + (isLastItem ? "└── " : "├── ");
                childPrefix = prefix + (isLastItem ? "    " : "│   ");
            }
            
            const stats = fs.statSync(item);
            
            if (stats.isDirectory()) {
                // Directory
                lines.push(`${itemPrefix}${itemName}/`);
                // Recursively process subdirectory
                lines.push(...this.generateTree(item, childPrefix, isLastItem, false));
            } else {
                // File
                lines.push(`${itemPrefix}${itemName}`);
            }
        }
        
        return lines;
    }

    /**
     * Collect all code files recursively
     */
    collectCodeFiles(directory, relativePath = "") {
        const codeFiles = [];
        
        // Get all items in directory
        let items;
        try {
            items = fs.readdirSync(directory);
        } catch (error) {
            return codeFiles;
        }
        
        // Filter out ignored items and sort
        items = items
            .map(item => path.join(directory, item))
            .filter(item => !this.shouldIgnore(item))
            .sort((a, b) => {
                const aIsFile = fs.statSync(a).isFile();
                const bIsFile = fs.statSync(b).isFile();
                
                // Directories first, then files
                if (aIsFile !== bIsFile) {
                    return aIsFile ? 1 : -1;
                }
                
                // Alphabetical within same type
                return path.basename(a).toLowerCase().localeCompare(path.basename(b).toLowerCase());
            });
        
        for (const item of items) {
            const stats = fs.statSync(item);
            const itemName = path.basename(item);
            const itemRelativePath = relativePath ? path.join(relativePath, itemName) : itemName;
            
            if (stats.isDirectory()) {
                // Recursively collect from subdirectory
                codeFiles.push(...this.collectCodeFiles(item, itemRelativePath));
            } else if (this.isCodeFile(item)) {
                // Add code file
                codeFiles.push({
                    fullPath: item,
                    relativePath: itemRelativePath,
                    content: this.getFileContent(item)
                });
            }
        }
        
        return codeFiles;
    }
    
    /**
     * Generate the complete flattened output
     */
    flatten() {
        const lines = [];
        
        // Add header
        lines.push("=".repeat(80));
        lines.push(`Directory Structure: ${this.rootDir}`);
        lines.push("=".repeat(80));
        lines.push("");
        
        // Generate tree structure (without file contents)
        const treeLines = this.generateTree(this.rootDir);
        lines.push(...treeLines);
        
        // Add file contents section if requested
        if (this.includeCode) {
            const codeFiles = this.collectCodeFiles(this.rootDir);
            
            if (codeFiles.length > 0) {
                lines.push("");
                lines.push("=".repeat(80));
                lines.push("FILE CONTENTS");
                lines.push("=".repeat(80));
                lines.push("");
                
                for (let i = 0; i < codeFiles.length; i++) {
                    const file = codeFiles[i];
                    
                    // File header
                    lines.push(`${"─".repeat(60)}`);
                    lines.push(`📄 ${file.relativePath}`);
                    lines.push(`${"─".repeat(60)}`);
                    lines.push("");
                    
                    // File content with syntax highlighting
                    const ext = path.extname(file.fullPath).slice(1) || '';
                    lines.push(`\`\`\`${ext}`);
                    lines.push(file.content);
                    lines.push(`\`\`\``);
                    
                    // Add spacing between files (except for the last one)
                    if (i < codeFiles.length - 1) {
                        lines.push("");
                        lines.push("");
                    }
                }
            }
        }
        
        // Add footer
        lines.push("");
        lines.push("=".repeat(80));
        
        // Add statistics
        if (this.includeCode) {
            const codeFiles = this.collectCodeFiles(this.rootDir);
            lines.push(`Output includes file contents (${codeFiles.length} files)`);
        } else {
            lines.push("Output shows tree structure only (use --code to include file contents)");
        }
        
        lines.push("=".repeat(80));
        
        return lines.join('\n');
    }
}

/**
 * Simple argument parser (replaces commander dependency)
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        dir: null,
        code: false,
        ignore: [],
        maxSize: 1024 * 1024,
        stdout: false,
        help: false
    };
    
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        
        switch (arg) {
            case '--dir':
                options.dir = args[++i];
                break;
            case '--code':
                options.code = true;
                break;
            case '--ignore':
                options.ignore.push(args[++i]);
                break;
            case '--max-size':
                options.maxSize = parseInt(args[++i]);
                break;
            case '--stdout':
                options.stdout = true;
                break;
            case '--help':
            case '-h':
                options.help = true;
                break;
            default:
                if (arg.startsWith('--')) {
                    console.error(`Unknown option: ${arg}`);
                    process.exit(1);
                }
        }
    }
    
    return options;
}

/**
 * Display help message
 */
function showHelp() {
    console.log(`
Code Flattener Script

Generate a tree structure of directories with optional file contents.

Usage:
  node scripts/code-flattener.js --dir <directory> [options]

Options:
  --dir <directory>     Directory to start from (required)
  --code               Include file contents in addition to tree structure
  --ignore <pattern>   Additional patterns to ignore (can be used multiple times)
  --max-size <bytes>   Maximum file size to include (default: 1048576)
  --stdout             Print to stdout instead of saving to file
  --help, -h           Show this help message

Examples:
  # Generate tree structure (saves to scripts/output/src_tree.txt)
  node scripts/code-flattener.js --dir ./src
  
  # Include file contents (saves to scripts/output/src_tree_with_code.txt)
  node scripts/code-flattener.js --dir ./src --code
  
  # Custom ignore patterns
  node scripts/code-flattener.js --dir ./src --ignore "*.test.js" --ignore "temp_*"
  
  # Print to stdout instead of file
  node scripts/code-flattener.js --dir ./src --stdout
    `);
}

/**
 * Main entry point
 */
function main() {
    const options = parseArgs();
    
    if (options.help) {
        showHelp();
        return;
    }
    
    if (!options.dir) {
        console.error('Error: --dir is required');
        console.error('Use --help for usage information');
        process.exit(1);
    }
    
    try {
        // Create flattener with custom ignore patterns
        const ignorePatterns = new Set(CodeFlattener.DEFAULT_IGNORE_PATTERNS);
        options.ignore.forEach(pattern => ignorePatterns.add(pattern));
        
        const flattener = new CodeFlattener(options.dir, {
            includeCode: options.code,
            ignorePatterns: ignorePatterns,
            maxFileSize: options.maxSize
        });
        
        // Generate output
        const output = flattener.flatten();
        
        // Determine output handling
        if (options.stdout) {
            console.log(output);
        } else {
            // Create output directory if it doesn't exist
            const scriptDir = __dirname;
            const outputDir = path.join(scriptDir, 'output');
            
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }
            
            // Generate filename based on input directory
            const dirPath = path.resolve(options.dir);
            let dirName = path.basename(dirPath).replace(/[/\\\.]/g, '_');
            if (!dirName) { // Handle root directory
                dirName = "root";
            }
            
            // Add suffix based on whether code is included
            const suffix = options.code ? "_tree_with_code" : "_tree";
            const outputFile = path.join(outputDir, `${dirName}${suffix}.txt`);
            
            // Write output
            fs.writeFileSync(outputFile, output, 'utf8');
            
            console.log(`Output written to: ${outputFile}`);
            console.log(`File size: ${fs.statSync(outputFile).size.toLocaleString()} bytes`);
        }
    } catch (error) {
        console.error(`Error: ${error.message}`);
        process.exit(1);
    }
}

// Run main function if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export { CodeFlattener };
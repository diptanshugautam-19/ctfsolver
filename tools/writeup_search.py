#!/usr/bin/env python3
"""
Local CTF Writeup Search Engine (Local RAG) (tools/writeup_search.py)
Uses SQLite FTS5 (Full-Text Search with BM25 ranking) to index and search thousands
of local CTF writeups, exploits, and technique guides instantly with 0 external dependencies.
"""

import os
import sys
import sqlite3
import argparse
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DB_PATH = Path(__file__).resolve().parent.parent / "writeups.db"

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize the SQLite database with FTS5 virtual table."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS writeups USING fts5(
            path UNINDEXED,
            title,
            category,
            content,
            tokenize='porter unicode61'
        );
    """)
    conn.commit()
    return conn

def extract_metadata(file_path: Path, text: str) -> Dict[str, str]:
    """Derive title and category from frontmatter, directory structure, or first heading."""
    title = file_path.stem
    category = "general"

    # Infer category from path
    path_lower = str(file_path).lower()
    for cat in ["osint", "crypto", "pwn", "rev", "web", "forensics", "misc", "dld", "hardware", "iot", "rf", "radio", "ics", "firmware"]:
        if f"/{cat}" in path_lower or f"\\{cat}" in path_lower or cat in path_lower:
            category = "hardware" if cat in ["rf", "radio", "ics", "firmware", "iot"] else cat
            break

    # Look for first Markdown heading
    for line in text.splitlines():
        line_s = line.strip()
        if line_s.startswith("# "):
            title = line_s[2:].strip()
            break
        elif line_s.startswith("title:"):
            title = line_s.split(":", 1)[1].strip().strip('"\'')
        elif line_s.startswith("category:"):
            category = line_s.split(":", 1)[1].strip().strip('"\'')

    return {"title": title, "category": category}

def index_directory(target_dir: Path, db_path: Path = DB_PATH, clear_existing: bool = False) -> int:
    """Recursively index all writeup files (.md, .txt, .py) in target_dir."""
    conn = init_db(db_path)
    cur = conn.cursor()

    if clear_existing:
        cur.execute("DELETE FROM writeups;")
        conn.commit()

    count = 0
    extensions = {".md", ".txt", ".rst", ".py", ".sol", ".pdf", ".docx", ".json", ".html", ".php", ".ino", ".c", ".cpp", ".h", ".v", ".sv", ".vhd"}

    for root, _, files in os.walk(target_dir):
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() in extensions:
                try:
                    if p.suffix.lower() == ".pdf":
                        try:
                            import pypdf
                            reader = pypdf.PdfReader(str(p))
                            content = "\n".join(page.extract_text() or "" for page in reader.pages)
                        except Exception:
                            continue
                    elif p.suffix.lower() == ".docx":
                        try:
                            import zipfile
                            import xml.etree.ElementTree as ET
                            with zipfile.ZipFile(str(p)) as z:
                                xml_content = z.read('word/document.xml')
                                tree = ET.fromstring(xml_content)
                                text_parts = [elem.text or '' for elem in tree.iter() if elem.tag.endswith('}t')]
                                content = "".join(text_parts)
                        except Exception:
                            continue
                    else:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                            content = fp.read()
                    
                    if len(content.strip()) < 20:
                        continue

                    meta = extract_metadata(p, content)
                    rel_path = str(p)

                    # Update or insert
                    cur.execute("DELETE FROM writeups WHERE path = ?;", (rel_path,))
                    cur.execute(
                        "INSERT INTO writeups (path, title, category, content) VALUES (?, ?, ?, ?);",
                        (rel_path, meta["title"], meta["category"], content)
                    )
                    count += 1
                except Exception as e:
                    pass

    conn.commit()
    conn.close()
    return count

def search_writeups(query: str, category: Optional[str] = None, limit: int = 5, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Search the FTS5 index using BM25 ranking and return snippets."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Escape query for FTS5 syntax safety while preserving phrase searches
    clean_q = query.replace("'", "''")
    cat_filter = f" AND category = '{category.lower()}'" if category else ""
    
    def run_query(q_str):
        sql = f"""
            SELECT 
                path, 
                title, 
                category, 
                snippet(writeups, 3, '[MATCH]', '[/MATCH]', '...', 25),
                bm25(writeups) as rank,
                content
            FROM writeups 
            WHERE writeups MATCH ? {cat_filter}
            ORDER BY rank
            LIMIT ?;
        """
        cur.execute(sql, (q_str, limit))
        rows = cur.fetchall()
        res = []
        for r in rows:
            res.append({
                "path": r[0],
                "title": r[1],
                "category": r[2],
                "snippet": r[3],
                "score": round(-float(r[4]), 2),
                "content": r[5]
            })
        return res

    try:
        results = run_query(clean_q)
        if not results:
            # Fallback 1: Decompose compound terms (e.g. ret2libc -> ret, libc)
            expanded = []
            for t in clean_q.split():
                subwords = re.findall(r'[a-zA-Z]+|\d+', t)
                expanded.extend([w for w in subwords if len(w) >= 3])
            
            if expanded:
                and_q = " ".join([f'"{w}"' for w in expanded])
                results = run_query(and_q)
                if not results:
                    or_q = " OR ".join([f'"{w}"' for w in expanded])
                    results = run_query(or_q)
        conn.close()
        return results
    except Exception as e:
        conn.close()
        try:
            conn2 = sqlite3.connect(str(db_path))
            cur2 = conn2.cursor()
            # Simple quoted fallback
            safe_q = f'"{query.replace("\"", "")}"'
            cur2.execute(f"SELECT path, title, category, snippet(writeups, 3, '[MATCH]', '[/MATCH]', '...', 25), bm25(writeups) as rank, content FROM writeups WHERE writeups MATCH ? {cat_filter} ORDER BY rank LIMIT ?;", (safe_q, limit))
            rows = cur2.fetchall()
            conn2.close()
            return [{"path": r[0], "title": r[1], "category": r[2], "snippet": r[3], "score": round(-float(r[4]), 2), "content": r[5]} for r in rows]
        except Exception:
            return []

def clone_writeup_repo(repo_url: str, dest_folder: Path) -> bool:
    """Shallow clone a public writeup repo to expand the local database."""
    print(f"[*] Cloning {repo_url} (shallow clone)...")
    dest_folder.mkdir(parents=True, exist_ok=True)
    try:
        cmd = ["git", "clone", "--depth", "1", repo_url, str(dest_folder)]
        subprocess.run(cmd, check=True)
        print(f"[+] Successfully cloned to {dest_folder}")
        return True
    except Exception as e:
        print(f"[-] Clone failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Local CTF Writeup Search Engine (Local RAG)")
    parser.add_argument("query", nargs="?", default=None, help="Search query (e.g. 'xs3 LFSR', 'RSA Wiener', 'SSTI')")
    parser.add_argument("--index", type=str, help="Index a specific directory of writeups")
    parser.add_argument("--category", type=str, help="Filter by category (crypto, rev, pwn, web, forensics, dld)")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to display")
    parser.add_argument("--code", action="store_true", help="Extract and display exploit code blocks from top matches")
    parser.add_argument("--clone", type=str, help="Clone a Git repository of writeups into writeups/ archive")
    parser.add_argument("--stats", action="store_true", help="Show total indexed writeups")

    args = parser.parse_args()

    if args.stats:
        if not DB_PATH.exists():
            print("Database does not exist yet. Run with --index first.")
            return
        conn = sqlite3.connect(str(DB_PATH))
        total = conn.execute("SELECT count(*) FROM writeups;").fetchone()[0]
        print(f"[+] Total indexed writeups: {total}")
        conn.close()
        return

    if args.clone:
        clean_url = args.clone.rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        parts = clean_url.split("/")
        if len(parts) >= 2:
            repo_name = f"{parts[-2]}_{parts[-1]}"
        else:
            repo_name = parts[-1]
        target_dir = Path(__file__).resolve().parent.parent / "writeup_archive" / repo_name
        if clone_writeup_repo(args.clone, target_dir):
            indexed = index_directory(target_dir)
            print(f"[+] Indexed {indexed} new writeups from cloned repository.")
        return

    if args.index:
        idx_path = Path(args.index)
        if not idx_path.exists():
            print(f"Path does not exist: {idx_path}")
            return
        print(f"[*] Indexing writeups in {idx_path}...")
        n = index_directory(idx_path)
        print(f"[+] Successfully indexed {n} files into {DB_PATH.name}.")
        return

    if args.query:
        results = search_writeups(args.query, category=args.category, limit=args.limit)
        if not results:
            print(f"[-] No writeups found matching '{args.query}'")
            return
        print(f"\n[+] Found {len(results)} matching writeup(s) for '{args.query}':\n" + "="*70)
        for i, res in enumerate(results, 1):
            print(f"[{i}] {res['title']} ({res['category'].upper()}) - Score: {res['score']}")
            print(f"    Path: {res['path']}")
            print(f"    Snippet: {res['snippet']}")
            if args.code and res.get("content"):
                code_blocks = re.findall(r'```(?:python|py|bash|sh|solidity|sol)?\n(.*?)```', res["content"], re.DOTALL)
                if not code_blocks and (res['path'].endswith('.py') or res['path'].endswith('.sh') or res['path'].endswith('.sol')):
                    code_blocks = [res["content"]]
                if code_blocks:
                    print(f"    --- Extracted Code Block ({len(code_blocks[0].strip().splitlines())} lines) ---")
                    lines = code_blocks[0].strip().splitlines()[:20]
                    for l in lines:
                        print(f"    | {l}")
                    if len(code_blocks[0].strip().splitlines()) > 20:
                        print(f"    | ... (truncated {len(code_blocks[0].strip().splitlines()) - 20} lines)")
            print("-" * 70)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

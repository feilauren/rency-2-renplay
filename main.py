#!/usr/bin/env python3
"""
rency-2-renplay: CrewAI multi-agent Cypress → Playwright migration tool.

Usage:
  python main.py --repo /path/to/project       # process all cypress files in a repo
  python main.py --file tests/login.cy.js      # process a single file
  echo "<cypress code>" | python main.py --snippet [--name my_test]  # process stdin
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def find_cypress_files(repo_path: str) -> list[tuple[str, str, str]]:
    """
    Walk repo_path and find all .cy.js/.cy.ts files inside cypress/ folders.

    Returns list of (file_path, output_dir, base_name) tuples where:
      - file_path: absolute path to the cypress file
      - output_dir: sibling playwright/ folder (adjacent to cypress/)
      - base_name: filename without extension (e.g. "login" from "login.cy.js")
    """
    results = []
    for root, dirs, files in os.walk(repo_path):
        # Only process files inside a directory named "cypress"
        if os.path.basename(root) == "cypress":
            parent = os.path.dirname(root)
            playwright_dir = os.path.join(parent, "playwright")
            for fname in files:
                if fname.endswith(".cy.js") or fname.endswith(".cy.ts"):
                    file_path = os.path.join(root, fname)
                    # Strip the .cy.js or .cy.ts extension
                    base = fname.replace(".cy.js", "").replace(".cy.ts", "")
                    results.append((file_path, playwright_dir, base))
    return results


def process_file(file_path: str, output_dir: str, base_name: str) -> None:
    from crew import run_pipeline

    print(f"\n[rency] Processing: {file_path}")
    print(f"[rency] Output dir: {output_dir}")

    with open(file_path, "r") as f:
        cypress_code = f.read()

    os.makedirs(output_dir, exist_ok=True)
    run_pipeline(cypress_code, output_dir, base_name)

    print(f"\n[rency] Done: {file_path}")
    print(f"  {output_dir}/{base_name}.spec.ts   — Playwright test")
    print(f"  {output_dir}/review_{base_name}.md — Review notes")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-agent Cypress → Playwright migration using CrewAI"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--repo", metavar="PATH", help="Path to a repo to scan for cypress/ folders")
    mode.add_argument("--file", metavar="PATH", help="Path to a single Cypress test file")
    mode.add_argument("--snippet", action="store_true", help="Read Cypress code from stdin")

    parser.add_argument(
        "--name",
        metavar="NAME",
        default="snippet",
        help="Base name for output files when using --snippet (default: snippet)",
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        default="output",
        help="Output directory for --file and --snippet modes (default: output/)",
    )

    args = parser.parse_args()

    if args.repo:
        repo_path = os.path.abspath(args.repo)
        if not os.path.isdir(repo_path):
            print(f"[rency] Error: repo path not found: {repo_path}", file=sys.stderr)
            sys.exit(1)

        cypress_files = find_cypress_files(repo_path)
        if not cypress_files:
            print(f"[rency] No Cypress files found under {repo_path}")
            sys.exit(0)

        print(f"[rency] Found {len(cypress_files)} Cypress file(s) to migrate.\n")
        for file_path, output_dir, base_name in cypress_files:
            process_file(file_path, output_dir, base_name)

    elif args.file:
        file_path = os.path.abspath(args.file)
        if not os.path.isfile(file_path):
            print(f"[rency] Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        fname = os.path.basename(file_path)
        base_name = fname.replace(".cy.js", "").replace(".cy.ts", "")
        output_dir = os.path.abspath(args.output)
        process_file(file_path, output_dir, base_name)

    elif args.snippet:
        if sys.stdin.isatty():
            print("[rency] Paste your Cypress code below, then press Ctrl+D when done:\n")
        cypress_code = sys.stdin.read().strip()
        if not cypress_code:
            print("[rency] Error: no input received.", file=sys.stderr)
            sys.exit(1)

        from crew import run_pipeline

        output_dir = os.path.abspath(args.output)
        os.makedirs(output_dir, exist_ok=True)
        base_name = args.name

        print(f"\n[rency] Processing snippet → {output_dir}/{base_name}.spec.ts\n")
        run_pipeline(cypress_code, output_dir, base_name)

        print(f"\n[rency] Done.")
        print(f"  {output_dir}/{base_name}.spec.ts   — Playwright test")
        print(f"  {output_dir}/review_{base_name}.md — Review notes")


if __name__ == "__main__":
    main()

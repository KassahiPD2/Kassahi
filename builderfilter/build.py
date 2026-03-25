import datetime
import json
import os
import re
import subprocess
import urllib.request

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.dirname(SCRIPT_DIR)

VERSION_TXT     = os.path.join(OUTPUT_DIR, "version.txt")
VERSION_SOURCE  = os.path.join(SCRIPT_DIR, "01-header", "02-Version.source.filter")
VERSION_FILTER  = os.path.join(SCRIPT_DIR, "01-header", "02-Version[ALL].filter")


def update_version():
    """Read version.txt and rewrite the version header filter from the source template."""
    with open(VERSION_TXT, encoding="utf-8") as f:
        version = int(f.read().strip())

    today = datetime.date.today()
    timestamp = today.strftime("%b/%d/%y")

    with open(VERSION_SOURCE, encoding="utf-8") as f:
        content = f.read()

    content = content.replace("--timestamp--", timestamp)
    content = content.replace("--buildnum--", str(version))

    with open(VERSION_FILTER, "w", encoding="cp1252", newline="\n") as f:
        f.write(content)

    print(f"Version: build {version} ({timestamp})")


def load_config():
    with open(os.path.join(SCRIPT_DIR, "filters.json"), encoding="utf-8") as f:
        data = json.load(f)
    return data["filters"], data.get("groups", {})


def extract_bracket_tag(filename):
    """Return the content inside [...] in a filename, or None if absent."""
    m = re.search(r'\[([^\]]+)\]', filename)
    return m.group(1) if m else None


def token_matches_filter(token, entry, groups):
    """Return True if a single tag token applies to the given filter entry."""
    if token in groups:
        members = groups[token]
        return entry["name"] in members or any(t in members for t in entry["tags"])
    return token == entry["name"] or token in entry["tags"]


def source_included(bracket_tag, entry, groups):
    """Decide whether a source file should be concatenated into the given filter."""
    if bracket_tag == "ALL":
        return True

    if bracket_tag.startswith("ONLY="):
        tokens = bracket_tag[5:].split("+")
        return any(token_matches_filter(t, entry, groups) for t in tokens)

    if bracket_tag.startswith("ALL-EXCEPT="):
        tokens = bracket_tag[11:].split("+")
        return not any(token_matches_filter(t, entry, groups) for t in tokens)

    # No keyword prefix — treat as implicit ONLY
    tokens = bracket_tag.split("+")
    return any(token_matches_filter(t, entry, groups) for t in tokens)


def sorted_walk(root):
    """
    Yield file paths under root in a depth-first, alphanumerically sorted walk.
    """
    entries = sorted(os.listdir(root))
    for name in entries:
        path = os.path.join(root, name)
        if os.path.isdir(path):
            yield from sorted_walk(path)
        elif os.path.isfile(path):
            yield path


def build_filter(entry, groups):
    parts = []
    subdirs = sorted(
        d for d in os.listdir(SCRIPT_DIR)
        if os.path.isdir(os.path.join(SCRIPT_DIR, d))
    )
    for subdir in subdirs:
        for filepath in sorted_walk(os.path.join(SCRIPT_DIR, subdir)):
            if not filepath.endswith(".filter"):
                continue
            tag = extract_bracket_tag(os.path.basename(filepath))
            if tag is None:
                continue  # template / untagged file — skip
            if source_included(tag, entry, groups):
                with open(filepath, encoding="utf-8") as f:
                    parts.append(f.read())
    return "".join(parts)


def build_filter_definitions(filters):
    """Write filter_definitions.json to the output directory."""
    filter_info = {}
    for i, entry in enumerate(filters, start=1):
        filter_info[str(i)] = {
            "display_name": entry["name"],
            "description": entry.get("description", ""),
            "file_name": entry["file"],
        }
    out_path = os.path.join(OUTPUT_DIR, "filter_definitions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"filter_info": filter_info}, f, indent=2)
    print(f"  wrote filter_definitions.json -> {out_path}")


HIIM_SOURCES = [
    "https://raw.githubusercontent.com/Maaaaaarrk/HiimFilter-PD2-Filter/refs/heads/main/builderfilter/02-alias/04-alias-economy-values%5BALL%5D.filter",
    "https://raw.githubusercontent.com/Maaaaaarrk/HiimFilter-PD2-Filter/refs/heads/main/builderfilter/02-alias/05-unid-unique-set-stars%5BALL%5D.filter",
]
HIIM_DIR = os.path.join(SCRIPT_DIR, "02-alias", "hiim")


def sync_hiim_aliases():
    """Download latest HiimFilter alias files and commit if any changed in CI."""
    updated = []
    for url in HIIM_SOURCES:
        filename = os.path.basename(urllib.request.url2pathname(url))
        dest = os.path.join(HIIM_DIR, filename)
        data = urllib.request.urlopen(url).read()
        new_text = data.decode("utf-8")
        old_text = None
        if os.path.exists(dest):
            with open(dest, encoding="utf-8") as f:
                old_text = f.read()
        if new_text != old_text:
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_text)
            updated.append(filename)
            print(f"  updated {filename}")
        else:
            print(f"  unchanged {filename}")
    if updated and os.environ.get("CI"):
        subprocess.run(["git", "add"] + [os.path.join(HIIM_DIR, f) for f in updated], check=True)
        subprocess.run(
            ["git", "commit", "-m", "Update HiimFilter alias sources"],
            check=True,
        )
        print("  committed hiim alias updates")


def main():
    print("Syncing HiimFilter aliases...")
    sync_hiim_aliases()
    update_version()
    filters, groups = load_config()
    for entry in filters:
        print(f"Building {entry['file']} ...")
        content = build_filter(entry, groups)
        out_path = os.path.join(OUTPUT_DIR, entry["file"])
        with open(out_path, "w", encoding="cp1252", newline="\n") as f:
            f.write(content)
        print(f"  wrote {len(content):,} chars -> {out_path}")
    build_filter_definitions(filters)
    print("All filters built.")


if __name__ == "__main__":
    main()

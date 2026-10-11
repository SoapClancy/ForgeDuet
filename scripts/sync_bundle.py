#!/usr/bin/env python3
"""Keep both standalone skills aligned with canonical protocol/resources."""
import argparse
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sources = list((root / "protocol").glob("*.md")) + list((root / "templates").glob("*"))
    errors = []
    for role in ("build", "review"):
        skill = root / "skills" / ("forgeduet-" + role)
        pairs = [(source, skill / "references" / source.name) for source in sources if source.is_file()]
        for helper in (root / "scripts").rglob("*.py"):
            if helper.name != "sync_bundle.py":
                pairs.append((helper, skill / "scripts" / helper.relative_to(root / "scripts")))
        pairs.append((root / "LICENSE", skill / "LICENSE"))
        for source, destination in pairs:
            if args.check:
                if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                    errors.append(str(destination.relative_to(root)))
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
    if errors:
        print("Stale/missing bundle files:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    print("Standalone skill bundles are synchronized." if args.check else "Updated both standalone skill bundles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

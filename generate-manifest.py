#!/usr/bin/env python3
"""
CS2 Utility — Manifest Generator
Run this script whenever you add new images to your CS2 Utility folder.
It scans the images/ directory and writes manifest.json.

Usage:
    python3 generate-manifest.py
"""

import os
import json
import re

IMAGES_DIR = "images"
OUTPUT     = "manifest.json"

MAPS = ["Ancient","Anubis","Dust2","Inferno","Mirage","Nuke","Vertigo"]

def to_title_case(s):
    return re.sub(r"\w+", lambda m: m.group(0).capitalize(), s)

def parse_entry(rel_path):
    """
    rel_path example:
      Ancient/Smokes/CT Side/CT - CT Spawn to A Main.png
    """
    parts    = rel_path.replace("\\", "/").split("/")
    filename = parts[-1]
    base     = re.sub(r"\.[^.]+$", "", filename)

    map_name     = "Unknown"
    utility_type = "Unknown"
    side         = "CT"
    label        = base

    # ── map from folder ──
    for part in parts:
        for m in MAPS:
            if part.lower() == m.lower():
                map_name = m
                break

    # ── utility type: folder after the map folder ──
    map_idx = next((i for i, p in enumerate(parts)
                    if any(p.lower() == m.lower() for m in MAPS)), -1)
    if map_idx != -1 and map_idx + 1 < len(parts) - 1:
        utility_type = to_title_case(parts[map_idx + 1])

    # ── side from folder name ──
    for part in parts:
        pl = part.lower()
        if "ct side" in pl or pl == "ct":
            side = "CT"; break
        if "t side" in pl:
            side = "T"; break

    # ── label + side from filename ──
    # Format: "CT - CT Spawn to A Main"  or  "T - Window Smoke"
    m = re.match(r"^(CT|T)\s*[-–]\s*(.+)$", base, re.IGNORECASE)
    if m:
        side  = m.group(1).upper()
        label = m.group(2).strip()
    else:
        label = re.sub(r"^(ct|t)\s*[-–]\s*", "", base, flags=re.IGNORECASE).strip()

    # ── fingerprint for dedup ──
    fingerprint = "|".join([map_name, utility_type, side, label]).lower()

    return {
        "path":        rel_path.replace("\\", "/"),
        "map":         map_name,
        "utilityType": utility_type,
        "side":        side,
        "label":       label,
        "fingerprint": fingerprint,
    }

def main():
    entries = []
    seen    = set()

    for root, dirs, files in os.walk(IMAGES_DIR):
        dirs.sort()
        for fname in sorted(files):
            if not re.search(r"\.(png|jpg|jpeg|webp)$", fname, re.IGNORECASE):
                continue
            full     = os.path.join(root, fname)
            rel_path = os.path.relpath(full, IMAGES_DIR).replace("\\", "/")
            entry    = parse_entry(rel_path)

            if entry["fingerprint"] in seen:
                print(f"  SKIP (duplicate): {rel_path}")
                continue
            seen.add(entry["fingerprint"])
            entries.append(entry)
            print(f"  + {entry['map']} / {entry['utilityType']} / {entry['side']} / {entry['label']}")

    with open(OUTPUT, "w") as f:
        json.dump({"images": entries}, f, indent=2)

    print(f"\n✓ manifest.json written — {len(entries)} images")

if __name__ == "__main__":
    main()

from __future__ import annotations


def changed_lines_from_patch(patch: str) -> set[int]:
    changed: set[int] = set()
    new_line = 0

    for line in patch.splitlines():
        if line.startswith("@@"):
            header = line.split(" ")
            new_range = header[2].removeprefix("+")
            new_line = int(new_range.split(",")[0])
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed.add(new_line)
            new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        else:
            new_line += 1

    return changed

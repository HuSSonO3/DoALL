"""Recipe persistence — save/load/parse markdown recipe files."""

import re
from pathlib import Path

SAVE_DIR = Path("file_holders/recipes")


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "recipe"


def parse_saved_recipe(path: Path) -> dict | None:
    """Extract title, tags, time, servings, source, and full content."""
    try:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        meta: dict = {"path": str(path), "filename": path.name, "raw": text}

        title_match = re.match(r"^#\s+(.+)", lines[0]) if lines else None
        meta["title"] = title_match.group(1).strip() if title_match else path.stem

        in_section = "meta"
        ingredients: list[str] = []
        instructions: list[str] = []
        for line in lines[1:]:
            if in_section == "meta":
                if line.startswith("tags:"):
                    meta["tags"] = line.split(":", 1)[1].strip()
                elif line.startswith("time:"):
                    meta["time"] = line.split(":", 1)[1].strip()
                elif line.startswith("servings:"):
                    meta["servings"] = line.split(":", 1)[1].strip()
                elif line.startswith("source:"):
                    meta["source"] = line.split(":", 1)[1].strip()
                elif line.startswith("## Ingredients"):
                    in_section = "ingredients"
                elif line.startswith("## Instructions"):
                    in_section = "instructions"
            elif in_section == "ingredients":
                if line.startswith("## Instructions"):
                    in_section = "instructions"
                elif line.strip().startswith("- "):
                    ingredients.append(line.strip()[2:])
            elif in_section == "instructions":
                if line.strip():
                    instructions.append(line.strip())

        meta["ingredients"] = "\n".join(ingredients)
        meta["instructions"] = "\n".join(instructions)
        return meta
    except Exception:
        return None


def load_all_recipes() -> list[dict]:
    if not SAVE_DIR.exists():
        return []
    recipes = []
    for f in sorted(SAVE_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        meta = parse_saved_recipe(f)
        if meta and meta.get("title"):
            recipes.append(meta)
    return recipes


def save_recipe(title: str, ingredients: str, instructions: str,
                tags: str = "", total_time: str = "", servings: str = "",
                source: str = "") -> str:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    filename = slugify(title) + ".md"
    path = SAVE_DIR / filename

    lines = [f"# {title}", ""]
    if tags:
        lines.append(f"tags: {tags}")
    if total_time:
        lines.append(f"time: {total_time}")
    if servings:
        lines.append(f"servings: {servings}")
    if source:
        lines.append(f"source: {source}")
    lines.append("")
    lines.append("## Ingredients")
    lines.append("")
    for line in ingredients.strip().splitlines():
        line = line.strip()
        if line:
            lines.append(f"- {line}")
    lines.append("")
    lines.append("## Instructions")
    lines.append("")
    for line in instructions.strip().splitlines():
        line = line.strip()
        if line:
            lines.append(line)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)

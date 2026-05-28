import os
from pathlib import Path
from collections import defaultdict

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"}


def scan_directory(root_path):
    """Recursively scan a directory for audio files.

    Returns:
        dict: {
            "tracks": list of track dicts,
            "albums": list of album dicts,
            "errors": list of error strings,
            "skipped_count": int
        }
    """
    root = Path(root_path).expanduser().resolve()
    if not root.exists():
        return {"tracks": [], "albums": [], "errors": [f"Path does not exist: {root}"], "skipped_count": 0}
    if not root.is_dir():
        return {"tracks": [], "albums": [], "errors": [f"Path is not a directory: {root}"], "skipped_count": 0}

    tracks = []
    errors = []
    skipped = 0

    try:
        for entry in sorted(root.rglob("*")):
            if entry.is_file() and entry.suffix.lower() in AUDIO_EXTENSIONS:
                try:
                    track = extract_metadata(entry)
                    tracks.append(track)
                except Exception:
                    skipped += 1
    except PermissionError as e:
        errors.append(f"Permission denied: {e}")

    albums = _group_into_albums(tracks)
    return {"tracks": tracks, "albums": albums, "errors": errors, "skipped_count": skipped}


def extract_metadata(file_path):
    """Extract metadata from file path using folder structure convention.

    Assumes structure: <root>/<artist>/<album>/<track> or <root>/<album>/<track>.
    """
    path = Path(file_path)
    parts = path.parts

    # Use folder structure: parent folder = album, grandparent = artist (if present)
    album = parts[-2] if len(parts) >= 2 else "Unknown Album"
    artist = parts[-3] if len(parts) >= 3 else "Unknown Artist"
    title = path.stem

    # If grandparent looks like an artist (not the root and not shared across albums),
    # treat it as artist. Otherwise, flatten to root/album/track.
    if artist == "Unknown Artist" or artist == album:
        artist = "Unknown Artist"

    return {
        "file_path": str(path),
        "title": title,
        "artist": artist,
        "album": album,
        "duration": 0,
    }


def _group_into_albums(tracks):
    """Group tracks into album dicts."""
    album_map = defaultdict(lambda: {"tracks": [], "artist": "Unknown Artist"})

    for t in tracks:
        key = (t["album"], t["artist"])
        album_map[key]["tracks"].append(t)
        album_map[key]["artist"] = t["artist"]

    albums = []
    for (album_name, artist), data in sorted(album_map.items()):
        albums.append({
            "album": album_name,
            "artist": data["artist"],
            "track_count": len(data["tracks"]),
            "tracks": sorted(data["tracks"], key=lambda t: t["title"]),
        })
    return albums

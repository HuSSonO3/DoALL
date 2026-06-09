"""Word pool and random prompt generator for typing speed tests."""

import random

WORD_POOL = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "great", "been", "might",
    "call", "world", "next", "life", "still", "run", "last", "need", "much",
    "keep", "long", "hand", "place", "case", "week", "point", "group",
    "number", "part", "write", "read", "move", "live", "find", "ask",
    "seem", "help", "talk", "turn", "start", "show", "play", "every",
    "high", "large", "must", "big", "own", "old", "right", "small",
    "home", "school", "never", "same", "another", "begin", "while",
    "above", "each", "left", "close", "late", "few", "stop", "open",
    "true", "light", "both", "young", "head", "under", "story", "saw",
    "along", "best", "end", "across", "city", "tree", "near", "body",
    "earth", "food", "sun", "eye", "door", "water", "room", "mother",
    "area", "money", "book", "word", "side", "kind", "today", "night",
    "face", "white", "early", "walk", "stand", "order", "line", "form",
    "hard", "sure", "land", "air", "care", "second", "letter", "age",
    "fire", "free", "black", "short", "class", "road", "force", "door",
    "build", "river", "horse", "north", "feet", "paper", "child",
    "table", "watch", "carry", "until", "color", "rock", "space",
    "plant", "cover", "star", "bird", "wood", "wind", "morning",
    "deep", "drive", "music", "blue", "green", "front", "simple",
    "clear", "common", "piece", "maybe", "voice", "ground",
    "bring", "low", "happy", "hope", "mind", "care", "rest", "cold",
    "miss", "hair", "hour", "hope", "town", "fall", "lead", "break",
    "car", "cut", "god", "buy", "stay", "train", "pass", "hold",
    "enter", "step", "ready", "final", "door", "teach", "land",
    "east", "plan", "ready", "north", "ago", "sat", "main", "wide",
    "law", "death", "south", "season", "room", "act", "floor",
    "wall", "floor", "sea", "dream", "touch", "past", "spring",
    "check", "hot", "summer", "winter", "glass", "smile", "edge",
    "price", "serve", "warm", "heart", "love", "hour", "road",
    "field", "round", "dark", "learn", "truth", "mark", "press",
    "green", "stone", "blood", "gold", "stick", "watch", "shape",
    "cause", "south", "sign", "built", "center", "team", "future",
    "pick", "sound", "office", "window", "gone", "type", "sleep",
    "wrong", "month", "notice", "valley", "coast", "class", "rich",
    "unit", "street", "decide", "answer", "mouth", "camp", "store",
    "object", "square", "visit", "island", "track", "finger",
    "happen", "thick", "pool", "village", "subject", "century",
    "corner", "brown", "labor", "pound", "basis", "catch", "cross",
]

RANDOM_WORD_COUNT = range(30, 51)  # 30–50 words per prompt


def random_prompt() -> str:
    count = random.choice(list(RANDOM_WORD_COUNT))
    words = random.choices(WORD_POOL, k=count)
    return " ".join(words)

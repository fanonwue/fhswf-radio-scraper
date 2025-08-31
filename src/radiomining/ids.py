import hashlib, re, unicodedata

def make_story_id(story_key: str) -> str:
    norm = unicodedata.normalize("NFKD", story_key).encode("ascii","ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")
    h = hashlib.sha1(norm.encode()).hexdigest()[:8]
    return f"{slug}-{h}"

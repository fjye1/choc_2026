import hashlib

def gravatar_url(email, size=34, default="retro"):
    email = email.strip().lower().encode("utf-8")
    hash_email = hashlib.md5(email).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_email}?s={size}&d={default}"
from functools import wraps
from flask import request, abort
import os

def internal_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if auth != f"Bearer {os.getenv('INTERNAL_API_TOKEN')}":
            abort(403)
        return f(*args, **kwargs)
    return decorated
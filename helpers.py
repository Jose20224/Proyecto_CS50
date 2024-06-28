from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userName") is None:
            return redirect("/login")
        
        if session.get("userName") is not None and session.get("activo") == 0:
            return redirect("/digitos")
        return f(*args, **kwargs)

    return decorated_function
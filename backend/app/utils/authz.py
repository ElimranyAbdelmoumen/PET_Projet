from functools import wraps
from flask import session, request, redirect, url_for, render_template

def browser_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.cookies.get("bss_active"):
            return render_template("browser_required.html"), 403
        return fn(*args, **kwargs)
    return wrapper

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.cookies.get("bss_active"):
            return render_template("browser_required.html"), 403
        if not session.get("user_id"):
            return redirect(url_for("web.login_page"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.cookies.get("bss_active"):
            return render_template("browser_required.html"), 403
        if not session.get("user_id"):
            return redirect(url_for("web.login_page"))
        if session.get("role") != "ADMIN":
            return redirect(url_for("web.home"))
        return fn(*args, **kwargs)
    return wrapper

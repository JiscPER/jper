import re, os
from unicodedata import normalize
from functools import wraps
from flask import request, current_app, flash, redirect, send_from_directory, abort, render_template, make_response
from urllib.parse import urlparse, urljoin

from standalone_octopus.core import app

# serve static files from multiple potential locations
def custom_static(path):
    for dir in app.config.get("STATIC_PATHS", []):
        target = os.path.join(dir, path)
        if os.path.isfile(target):
            return send_from_directory(os.path.dirname(target), os.path.basename(target))
    abort(404)

# a decorator to be used elsewhere (or in this file) in the app,
# anywhere where a view f() should be served only over SSL
def ssl_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if app.config.get("SSL"):
            if request.is_secure:
                return fn(*args, **kwargs)
            else:
                return redirect(request.url.replace("http://", "https://"))

        return fn(*args, **kwargs)

    return decorated_view

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    if ( test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc ):
        return target
    else:
        return '/'

def jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            resp = f(*args,**kwargs)
            content = str(callback) + '(' + str(resp.data) + ')'
            nr = current_app.response_class(content, mimetype='application/javascript')
            nr.status_code = resp.status_code
            return nr
        else:
            return f(*args, **kwargs)
    return decorated_function


# derived from http://flask.pocoo.org/snippets/45/ (pd) and customised
def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    if best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']:
        best = True
    else:
        best = False
    if request.values.get('format','').lower() == 'json' or request.path.endswith(".json"):
        best = True
    return best


# derived from http://flask.pocoo.org/snippets/5/ (public domain)
# changed delimiter to _ instead of - due to ES search problem on the -
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim='_'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return str(delim.join(result))

def flash_with_url(message, category=''):
    flash(message, category + '+contains-url')

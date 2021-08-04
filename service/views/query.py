'''
An elasticsearch query pass-through.
Has auth control, so it is better than exposing your ES index directly.
'''

import json, urllib.request, urllib.error, urllib.parse

from flask import Blueprint, request, abort, make_response
from flask_login import current_user

from service import models

blueprint = Blueprint('query', __name__)


# pass queries direct to index. POST only for receipt of complex query objects
@blueprint.route('/<path:path>', methods=['GET','POST'])
@blueprint.route('/', methods=['GET','POST'])
def query(path='match_prov'):
    pathparts = path.strip('/').split('/')
    subpath = pathparts[0]
    if subpath.lower() == 'match_prov': 
        klass = getattr(models, 'MatchProvenance' )      
    elif subpath.lower() == 'failed':
        klass = getattr(models, 'FailedNotification')
    # could add more index types if want to make them queryable
    else:
        abort(401)
    
    if len(pathparts) == 2 and pathparts[1] not in ['_search']:
        if request.method == 'POST':
            abort(401)
        else:
            rec = klass().pull(pathparts[1])
            if rec:
                if not current_user.is_anonymous:
                    resp = make_response( rec.json )
                else:
                    abort(401)
            else:
                abort(404)
    else:
        if request.method == "POST":
            if request.json:
                qs = request.json
            else:
                qs = list(dict(request.form).keys())[-1]
        elif 'q' in request.values:
            qs = {'query': {'query_string': { 'query': request.values['q'] }}}
        elif 'source' in request.values:
            qs = json.loads(urllib.parse.unquote(request.values['source']))
        else: 
            qs = {'query': {'match_all': {}}}

        for item in request.values:
            if item not in ['q','source','callback','_'] and isinstance(qs,dict):
                qs[item] = request.values[item]

        resp = make_response( json.dumps(klass().query(q=qs)) )

    resp.mimetype = "application/json"
    return resp

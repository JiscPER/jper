import esprit, json, re
from standalone_octopus.core import app
from flask import Blueprint, request, abort, make_response
from standalone_octopus.lib import webapp, plugin
from standalone_octopus.modules.es import dao
from datetime import datetime

blueprint = Blueprint('searchapi', __name__)

def substitute(query, substitutions):
    if len(list(substitutions.keys())) == 0:
        return query

    # apply the regex escapes to the substitutions, so we know they
    # are ready to be matched
    escsubs = {}
    for k, v in substitutions.items():
        escsubs[k.replace(":", "\\:")] = v

    # define a function which takes the match group and returns the
    # substitution if there is one
    def rep(match):
        for k, v in escsubs.items():
            if k == match.group(1):
                return v
        return match.group(1)

    # define the regular expressions for splitting and then extracting
    # the field to be substituted
    split_rx = "([^\\\\]:)"
    field_rx = "([^\s\+\-\(\)\"]+?):$"

    # split the query around any unescaped colons
    bits = re.split(split_rx, query)

    # stitch back together the split sections and the separators
    segs = [bits[i] + bits[i+1] for i in range(0, len(bits), 2) if i+1 < len(bits)] + [bits[len(bits) - 1]] if len(bits) % 2 == 1 else []

    # substitute the fields as required
    subs = []
    for seg in segs:
        if seg.endswith(":"):
            subs.append(re.sub(field_rx, rep, seg))
        else:
            subs.append(seg)

    return ":".join(subs)

def allowed(query, wildcards=False, fuzzy=False):
    if not wildcards:
        rx = "(.+[^\\\\][\?\*]+.*)"
        if re.search(rx, query):
            return False

    if not fuzzy:
        # this covers both fuzzy searching and proximity searching
        rx = "(.+[^\\\\]~[0-9]{0,1}[\.]{0,1}[0-9]{0,1})"
        if re.search(rx, query):
            return False

    return True

# simple proxy for an underlying ES index, queried using a query string
@blueprint.route('/search', methods=['GET'])
@webapp.jsonp
def search():
    # get the values for the 3 key bits of search info: the query, the page number and the page size
    q = request.values.get("q")
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)

    # check that we have been given a query
    if q is None or q == "":
        abort(400)

    # check the page is an integer greater than 0
    try:
        page = int(page)
    except:
        abort(400)
    if page < 1:
        page = 1

    # limit the page size as per the configuration
    try:
        psize = int(psize)
    except:
        abort(400)
    if psize > app.config.get("SEARCH_MAX_PAGE_SIZE", 100):
        psize = app.config.get("SEARCH_MAX_PAGE_SIZE", 100)
    elif psize < 1:
        psize = 10

    # calculate the position of the from cursor in the document set
    fro = (page - 1) * psize

    # assemble the query
    query = dao.QueryStringQuery(q, fro, psize)

    # load the DAO class and send the query through it
    klazz = plugin.load_class(app.config.get("SEARCH_DAO"))
    res = klazz.query(q=query.query())

    # check to see if there was a search error
    if res.get("error") is not None:
        abort(400)

    # unpack the results and pull out the search metadata
    obs = esprit.raw.unpack_json_result(res)
    total = res.get("hits", {}).get("total", 0)

    # optionally filter the result objects as per the config
    filter = app.config.get("SEARCH_RESULT_FILTER")
    if filter is not None:
        fn = plugin.load_function(filter)
        obs = [fn(o) for o in obs]

    # build the response object
    response = {
        "total" : total,
        "page" : page,
        "pageSize" : psize,
        "timestamp" : datetime.utcnow().strftime("%Y-%m%dT%H:%M:%SZ"),
        "query" : q,
        "results" : obs
    }

    resp = make_response(json.dumps(response))
    resp.mimetype = "application/json"
    return resp
from octopus.core import app
from werkzeug import generate_password_hash
import uuid, requests, json

ELASTIC_SEARCH_HOST = "http://gateway:9200"
ELASTIC_SEARCH_INDEX = "jper"

def initialise():
	i = app.config['ELASTIC_SEARCH_HOST'] + '/' + app.config['ELASTIC_SEARCH_INDEX'] + '/'
	un = 'admin'
	ia = i + '/account/' + un
	ae = requests.get(ia)
	if ae.status_code != 200:
		su = {
			"id":un, 
			"role": ["admin"],
			"email":"mark@cottagelabs.com",
			"api_key":str(uuid.uuid4()),
			"password":generate_password_hash(un)
		}
		c = requests.post(ia, data=json.dumps(su))
		print "first superuser account created for user " + un + " with password " + un 

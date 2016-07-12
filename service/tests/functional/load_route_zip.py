"""
Script which can be used to load a ZIP file into the system for the purposes of testing

Nothing particularly clever going on here.  Set ZIPFILE to the path to the file you want to work with, then
run the script.

It does not clean up after itself, so whatever you do, don't use this on a live environment, it's for testing
purposes only.
"""
ZIPFILE = "/path/to/your/zip/here/FilesAndJATS.zip"

from service import api, models, routing
import time

acc = models.Account()
acc.add_role("publisher")
acc.save(blocking=True)

note = {
    "content": {
        "packaging_format": "https://datahub.deepgreen.org/FilesAndJATS"
        ## "packaging_format": "https://pubrouter.jisc.ac.uk/FilesAndJATS"
    }
}

with open(ZIPFILE, "rb") as f:
    unrouted = api.JPER.create_notification(acc, note, f)

time.sleep(2)

wasrouted = routing.route(unrouted)

# Note that this does not delete the unrouted notification

# maximum number of times to attempt retries on an HTTP request
HTTP_MAX_RETRIES = 5

# when backing off an http request, the next attempt will be 2**attempt_number, multiplied by this back-off factor
# increase the factor to back off further each time, and reduce it to back off less each time
HTTP_BACK_OFF_FACTOR = 1

# when backing off an http request, never back off further than this each time.  Allows the power-of-2 law used in
# the back-off to be contained to a reasonable number
HTTP_MAX_BACK_OFF = 30

# maximum amount of time to wait for an ack from the server on an HTTP request
HTTP_TIMEOUT = 30

# should we try again if we receive a timeout from the server?
HTTP_RETRY_ON_TIMEOUT = True

# which http code responses should result in a retry?
HTTP_RETRY_CODES = [
    403,    # forbidden; retry in case this is returned as a rate-limiter
    408,    # request timeoue
    409,    # conflict; not clear whether retry will help or not, but worth a go
    420,    # enhance your calm; twitter rate limit code
    429,    # too many requests; general rate limit code
    444,    # no response; nginx specific, not clear if this actuall would go to the client
    502,    # bad gateway; retry to see if the gateway can re-establish connection
    503,    # service unavailable; retry to see if it comes back
    504     # gateway timeout; retry to see if it responds next time
]

# if you want to force a response encoding, set it here.  Will be used across the board unless
# overridden on the method call, so use carefully
HTTP_RESPONSE_ENCODING = None

# When streaming content, what is the maximum size download that is allowed.  The streaming code
# will first check the Content-Type header, then it will monitor the download until the size limit
# is exceeded.  Setting this to 0 means no size limit
HTTP_STREAM_MAX_SIZE = 0

# When streaming content, what size of download to cut off at.  This differs from the HTTP_STREAM_MAX_SIZE
# above in that all content downloaded before the cut off size is reached will be returned.
HTTP_STREAM_CUT_OFF = 0

# When streaming content, size of chunks to download by (this default is 250Kb)
HTTP_STREAM_CHUNK_SIZE = 262144


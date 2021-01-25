# when dates.format is called without a format argument, what format to use?
# FIXME: this is actually wrong - should really use the timezone correctly
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# date formats that we know about, and should try, in order, when parsing
DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",   # e.g. 2014-09-23T11:30:45Z
    "%Y-%m-%d",             # e.g. 2014-09-23
    "%d/%m/%y",             # e.g. 29/02/80
    "%d/%m/%Y",             # e.g. 29/02/1980
    "%d-%m-%Y",             # e.g. 01-01-2015
    "%Y.%m.%d",             # e.g. 2014.09.12
    "%d.%m.%Y",             # e.g. 12.9.2014
    "%d.%m.%y",             # e.g. 12.9.14
    "%d %B %Y",             # e.g. 21 June 2014
    "%d-%b-%Y",             # e.g. 31-Jul-13
    "%d-%b-%y",             # e.g. 31-Jul-2013
    "%d %b, %Y",            # e.g. 01 Dec, 1975
    "%b-%y",                # e.g. Aug-13
    "%B %Y",                # e.g. February 2014
    "%Y"                    # e.g. 1978
]
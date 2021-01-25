import re

# A UK postcode regular expression, which looks for the following forms:
# AA9A 9AA
# A9A 9AA
# A9 9AA
# A99 9AA
# AA9 9AA
# AA99 9AA
UKPCRX = "([a-zA-Z](?:(?:[a-zA-Z]?\d[a-zA-Z])|(?:\d{1,2})|(?:[a-zA-Z]\d{1,2}))\W?[0-9][a-zA-Z]{2})"

def extract_all(source):
    return re.findall(UKPCRX, source)



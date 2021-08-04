from random import randint
import string, uuid, json

def _random_string(shortest, longest, space=True):
    """
    Create a random string between the lengths of shortest and longest

    Strings are constructed out of the ascii letters and some spaces

    :param shortest: shortes the string should be
    :param longest: longest the string should be
    :return: a string
    """
    length = randint(shortest, longest)
    s = ""
    pool = string.ascii_letters
    pool = pool.replace(" ", "")
    if space:
        pool += "    "    # inject a few extra spaces, to increase their prevalence
    for i in range(length):
        l = randint(0, len(pool) - 1)
        s += pool[l]
    return s

def _select_n(arr, n):
    """
    Select N unique elements from the array

    :param arr: the array to select from
    :param n: the number of elements to select
    :return: a list of elements
    """
    selection = []

    idx = list(range(0, len(arr)))
    for x in range(n):
        if len(idx) == 0:
            break
        i = randint(0, len(idx) - 1)
        selection.append(arr[idx[i]])
        del idx[i]

    return selection

def _random_domain():
    return _random_string(2, 8, space=False).lower() + ".ac.uk"

def _random_name():
    return _random_string(10, 20)

def _random_postcode():
    return _random_string(3, 4, space=False).upper() + " " + _random_string(3, 3, space=False).upper()

def _random_strings():
    return _random_string(5, 10)

fields = [
    "domains", "name_variants", "postcodes", "strings"
]

randomisers = {
    "domains" : _random_domain,
    "name_variants" : _random_name,
    "postcodes" : _random_postcode,
    "strings" : _random_strings
}

configs = []
for i in range(70):
    fs = _select_n(fields, randint(1, len(fields)))
    cobj = {}
    for f in fs:
        cobj[f] = [randomisers[f]()]

    cobj["id"] = uuid.uuid4().hex
    cobj["repository"] = uuid.uuid4().hex
    configs.append(cobj)

with open("gen_repo_configs.json", "wb") as f:
    f.write(json.dumps(configs, indent=2))

s = ""
for i in range(70):
    s += uuid.uuid4().hex + "\n"
with open("gen_repo_keys.txt", "wb") as f:
    f.write(s)

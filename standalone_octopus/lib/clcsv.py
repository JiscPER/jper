import csv, codecs, re, os
from standalone_octopus.core import app
from io import StringIO
from io import IOBase


class CsvReadException(Exception):
    pass


class CsvStructureException(Exception):
    pass


class ClCsv():

    def __init__(self, file_path=None, writer=None,
                 output_encoding="utf-8", input_encoding="utf-8",
                 try_encodings_hard=True, fallback_input_encodings=None,
                 from_row=0, from_col=0, ignore_blank_rows=False,
                 input_dialect=csv.excel):
        """
        Class to wrap the Python CSV library. Allows reading and writing by column.
        :param file_path: A file object or path to a file. Will create one at specified path if it does not exist.
        """
        self.file_path = None
        self.output_encoding = output_encoding
        self.input_encoding = input_encoding

        # useful to know about this for any future work on encodings: https://docs.python.org/2.4/lib/standard-encodings.html
        if fallback_input_encodings is None and try_encodings_hard:
            fallback_input_encodings = ["cp1252", "cp1251", "iso-8859-1", "iso-8859-2", "windows-1252", "windows-1251", "mac_roman"]
        else:
            fallback_input_encodings = []
        self.fallback_input_encodings = fallback_input_encodings

        self.from_row = from_row
        self.from_col = from_col
        self.ignore_blank_rows = ignore_blank_rows
        self.input_dialect = input_dialect

        # Store the csv contents in a list of tuples, [ (column_header, [contents]) ]
        self.data = []

        # Get an open file object from the given file_path or file object
        if file_path is not None:
            if isinstance(file_path, IOBase):
                self.file_path = file_path.name
                # NOTE: if you have passed in a file object, it MUST work - as in, it must be set to
                # read the right encoding, and everything.  We will not try to parse it again if it
                # fails the first time.  If it is closed, you will also need to be sure to set the input_encoding.
                # All round - better if you just give us the file path
                self.file_object = file_path
                if self.file_object.closed:
                    self.file_object = open(self.file_object.name, 'r+', encoding=self.input_encoding)

                # explicitly read this file in
                self._read_file(self.file_object)
            else:
                self.file_path = file_path
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    self._read_from_path(file_path)
                else:
                    # If the file doesn't exist, create it.
                    self.file_object = open(file_path, 'w+', encoding=self.output_encoding)

        elif writer is not None:
            self.file_object = writer

    def _read_from_path(self, file_path):
        codes = [self.input_encoding] + self.fallback_input_encodings
        for code in codes:
            try:
                file_object = open(file_path, 'r+', encoding=code)
                self._read_file(file_object)
                self.file_object = file_object
                self.input_encoding = code
                return
            except CsvReadException as e:
                app.logger.info(str(e))
            except CsvStructureException as e:
                app.logger.info(str(e))
            except Exception as e:
                app.logger.info(str(e))
        # if we get to here, we were unable to read the file using any method
        raise CsvReadException("Unable to find a codec which can parse the file correctly")

    def _read_file(self, file_object):
        """
        Retrieve all of the information from the stored file using standard csv lib
        :return: Entire CSV contents, a list of rows (like the standard csv lib)
        """
        try:
            if file_object.closed:
                open(file_object.name, 'r+', encoding=self.input_encoding)

            reader = csv.reader(file_object, dialect=self.input_dialect)
            rows = []
            for row in reader:
                rows.append(row)
        except:
            raise CsvReadException("Unable to read file with {x} - likely an encoding problem (non fatal)".format(x=self.input_encoding))

        try:
            self._populate_data(rows)
            return rows
        except:
            raise CsvStructureException("Unable to read file into meaningful datastructure using encoding {x} (non fatal)".format(x=self.input_encoding))

    def headers(self):
        """
        Return the headers of all of the columns in the csv in the order that they appear
        :return: just the headers
        """
        return [h for h, _ in self.data]

    def set_headers(self, headers):
        for h in headers:
            c = self.get_column(h)
            if c is None:
                self.set_column(h, [])

    def columns(self):
        """
        Iterate over the columns in the csv in the order that they appear
        :return: a generator which yields columns
        """
        headers = self.headers()
        for h in headers:
            col = self.get_column(h)
            yield col

    def objects(self):
        """
        Iterate over the rows in the csv in the order they are provided, returned
        as objects keyed by the header row
        :return: a generator which yields objects
        """
        _, c = self.get_column(0)
        size = len(c)
        headers = self.headers()
        for i in range(size):
            obj = {}
            for h in headers:
                _, col = self.get_column(h)
                val = col[i]
                obj[h] = val
            yield obj

    def add_object(self, obj):
        for h, c in self.columns():
            v = obj.get(h)
            if v is not None:
                c.append(v)
            else:
                c.append("")

    def triples(self):
        """
        Iterate over every cell in the body of the sheet, taking the header and the
        first value in the row as the indices, and the value in the intersecting cell
        :return: (column header, row title, value)
        """
        _, c = self.get_column(0)
        headers = self.headers()

        vert = 0
        for y in c:
            for x in headers[1:]:
                _, col = self.get_column(x)
                yield x, y, col[vert]
            vert += 1

    def get_column(self, col_identifier):
        """
        Get a column from the CSV file.
        :param col_identifier: An int column index or a str column heading.
        :return: The column, as a { heading : [contents] } dict.
        """
        try:
            if type(col_identifier) == int:
                # get column by index
                return self.data[col_identifier]
            elif isinstance(col_identifier, str):
                # get column by title
                for col in self.data:
                    if col[0] == col_identifier:
                        return col
        except IndexError:
            return None

    def set_column(self, col_identifier, col_contents):
        """
        Set a column in the CSV file.
        :param col_identifier: An int column index or a str column heading.
        :param col_contents: The contents for the column
        """
        try:
            if type(col_identifier) == int:
                self.data[col_identifier] = col_contents
            elif isinstance(col_identifier, str):
                # set column by title.
                num = self.get_colnumber(col_identifier)
                if num is not None and type(col_contents) == list:
                    self.set_column(num, (col_identifier, col_contents))
                else:
                    raise IndexError

        except IndexError:
            # The column isn't there already; append a new one
            if type(col_identifier) == int:
                self.data.append(col_contents)
            elif isinstance(col_identifier, str):
                self.data.append((col_identifier, col_contents))

    def get_colnumber(self, header):
        """
        Return the column number of a given header
        :param header:
        :return: The column number
        """
        for i in range(0, len(self.data)):
            if self.data[i][0] == header:
                return i
        return None

    def get_rownumber(self, first_col_val):
        """
        Get the row number of a given first column value, or none if not found
        :param first_col_val:
        :return: The row number
        """

        try:
            (col_name, col_contents) = self.data[0]
            col_data = [col_name] + col_contents
            return col_data.index(first_col_val)
        except ValueError:
            return None

    def save(self, close=True):
        """
        Write and close the file.
        """
        rows = []
        # find out how many rows we're going to need to write
        max_rows = 0
        for _, cont in self.data:
            if len(cont) > max_rows:
                max_rows = len(cont)
        max_rows += 1 # add the header row

        for i in range(0, max_rows):
            row = []
            for (col_name, col_contents) in self.data:
                col_data = [col_name] + col_contents
                if len(col_data) > i:
                    row.append(col_data[i])
                else:
                    row.append("")
            rows.insert(i, row)

        # Remove current contents of file
        self.file_object.seek(0)
        self.file_object.truncate()

        # Write new CSV data
        writer = csv.writer(self.file_object)
        writer.writerows(rows)

        if close:
            self.file_object.close()

    def filename(self):
        if self.file_path is not None:
            return os.path.basename(self.file_path)
        return None

    def _is_empty(self, row):
        return sum([1 if c is not None and c != "" else 0 for c in row]) == 0

    def _populate_data(self, csv_rows):
        # Reset the stored data
        self.data = []
        if len(csv_rows) == 0:
            return

        # Add new data
        for i in range(self.from_col, len(csv_rows[0])):        # for each column
            col_data = []
            for row in csv_rows[self.from_row + 1:]:            # for each row
                if self.ignore_blank_rows:                      # conditionally ignore blank rows
                    row_segment = row[self.from_col:]
                    if self._is_empty(row_segment):
                        continue
                col_data.append(row[i])
            self.data.append((csv_rows[self.from_row][i], col_data))    # register along with the header


class BadCharReplacer:
    """
    Iterator that reads an encoded stream and replaces Bad Characters!

    The underlying reader MUST be returning UTF-8 encoded unicode strings
    """
    def __init__(self, f, charmap=None):
        self.reader = f

        self.charmap = charmap
        if self.charmap is None:
            self.charmap = {
                # unicode versions
                #'\xc2\x82' : ',',        # High code comma
                #'\xc2\x84' : ',,',       # High code double comma
                '\xc2\x85' : '...',      # Tripple dot
                #'\xc2\x88' : '^',        # High carat
                #'\xc2\x91' : '\x27',     # Forward single quote
                #'\xc2\x92' : '\x27',     # Reverse single quote
                #'\xc2\x93' : '\x22',     # Forward double quote
                #'\xc2\x94' : '\x22',     # Reverse double quote
                #'\xc2\x95' : ' ',
                #'\xc2\x96' : '-',        # High hyphen
                #'\xc2\x97' : '--',       # Double hyphen
                #'\xc2\x99' : ' ',
                #'\xc2\xa0' : ' ',
                #'\xc2\xa6' : '|',        # Split vertical bar
                #'\xc2\xab' : '<<',       # Double less than
                #'\xc2\xbb' : '>>',       # Double greater than
                #'\xc2\xbc' : '1/4',      # one quarter
                #'\xc2\xbd' : '1/2',      # one half
                #'\xc2\xbe' : '3/4',      # three quarters
                #'\xca\xbf' : '\x27',     # c-single quote
                #'\xcc\xa8' : '',         # modifier - under curve
                #'\xcc\xb1' : '',         # modifier - under line
            }

        self.pattern = '(' + '|'.join(list(self.charmap.keys())) + ')'
        self.rx = re.compile(self.pattern)

    def __iter__(self):
        return self

    def __next__(self):
        val = next(self.reader)

        def replace_chars(match):
            # this function returns the substitute value from the dict above
            char = match.group(0)
            return self.charmap[char]

        # if the rx does match, then do the substitution.  I think this is the fastest
        # way to do this
        if self.rx.search(val) is not None:
            return self.rx.sub(replace_chars, val)

        # if no match, return the unmodifed string
        return val

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = f # codecs.getreader("ISO-8859-2")(f) # FIXME: just for testing
        self.encoding = encoding

    def __iter__(self):
        return self

    def __next__(self):
        val = next(self.reader)
        raw = val.encode("utf-8")
        if raw.startswith(codecs.BOM_UTF8):
            raw = raw.replace(codecs.BOM_UTF8, '', 1)
        return raw


######################################################################

class SheetValidationException(Exception):
    def __init__(self, *args, **kwargs):
        super(SheetValidationException, self).__init__(*args)
        self.missing_header = kwargs["missing_header"]


class SheetWrapper(object):
    # map from values that will appear in the headers for real (i.e. human readable) to values
    # that should be used to refer to that column internally
    HEADERS = {}

    # Function(s) which are applied to normalise header keys (in order), to be used in the absence of the map
    # in the HEADERS dictionary
    HEADER_NORMALISER = []

    # list of headers that must be present such that validation of the sheet will succeed - use
    # the internal reference name, not the human name
    REQUIRED = []

    # order of headers as they should be saved - use the internal reference name, not the human
    # readable name
    OUTPUT_ORDER = []

    # values to set in cells where no value is provided when adding a row/object - use the internal
    # reference name as the key, and the default value as the value
    DEFAULT_VALUES = {}

    # should any empty string be represented as a None?  Is overridden by anything in the
    # DEFAULT_VALUES mapping
    EMPTY_STRING_AS_NONE = False

    # should values be trimmed before being returned.  This will be applied before the empty string
    # check, so can be used to return all whitespace-only strings as None too
    TRIM = True

    # coerce functions to apply to a value when it is read.  Use the internal reference name as the key,
    # and a function reference as the value
    COERCE = {}

    # coerce function(s) to apply to a value when it is read if it does not appear in the above COERCE list
    # executed in order
    DEFAULT_COERCE = []

    # values that should be treated as the empty string.  Use the internal reference name as the key
    # and a list of values in an array that should be ignored
    IGNORE_VALUES = {}

    def __init__(self, path=None, writer=None, spec=None):
        if path is not None:
            self._sheet = ClCsv(path, ignore_blank_rows=True)
        elif writer is not None:
            self._sheet = ClCsv(writer=writer, ignore_blank_rows=True)
            self._set_headers(spec)

    def _set_headers(self, spec=None):
        headers = []

        # only write headers which are in the object spec
        if spec is not None:
            oo = [x for x in self.OUTPUT_ORDER if x in spec]
        else:
            oo = self.OUTPUT_ORDER

        # write the headers in the correct order, ensuring they exist in the
        # Master spreadsheet header definitions
        for o in oo:
            found = False
            for k, v in self.HEADERS.items():
                if v == o:
                    headers.append(k)
                    found = True
                    break
            if not found:
                headers.append(o)

        # finally write the filtered, sanitised headers
        self._sheet.set_headers(headers)

    def _header_key_map(self, key):
        for k, v in self.HEADERS.items():
            if key.strip().lower() == k.lower():
                return v
        return None

    def _header_value_map(self, val):
        for k, v in self.HEADERS.items():
            if v.strip().lower() == val.lower():
                return k

    def _value(self, field, value):
        # first thing is, do we trim the value
        if self.TRIM:
            try:
                value = value.strip()
            except AttributeError:
                # this is a type that can't be stripped
                pass

        # we have the normalised value, so determine if it is to be ignored now
        if field in self.IGNORE_VALUES:
            if value in self.IGNORE_VALUES[field]:
                # if it's on the ignore list, re-write it to the empty string
                value = ""

        # now check to see if this is the empty string or None, and therefore if we need to return a default value
        if value is None or value == "":
            # the value in the cell is empty, so decide what to do
            #
            # if there is a default value, return that.
            if field in self.DEFAULT_VALUES:
                return self.DEFAULT_VALUES.get(field, "")

            # otherwise, if we return empty strings as none, return none
            if self.EMPTY_STRING_AS_NONE:
                return None

            # finally, otherwise, return the empty string
            return value

        # now we have a value which has content that we don't want to ignore, so see if we need to
        # coerce it at all.  If there's no specific coerce, check the default coerce
        if field in self.COERCE:
            fn = self.COERCE[field]
            value = fn(value)
        elif len(self.DEFAULT_COERCE) > 0:
            for fn in self.DEFAULT_COERCE:
                value = fn(value)

        # finally, return the value in whatever state it is now in
        return value

    def validate(self):
        ref = [self.HEADERS.get(h) for h in self._sheet.headers() if h in self.HEADERS]
        for r in self.REQUIRED:
            if r not in ref:
                header = self._header_value_map(r)
                raise SheetValidationException("One or more headings are missing from the sheet", missing_header=header)
        return True

    def objects(self, use_headers=True, beyond_headers=False):
        for o in self._sheet.objects():
            no = {}
            for key, val in o.items():
                hk = None
                if use_headers:
                    hk = self._header_key_map(key)
                if hk is None and beyond_headers:
                    hk = key
                    if len(self.HEADER_NORMALISER) > 0:
                        for fn in self.HEADER_NORMALISER:
                            hk = fn(hk)
                if hk is not None:
                    no[hk] = self._value(hk, val)
            yield no

    def add_object(self, obj):
        no = {}
        for k, v in obj.items():
            for k1, v1 in self.HEADERS.items():
                if k == v1:
                    no[k1] = self._value(k, v)
                    break
        self._sheet.add_object(no)

    def dataobjs(self, template, skip_on_error=False):
        for o in self.objects():
            do = template()
            try:
                do.populate(o)
                yield do
            except Exception as e:
                if skip_on_error:
                    continue
                raise e

    def add_dataobj(self, dobj, coerce=None):
        obj = {}
        for field in list(self.HEADERS.values()):
            # get the attribute for the header if it exists
            att = getattr(dobj, field, None)
            if att is None:
                continue            # Do it this way round to avoid further indentation

            # if the attribute exists, we now have its value
            coerced = False
            if coerce is not None:
                # we may have been passed a coerce function for this field
                fn = coerce.get(field)
                if fn is not None:
                    att = fn(att)
                    coerced = True

            # as a special favour, if the value is a list and we haven't been given
            # a coerce function, then join it with commas
            if isinstance(att, list) and not coerced:
                att = ", ".join(att)

            # now record the value in the object
            obj[field] = att

        # finally, add the object to the sheet
        self.add_object(obj)

    def filename(self):
        return self._sheet.filename()

    def save(self):
        self._sheet.save(close=False)


def get_csv_string(csv_row):
    '''
    csv.writer only writes to files - it'd be a lot easier if it
    could give us the string it generates, but it can't. This
    function uses StringIO to capture every CSV row that csv.writer
    produces and returns it.

    :param csv_row: A list of strings, each representing a CSV cell.
        This is the format required by csv.writer .
    '''
    csvstream = StringIO()
    csvwriter = csv.writer(csvstream, quoting=csv.QUOTE_ALL)
    # normalise the row - None -> "", and unicode > 128 to ascii
    csvwriter.writerow([str(c).encode("utf8", "replace") if c is not None else "" for c in csv_row])
    csvstring = csvstream.getvalue()
    csvstream.close()
    return csvstring

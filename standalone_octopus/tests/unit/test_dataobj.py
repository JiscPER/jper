from unittest import TestCase
from standalone_octopus.lib import dataobj

class CustomDO(dataobj.DataObj):
    pass

class InvalidDO(dataobj.DataObj):
    pass

class TestDataObj(dataobj.DataObj):
    def __init__(self, raw=None, expose_data=False):
        self._struct = {
            "fields" : {
                "title" : {"coerce" : "unicode"},
                "name" : {"coerce" : "unicode"},
                "exposed" : {"coerce" : "unicode"}
            },
            "objects" : ["objy", "theobj", "objdata"],
            "lists" : {
                "listy" : {"contains" : "object"},
                "thelist" : {"contains" : "object"},
                "listdata" : {"contains" : "object"}
            },
            "structs" : {
                "objy" : {
                    "fields" : {
                        "one" : {"coerce" : "unicode"},
                        "two" :{"coerce" : "unicode"}
                    }
                },
                "theobj" : {
                    "fields" : {
                        "one" : {"coerce" : "unicode"},
                        "two" :{"coerce" : "unicode"}
                    }
                },
                "listy" : {
                    "fields" : {
                        "three" : {"coerce" : "unicode"},
                        "four" :{"coerce" : "unicode"}
                    }
                },
                "thelist" : {
                    "fields" : {
                        "three" : {"coerce" : "unicode"},
                        "four" :{"coerce" : "unicode"}
                    }
                }
            }
        }

        self._properties = {
            "the_name" : ("name", None),
            "wrap_obj" : ("objy", dataobj.DataObj),
            "raw_obj" : ("objy", None),
            "wrap_list" : ("listy", dataobj.DataObj),
            "raw_list" : ("listy", None),

            "theobj" : ("theobj", None),
            "thelist" : ("thelist", None),

            "invalidobj" : ("invalidobj", CustomDO),
            "invalidlist" : ("invalidlist", CustomDO)
        }

        super(TestDataObj, self).__init__(raw=raw, expose_data=expose_data)

    @property
    def my_title(self):
        return self._get_single("title")

    @my_title.setter
    def my_title(self, val):
        self._set_single("title", val, coerce=dataobj.to_unicode())

    @property
    def my_object(self):
        return self._get_single("my_object")

    @my_object.setter
    def my_object(self, val):
        self._set_single("my_object", val)

    @property
    def my_list(self):
        return self._get_list("my_list")

    @my_list.setter
    def my_list(self, val):
        self._set_list("my_list", val)

class TestImport(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_delete_with_prune(self):
        d = dataobj.DataObj()
        d._set_single("one.two", "value")
        d._set_single("one.three.four.five", "value")
        d._delete("one.three.four.five")

    def test_02_construct(self):
        struct = {
            "fields" : {
                "one" : {"coerce" : "unicode"}
            },
            "objects" : [
                "three", "four", "five"
            ],
            "lists" : {
                "six" : {"contains" : "whatever"},
                "seven" : {"contains" : "field", "coerce" : "integer"},
                "eight" : {"contains" : "object"},
                "nine" : {"contains" : "object"}
            },
            "required" : ["one"],
            "structs" : {
                # Note there's no structure for three, so it can be anything
                "four" : {
                    "fields" : {
                        "alpha" : {"coerce" : "integer"}
                    }
                },
                "nine" : {
                    "fields" : {
                        "beta" : {"coerce" : "integer"}
                    }
                }
            }
        }

        coerce = {
            "unicode" : dataobj.to_unicode(),
            "integer" : dataobj.to_int()
        }

        obj = { "one" : "hello" }
        new = dataobj.construct(obj, struct, coerce)
        assert new["one"] == "hello"
        assert isinstance(new["one"], str)

        # try adding a disallowed field
        obj["two"]  = "world"

        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # try not providing a required field
        obj = {}
        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # try an unvalidated sub-object
        obj = {"one" : "hello"}
        obj["three"] = {"something" : "here"}
        new = dataobj.construct(obj, struct, coerce)
        assert new["three"]["something"] == "here"

        # and a validated sub-object
        obj["four"] = {"alpha" : "4"}
        new = dataobj.construct(obj, struct, coerce)
        assert new["four"]["alpha"] == 4

        # and a field that should be an object but isn't
        obj["five"] = "something here"
        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # a list where the list contains directive is broken
        del obj["five"]
        obj["six"] = ["6"]
        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # successfully coerce a list of field values
        del obj["six"]
        obj["seven"] = ["1", "1", "2", "3"]
        new = dataobj.construct(obj, struct, coerce)
        assert new["seven"] == [1, 1, 2, 3]

        # faile to coerce a list of field values
        obj["seven"] = ["a", "b", "walton-upon-thames"]
        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # list is supposed to contain an object but doesn't
        del obj["seven"]
        obj["eight"]  = ["not an object"]
        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # list contains an object but no validation required on its structure
        obj["eight"] = [{"an" : "object"}]
        new = dataobj.construct(obj, struct, coerce)
        assert new["eight"][0]["an"] == "object"

        # list contains an object which fails to validate
        obj["nine"] = [{"beta" : "whatever"}]
        with self.assertRaises(dataobj.DataStructureException):
            try:
                new = dataobj.construct(obj, struct, coerce)
            except dataobj.DataStructureException as e:
                print(str(e))
                raise e

        # list contains an object that does validate
        obj["nine"] = [{"beta" : 9}]
        new = dataobj.construct(obj, struct, coerce)
        assert new["nine"][0]["beta"] == 9

    def test_03_getattribute(self):
        do = TestDataObj({
            "title" : "Test Title",
            "name" : "Test Name",
            "exposed" : "Not",
            "objy" : {
                "one" : "first",
                "two" : "second"
            },
            "listy" : [
                {
                    "three" : "third",
                    "four" : "fourth"
                }
            ]
        })

        assert do.my_title == "Test Title"
        assert do.the_name == "Test Name"

        wo = do.wrap_obj
        assert isinstance(wo, dataobj.DataObj)
        assert wo.data.get("one") == "first"
        assert wo.data.get("two") == "second"

        ro = do.raw_obj
        assert isinstance(ro, dict)
        assert ro.get("one") == "first"
        assert ro.get("two") == "second"

        wl = do.wrap_list
        assert len(wl) == 1
        assert isinstance(wl[0], dataobj.DataObj)
        assert wl[0].data.get("three") == "third"
        assert wl[0].data.get("four") == "fourth"

        rl = do.raw_list
        assert len(rl) == 1
        assert isinstance(rl[0], dict)
        assert rl[0].get("three") == "third"
        assert rl[0].get("four") == "fourth"

        # check that we can't access the "exposed" attribute
        with self.assertRaises(AttributeError):
            do.exposed

    def test_04_expose_data(self):
        do = TestDataObj({
            "title" : "Test Title",
            "name" : "Test Name",
            "exposed" : "Yes",
            "objy" : {
                "one" : "first",
                "two" : "second"
            },
            "listy" : [
                {
                    "three" : "third",
                    "four" : "fourth"
                }
            ]
        }, expose_data=True)

        # try accessing the exposed field
        assert do.exposed == "Yes"

        # now do a more complex un-structured dataobj
        data = {
            "one" : {
                "two" : [
                    {
                        "three" : "four"
                    }
                ]
            }
        }
        do = dataobj.DataObj(data, expose_data=True)

        one = do.one

    # DataObjects may be in 4 configurations
    # 1. no struct, no expose_data
    # 2. no struct, expose_data
    # 3. struct, no expose_data
    # 4, struct, expose_data

    # For each field we set, we will want to try the following combinations
    # 1. If a field, just set a raw value
    # 2. If an object
    #   a. set a raw value
    #   b. set a vanilla DataObj
    #   c. set a custom DataObj that is valid (where properties are set)
    #   d. set a custom DataObj that is invalid (where properties are set)
    # 3. If a list
    #   a. set a raw value
    #   b. set a vanilla DataObj
    #   c. set a custom DataObj that is valid (where properties are set)
    #   d. set a custom DataObj that is invalid (where properties are set)

    # Furthermore, for each type (field, object, list) ensure that we can set through
    # 1. A class/object attribute
    # 2. A dynamic property (where properties are set)
    # 3. The internal data structure key name (when expose_data is on)

    # Finally, we also want to ensure that we can set previously unknown properties
    # on the object

    def test_05_setattr_no_struct_no_expose(self):

        # 1. no struct, no expose_data
        do = dataobj.DataObj(properties={
            "the_name" : ("name", None),
            "theobj" : ("theobj", None),
            "thelist" : ("thelist", None),
            "wrapobj" : ("wrapobj", None),
            "wraplist" : ("wraplist", None),
            "customobj" : ("customobj", CustomDO),
            "customlist" : ("customlist", CustomDO),
            "invalidobj" : ("invalidobj", CustomDO),
            "invalidlist" : ("invalidlist", CustomDO)
        })

        # Setting fields with raw values
        # 2. A dynamic property (where properties are set)
        do.the_name = "My Name"

        # Setting an object
        #   a. set a raw value
        do.theobj = {"one" : "first", "two" : "second" }
        #   b. set a vanilla DataObj
        do.wrapobj = dataobj.DataObj({"one" : "first", "two" : "second" })
        #   c. set a custom DataObj that is valid (where properties are set)
        do.customobj = CustomDO({"one" : "first", "two" : "second" })
        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.invalidobj = InvalidDO({"one" : "first", "two" : "second" })

        # Setting a list
        #   a. set a raw value
        do.thelist = [{"three" : "third", "four" : "fourth"}]
        #   b. set a vanilla DataObj
        do.wraplist = [dataobj.DataObj({"three" : "third", "four" : "fourth"})]
        #   c. set a custom DataObj that is valid (where properties are set)
        do.customlist = [CustomDO({"three" : "third", "four" : "fourth"})]
        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.invalidlist = [InvalidDO({"three" : "third", "four" : "fourth"})]

        # a previously unknown property
        do.whatever = "hello"

        # now do our checks
        assert do.the_name == "My Name"
        assert do.data.get("name") == "My Name"

        assert do.theobj == {"one" : "first", "two" : "second" }
        assert do.data.get("theobj") == {"one" : "first", "two" : "second" }

        assert do.wrapobj == {"one" : "first", "two" : "second" }
        assert do.data.get("wrapobj") == {"one" : "first", "two" : "second" }

        assert isinstance(do.customobj, CustomDO)
        assert do.customobj.data == {"one" : "first", "two" : "second" }
        assert do.data.get("customobj") == {"one" : "first", "two" : "second" }

        assert "invalidobj" not in do.data

        assert do.thelist == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("thelist") == [{"three" : "third", "four" : "fourth"}]

        assert do.wraplist == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("wraplist") == [{"three" : "third", "four" : "fourth"}]

        assert isinstance(do.customlist[0], CustomDO)
        assert do.customlist[0].data == {"three" : "third", "four" : "fourth"}
        assert do.data.get("customlist") == [{"three" : "third", "four" : "fourth"}]

        assert "invalidlist" not in do.data

        assert do.whatever == "hello"
        assert "whatever" not in do.data

    def test_06_setattr_no_struct_expose(self):

        # 2. no struct, expose_data
        do = dataobj.DataObj(
            {"one" : "first", "two" : {}, "three" : {}, "four" : [], "five" : []},
            properties={
                "the_name" : ("name", None),
                "theobj" : ("theobj", None),
                "thelist" : ("thelist", None),
                "wrapobj" : ("wrapobj", None),
                "wraplist" : ("wraplist", None),
                "customobj" : ("customobj", CustomDO),
                "customlist" : ("customlist", CustomDO),
                "invalidobj" : ("invalidobj", CustomDO),
                "invalidlist" : ("invalidlist", CustomDO)
            },
            expose_data=True
        )

        # Setting fields with raw values
        # 2. A dynamic property (where properties are set)
        do.the_name = "My Name"
        # 3. The internal data structure key name (when expose_data is on)
        do.one = "prime"

        # Setting an object
        #   a. set a raw value
        # on a defined property
        do.theobj = {"one" : "first", "two" : "second" }
        # on the internal data
        do.two = {"a" : "b"}
        #   b. set a vanilla DataObj
        # on a defined property
        do.wrapobj = dataobj.DataObj({"one" : "first", "two" : "second" })
        # on the internal data
        do.three = dataobj.DataObj({"a" : "b" })
        #   c. set a custom DataObj that is valid (where properties are set)
        do.customobj = CustomDO({"one" : "first", "two" : "second" })
        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.invalidobj = InvalidDO({"one" : "first", "two" : "second" })


        # Setting a list
        #   a. set a raw value
        # on a defined property
        do.thelist = [{"three" : "third", "four" : "fourth"}]
        # on the internal data
        do.four = [{"three" : "third", "four" : "fourth"}]
        #   b. set a vanilla DataObj
        # on a defined property
        do.wraplist = [dataobj.DataObj({"three" : "third", "four" : "fourth"})]
        # on the internal data
        do.five = [dataobj.DataObj({"three" : "third", "four" : "fourth"})]
        #   c. set a custom DataObj that is valid (where properties are set)
        do.customlist = [CustomDO({"three" : "third", "four" : "fourth"})]
        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.invalidlist = [InvalidDO({"three" : "third", "four" : "fourth"})]

        # a previously unknown property
        do.whatever = "hello"

        # now do our checks
        assert do.the_name == "My Name"
        assert do.data.get("name") == "My Name"

        assert do.one == "prime"
        assert do.data.get("one") == "prime"

        assert do.theobj == {"one" : "first", "two" : "second" }
        assert do.data.get("theobj") == {"one" : "first", "two" : "second" }

        assert isinstance(do.two, dataobj.DataObj)
        assert do.two.data == {"a" : "b"}
        assert do.two.a == "b"

        assert do.wrapobj == {"one" : "first", "two" : "second" }
        assert do.data.get("wrapobj") == {"one" : "first", "two" : "second" }

        assert isinstance(do.three, dataobj.DataObj)
        assert do.three.data == {"a" : "b"}
        assert do.three.a == "b"

        assert isinstance(do.customobj, CustomDO)
        assert do.customobj.data == {"one" : "first", "two" : "second" }
        assert do.data.get("customobj") == {"one" : "first", "two" : "second" }

        assert "invalidobj" not in do.data

        assert do.thelist == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("thelist") == [{"three" : "third", "four" : "fourth"}]

        assert isinstance(do.four[0], dataobj.DataObj)
        assert do.four[0].data == {"three" : "third", "four" : "fourth"}
        assert do.four[0].four == "fourth"
        assert do.data.get("four") == [{"three" : "third", "four" : "fourth"}]

        assert do.wraplist == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("wraplist") == [{"three" : "third", "four" : "fourth"}]

        assert isinstance(do.five[0], dataobj.DataObj)
        assert do.five[0].data == {"three" : "third", "four" : "fourth"}
        assert do.five[0].three == "third"
        assert do.data.get("five") == [{"three" : "third", "four" : "fourth"}]

        assert isinstance(do.customlist[0], CustomDO)
        assert do.customlist[0].data == {"three" : "third", "four" : "fourth"}
        assert do.data.get("customlist") == [{"three" : "third", "four" : "fourth"}]

        assert "invalidlist" not in do.data

        assert do.whatever == "hello"
        assert "whatever" not in do.data

    def test_07_setattr_struct_no_expose(self):
        # 3. struct, no expose_data
        do = TestDataObj()

        # Setting fields with raw values
        # 1. A class/object attribute
        do.my_title = "Title"
        # 2. A dynamic property (where properties are set)
        do.the_name = "My Name"

        # Setting an object
        #   a. set a raw value
        # an an object attribute
        do.my_object = {"one" : "first", "two" : "second" }
        # on a property
        do.theobj = {"one" : "first", "two" : "second" }

        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.wrap_obj = {"another" : "object"}
        #   c. set a custom DataObj that is valid (where properties are set)
        do.wrap_obj = {"one" : "first", "two" : "second" }

        # Set an attribute that is a defined property, but which is invalid because it refers to a
        # space outside the struct
        do.invalidobj = {"one" : "first", "two" : "second" }

        # Setting a list
        #   a. set a raw value
        # on an object attribute
        do.my_list = [{"three" : "third", "four" : "fourth"}]
        # on a property
        do.thelist = [{"three" : "third", "four" : "fourth"}]

        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.wrap_list = [{"something" : "invalid"}]
        #   c. set a custom DataObj that is valid (where properties are set)
        do.wrap_list = [{"three" : "third", "four" : "fourth"}]

        # Set an attribute that is a defined property, but which is invalid because it refers to a
        # space outside the struct
        do.invalidlist = [{"three" : "third", "four" : "fourth"}]

        # an arbitrary property
        do.whatever = "hello"

        # now do our checks
        assert do.my_title == "Title"
        assert do.data.get("title") == "Title"

        assert do.the_name == "My Name"
        assert do.data.get("name") == "My Name"

        assert do.my_object == {"one" : "first", "two" : "second" }
        assert do.data.get("my_object") == {"one" : "first", "two" : "second" }

        assert do.theobj == {"one" : "first", "two" : "second" }
        assert do.data.get("theobj") == {"one" : "first", "two" : "second" }

        assert do.wrap_obj.data == {"one" : "first", "two" : "second" }
        assert do.data.get("objy") == {"one" : "first", "two" : "second" }

        assert do.invalidobj == {"one" : "first", "two" : "second" }
        assert "invalidobj" not in do.data

        assert do.my_list == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("my_list") == [{"three" : "third", "four" : "fourth"}]

        assert do.thelist == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("thelist") == [{"three" : "third", "four" : "fourth"}]

        assert do.wrap_list[0].data == {"three" : "third", "four" : "fourth"}
        assert do.data.get("listy") == [{"three" : "third", "four" : "fourth"}]

        assert do.invalidlist == [{"three" : "third", "four" : "fourth"}]
        assert "invalidlist" not in do.data

        assert do.whatever == "hello"
        assert "whatever" not in do.data

    def test_08_setattr_struct_expose(self):
        # 4, struct, expose_data
        do = TestDataObj(expose_data=True)

        # Setting fields with raw values
        # 1. A class/object attribute
        do.my_title = "Title"
        # 2. A dynamic property (where properties are set)
        do.the_name = "My Name"
        # 3. The internal data structure key name (when expose_data is on)
        do.exposed = "open"

        # Setting an object
        #   a. set a raw value
        # an an object attribute
        do.my_object = {"one" : "first", "two" : "second" }
        # on a property
        do.theobj = {"one" : "first", "two" : "second" }
        # on the internal data
        do.objdata = {"one" : "first", "two" : "second" }

        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.wrap_obj = {"another" : "object"}
        #   c. set a custom DataObj that is valid (where properties are set)
        do.wrap_obj = {"one" : "first", "two" : "second" }

        # Set an attribute that is a defined property, but which is invalid because it refers to a
        # space outside the struct
        do.invalidobj = {"one" : "first", "two" : "second" }

        # Setting a list
        #   a. set a raw value
        # on an object attribute
        do.my_list = [{"three" : "third", "four" : "fourth"}]
        # on a property
        do.thelist = [{"three" : "third", "four" : "fourth"}]
        # on the internal data
        do.listdata = [{"three" : "third", "four" : "fourth"}]

        #   d. set a custom DataObj that is invalid (where properties are set)
        with self.assertRaises(AttributeError):
            do.wrap_list = [{"something" : "invalid"}]
        #   c. set a custom DataObj that is valid (where properties are set)
        do.wrap_list = [{"three" : "third", "four" : "fourth"}]

        # Set an attribute that is a defined property, but which is invalid because it refers to a
        # space outside the struct
        do.invalidlist = [{"three" : "third", "four" : "fourth"}]

        # an arbitrary property
        do.whatever = "hello"

        # now do our checks
        assert do.my_title == "Title"
        assert do.data.get("title") == "Title"

        assert do.the_name == "My Name"
        assert do.data.get("name") == "My Name"

        assert do.exposed == "open"
        assert do.data.get("exposed") == "open"

        assert do.my_object == {"one" : "first", "two" : "second" }
        assert do.data.get("my_object") == {"one" : "first", "two" : "second" }

        assert do.theobj == {"one" : "first", "two" : "second" }
        assert do.data.get("theobj") == {"one" : "first", "two" : "second" }

        assert do.objdata.data == {"one" : "first", "two" : "second" }
        assert do.data.get("objdata") == {"one" : "first", "two" : "second" }

        assert do.wrap_obj.data == {"one" : "first", "two" : "second" }
        assert do.data.get("objy") == {"one" : "first", "two" : "second" }

        assert do.invalidobj == {"one" : "first", "two" : "second" }
        assert "invalidobj" not in do.data

        assert do.my_list == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("my_list") == [{"three" : "third", "four" : "fourth"}]

        assert do.thelist == [{"three" : "third", "four" : "fourth"}]
        assert do.data.get("thelist") == [{"three" : "third", "four" : "fourth"}]

        assert do.listdata[0].data == {"three" : "third", "four" : "fourth"}
        assert do.data.get("listdata") == [{"three" : "third", "four" : "fourth"}]

        assert do.wrap_list[0].data == {"three" : "third", "four" : "fourth"}
        assert do.data.get("listy") == [{"three" : "third", "four" : "fourth"}]

        assert do.invalidlist == [{"three" : "third", "four" : "fourth"}]
        assert "invalidlist" not in do.data

        assert do.whatever == "hello"
        assert "whatever" not in do.data

    def test_09_silent_prune(self):
        data = {
            "one" : {
                "two" : "twice",
                "pruned" : "bye"
            },
            "three" : "third",
            "four" : [
                {
                    "five" : 5,
                    "cut" : -1
                }
            ],
            "nixed" : "outta here"
        }

        do = dataobj.DataObj(
            data,
            struct = {
                "fields" : {
                    "three" :{"coerce" : "unicode"}
                },
                "lists" : {
                    "four" : {"contains" : "object"}
                },
                "objects" : ["one"],

                "structs" : {
                    "one" : {
                        "fields" : {
                            "two" : {"coerce" : "unicode"}
                        }
                    },
                    "four" : {
                        "fields" : {
                            "five" : {"coerce" : "unicode"}
                        }
                    }
                }
            },
            construct_silent_prune=True,
            expose_data=True
        )

        assert do.one.two == "twice"
        with self.assertRaises(AttributeError):
            do.one.pruned

        assert do.three == "third"
        with self.assertRaises(AttributeError):
            do.nixed

        assert do.four[0].five == "5"
        with self.assertRaises(AttributeError):
            do.four[0].cut

    def test_10_add_struct(self):
        class A(dataobj.DataObj):
            def __init__(self):
                struct = {
                    "fields" : {
                        "one" : {"coerce" : "unicode"}
                    }
                }
                self._add_struct(struct)
                super(A, self).__init__()

        a = A()

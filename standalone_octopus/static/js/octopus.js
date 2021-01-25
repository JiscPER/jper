var octopus = {
    display : {
        hidden : {},

        hideOffScreen : function(selector) {
            var el = $(selector);
            if (selector in this.hidden) { return }
            this.hidden[selector] = {"position" : el.css("position"), "margin" : el.css("margin-left")};
            $(selector).css("position", "absolute").css("margin-left", -9999);
        },

        bringIn : function(selector) {
            var pos = this.hidden[selector].position;
            var mar = this.hidden[selector].margin;
            $(selector).css("position", pos).css("margin-left", mar);
            delete this.hidden[selector];
        }
    },

    string : {
        startsWith : function(str, prefix) {
           return str.lastIndexOf(prefix, 0) === 0
        },

        escapeHtml : function (unsafe) {
            return unsafe
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }
    },

    dataobj : {
        newDataObj : function(params) {
            var DataObj = function(params) {
                this.data = {};
                this.schema = {};
                this.allow_off_schema = false;
            }
            DataObj.prototype = octopus.dataobj.DataObjPrototype;
            var dobj = new DataObj();

            if (params) {
                if (params.raw) {
                    dobj.data = params.raw;
                }
                if (params.schema) {
                    dobj.schema = params.schema;
                }
                if (params.hasOwnProperty("allow_off_schema")) {
                    dobj.allow_off_schema = params.allow_off_schema;
                }
            }
            return dobj;
        },

        DataObjPrototype : {

            /////////////////////////////////////////////////
            // entry points to the data object - from outside you should only use these
            /////////////////////////////////////////////////

            set_field : function(field, value) {
                var cfg = this.schema[field];
                if (!cfg) {
                    if (!this.allow_off_schema) {
                        throw "no schema entry defined for field " + field;
                    } else {
                        cfg = {path: field, type: "single"};
                    }
                }
                if (cfg.type === "single") {
                    this.set_single(cfg, value);
                } else if (cfg.type === "list") {
                    this.set_list(cfg, value);
                }
            },

            get_field : function(field) {
                var cfg = this.schema[field];
                if (!cfg) {
                    if (!this.allow_off_schema) {
                        return undefined;
                    } else {
                        cfg = {path: field, type: "single"}
                    }
                }
                if (cfg.type === "single") {
                    return this.get_single(cfg);
                } else if (cfg.type === "list") {
                    return this.get_list(cfg, true);
                }
            },

            append_field : function(field, val) {
                var cfg = this.schema[field];
                if (!cfg) {
                    if (!this.allow_off_schema) {
                        throw "no schema entry defined for field " + field;
                    } else {
                        cfg = {path: field, type: "list"};
                    }
                }
                if (cfg.type === "list") {
                    this.add_to_list(cfg, val);
                } else {
                    throw "cannot append to a non-list field " + field;
                }
            },

            //////////////////////////////////////////////////////
            // getters and setters for individual values.
            // values will be coerced, etc.
            //////////////////////////////////////////////////////

            set_single : function(cfg, value) {
                // set some default values for the config
                if (!cfg.hasOwnProperty("allow_none")) {
                    cfg.allow_none = true;
                }

                // reject disallowed undefineds
                if (!value && !cfg.allow_none) {
                    throw "undefined not allowed at " + cfg.path;
                }

                // coerce the value if it not undefined
                if (cfg.coerce && value !== undefined) {
                    value = cfg.coerce(value);
                }

                // is the value one of the allowed values
                if (cfg.allowed_values && $.inArray(value, cfg.allowed_values) === -1) {
                    throw "value" + value + " is not permitted at " + cfg.path;
                }

                // check the value is in the allowed range
                if (cfg.allowed_range) {
                    var lower = cfg.allowed_range.lower;
                    var upper = cfg.allowed_range.upper;
                    if ((lower && value < lower) || (upper && value > upper)) {
                        throw "value " + value + " is outside the allowed range" + lower + " - " + upper;
                    }
                }

                // set the value at the path
                this.set_path(cfg.path, value);
            },

            get_single : function(cfg) {
                var val = this.get_path(cfg.path, cfg.default_value)

                if (cfg.coerce && val !== undefined) {
                    return cfg.coerce(val);
                } else {
                    return val;
                }
            },

            ////////////////////////////////////////////
            // getters and setters for points whose values are lists
            // the values in the supplied lists will be coerced, etc
            ////////////////////////////////////////////

            set_list : function(cfg, val) {
                for (var i = 0; i < val.length; i++) {
                    this.add_to_list(cfg, val[i]);
                }
            },

            add_to_list : function(cfg, val) {
                if (cfg.coerce && val !== undefined) {
                    val = cfg.coerce(val)
                }
                var current = this.get_list(cfg, true);
                current.push(val);
            },

            get_list : function(cfg, by_reference) {
                // get the raw value from the object
                var val = this.get_path(cfg.path, undefined);

                // if there is no value, but we want by-reference, then make a list, store it and return it
                if (val === undefined && by_reference) {
                    var mylist = [];
                    this.set_path(cfg.path, mylist);
                    return mylist;
                }

                // if there's no value and no interest in by-reference return an empty list
                if (val === undefined && !by_reference) {
                    return [];
                }

                // if the val is not a list don't return it
                if( Object.prototype.toString.call(val) !== '[object Array]') {
                    throw "Expecting a list at " + cfg.path + " but found " + Object.prototype.toString.call(val)
                }

                // if there is a value do we want to coerce?
                if (cfg.coerce) {
                    var coerced = [];
                    for (var i = 0; i < val.length; i++) {
                        coerced.push(cfg.coerce(val[i]));
                    }
                    if (by_reference) {
                        this.set_path(cfg.path, coerced)
                    }
                    return coerced;
                } else {
                    if (by_reference) {
                        return val;
                    } else {
                        return $.extend(true, {}, val);
                    }
                }
            },

            ///////////////////////////////////////////////////////
            // functions for directly writing to the underlying data structure
            ///////////////////////////////////////////////////////

            set_path : function(path, value) {
                var parts = path.split(".");
                var context = this.data;

                for (var i = 0; i < parts.length; i++) {
                    var p = parts[i];

                    if (!context.hasOwnProperty(p) && i < parts.length - 1) {
                        context[p] = {};
                        context = context[p];
                    } else if (context.hasOwnProperty(p) && i < parts.length - 1) {
                        context = context[p];
                    } else {
                        context[p] = value;
                    }
                }
            },

            get_path : function(path, default_value) {
                var parts = path.split(".");
                var context = this.data;

                for (var i = 0; i < parts.length; i++) {
                    var p = parts[i];
                    var d = i < parts.length - 1 ? {} : default_value;
                    context = context[p] !== undefined ? context[p] : d;
                }

                return context;
            }
        }
    }
};

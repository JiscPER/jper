/**********************************

a copy of the 0.0.2 version of holder

**********************************/

// function to bind change on delay, good for text search autosuggest
(function($) {
    $.fn.bindWithDelay = function( type, data, fn, timeout, throttle ) {
        var wait = null;
        var that = this;

        if ( $.isFunction( data ) ) {
            throttle = timeout;
            timeout = fn;
            fn = data;
            data = undefined;
        }

        function cb() {
            var e = $.extend(true, { }, arguments[0]);
            var throttler = function() {
                wait = null;
                fn.apply(that, [e]);
            };

            if (!throttle) { clearTimeout(wait); }
            if (!throttle || !wait) { wait = setTimeout(throttler, timeout); }
        }

        return this.bind(type, data, cb);
    };
})(jQuery);


// add extension to jQuery with a function to get URL parameters
jQuery.extend({
    getUrlVars: function() {
        var params = new Object;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for ( var i = 0; i < hashes.length; i++ ) {
            hash = hashes[i].split('=');
            if ( hash.length > 1 ) {
                if ( hash[1].replace(/%22/gi,"")[0] == "[" || hash[1].replace(/%22/gi,"")[0] == "{" ) {
                    hash[1] = hash[1].replace(/^%22/,"").replace(/%22$/,"");
                    var newval = JSON.parse(unescape(hash[1].replace(/%22/gi,'"')));
                } else {
                    var newval = unescape(hash[1].replace(/%22/gi,'"'));
                }
                params[hash[0]] = newval;
            }
        }
        return params;
    },
    getUrlVar: function(name){
        return jQuery.getUrlVars()[name];
    }
});


// Deal with indexOf issue in <IE9
// provided by commentary in repo issue - https://github.com/okfn/facetview/issues/18
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(searchElement /*, fromIndex */ ) {
        "use strict";
        if (this == null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 1) {
            n = Number(arguments[1]);
            if (n != n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n != 0 && n != Infinity && n != -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}

// a function for making a text into a link that when pressed adds the text to the search parameters
// requires an opts object with class, text value to display, and a list of further attrs
// attrs should include at least function which is the function name to trigger on click, which by default should be add
// can also then include attrs.filter and attrs.value to include a term filter, or attrs.query to include a query_string query
var searchify = function(opts) {
    var link = '<a class="' + opts.class + ' holder-function" ';
    for ( var o in opts.attrs ) {
        link += 'holder-' + o + '="' + opts.attrs[o] + '" ';
    }
    link += 'style="color:black;" alt="search this value" title="search this value" href="#">';
    link += opts.val + '</a>';
    return link;
}

// fuzzify the freetext search query terms with elasticsearch fuzzy match signifiers
var fuzzify = function(querystr, fuzz) {
    var rqs = querystr;
    if ( querystr.indexOf('*') == -1 && querystr.indexOf('~') == -1 && querystr.indexOf(':') == -1 && querystr.indexOf('"') == -1 && querystr.indexOf('AND') == -1 && querystr.indexOf('OR') == -1 ) {
        var optparts = querystr.split(' ');
        pq = "";
        for ( var oi = 0; oi < optparts.length; oi++ ) {
            var oip = optparts[oi];
            if ( oip.length > 0 ) {
                oip = oip + fuzz;
                fuzz == "*" ? oip = "*" + oip : false;
                pq += oip + " ";
            }
        };
        rqs = pq;
    };
    return rqs;
};

// an inefficient function to take dot notation strings and get / set the values
// but useful for passing dot notation strings in via the text box in the UI, or finding values by dot notation key names in ES responses
// example dot(options,'query.from',50) would set the options.query.from to 50 (or without the 50 just returns the value of it)
function dot(obj, s, val) {
    if ( typeof s === 'string' ) {
        return dot(obj,s.split('.'), val);
    } else if ( s.length === 1 && val === false ) {
        if ( isNaN(parseInt(s[0])) ) {
            if ( obj[s[0]] === undefined && typeof obj === 'object' && typeof obj !== null ) {
                for ( var pt in obj ) {
                    delete obj[pt][s[0]];
                }
                return true;
            } else {
                delete obj[s[0]]; // TODO check if this when a named key leaves a null or not
            }
        } else {
            obj.splice(parseInt(s[0]),1);
        }
        return true;
    } else if ( s.length === 1 && val !== undefined ) {
        if ( obj[s[0]] === undefined && typeof obj === 'object' && typeof obj !== null ) {
            for ( var pt in obj ) {
                obj[pt][s[0]] = val;
            }
            return true;
        } else {
            return obj[s[0]] = val;
        }
    } else if ( s.length === 0 ) {
        return obj;
    } else {
        if ( obj[s[0]] === undefined && typeof obj === 'object' && typeof obj !== null ) {
            var ret = [];
            for ( var pt in obj ) {
                ret.push(obj[pt][s[0]]);
            }
        } else {
            var ret = obj[s[0]];
        }
        return dot(ret,s.slice(1), val);
    }
}

function scrollin(elem) {
    var doctop = $(window).scrollTop();
    var docbottom = doctop + $(window).height();
    var top = elem.offset().top;
    if ( top < 150 ) top = 0;
    var bottom = top + elem.height();
    if ( bottom > docbottom || top <  doctop ) $('html, body').animate({ scrollTop: top - 10 }, 200);
}

(function($){
    $.fn.holder = function(options) {

        var defaults = {
            "what": "search...", // the name of what is being searched, to show in the search bar placeholder
            "class": "holder", // the class name used to identify holder properties for this instance on the page - DO NOT include the .
            "url": 'http://localhost:9200/_search', // the URL to send the query to (followed by type and datatype for the query)
            "type": "GET",
            "datatype": "JSONP",
            
            // define the starting query here - see ES docs. A filtered query is REQUIRED (empties are stripped for old ES compatibility)
            "defaultquery": { 
                "query": {
                    "filtered": {
                        "query": {
                            "bool": {
                                "must": [
                                ]
                            }
                        },
                        "filter": {
                            "bool": {
                                "must":[]
                            }
                        }
                    }
                }
            },
            "aggregations": undefined, // the aggregations can be defined separate from default query to save having to rewrite the whole thing
            "facets": undefined, // for older ES simplicity, facets can be defined too instead of aggregations
            "size": undefined, // size can be set on query start too, to save overwriting whole query (but from can't)
            
            "query": undefined, // this could be defined at startup if for some reason should be different from defaultquery
            "operator": "AND", // query operator param for the search box query params
            "fuzzify": "*", // fuzzify the search box query params if they are simple strings. Can be * or ~ or if false it will not run
            "executeonload": true, // run default search as soon as page loads
            "pushstate": true, // try pushing state to browser URL bar or not
            "scroll": false, // when results are scrolled to bottom retrieve the next set of results
            "after": {} // define callback functions to run after any other function (keyed by function name it should follow)
        };
        
        defaults.ui = function() {
            // if there is no search box on the page for this to run against, append a simple default one
            if ( !$('.' + options.class + '.holder-search').length ) {
                obj.append(' \
                    <div class="input-group" style="margin-left:-1px;margin-top:-1px;margin-bottom:-6px;margin-right:-2px;"> \
                        <div class="input-group-btn"><a class="btn btn-default holder holder-function" holder-function="prev" alt="previous" title="previous" style="height:50px;font-size:1.6em;" href="#">&lt;</a></div> \
                        <input type="text" class="form-control holder holder-search holder-function" holder-function="suggest" placeholder="search..." style="font-size:1.6em;height:50px;"> \
                        <div class="input-group-btn"><a class="btn btn-default holder holder-function" holder-function="next" alt="next" title="next" style="height:50px;font-size:1.6em;" href="#">&gt;</a></div> \
                    </div> \
                    <div class="holder holder-filters" style="margin-top:5px;"></div> \
                    <div class="holder holder-suggestions" style="margin-top:5px;"></div> \
                    <div class="holder holder-results"></div>'
                );
            }
            // bind the add to the search box explicitly with delay, if there is a suggest function defined
            if ( typeof options.suggest === 'function' ) {
                $('.' + options.class + '.holder-search').bindWithDelay('keyup',function(event) { options[$(this).attr('holder-function')](event,$(this)); }, 300);
                $('.' + options.class + '.holder-search').bind('focus', function(event) { $('.' + options.class + '.holder-options').show('fast'); });
                $('.' + options.class + '.holder-search').bindWithDelay('blur', function(event) { $('.' + options.class + '.holder-options').hide('fast'); }, 500);
            }
            // bind holder prev, next, from, to controllers (and any other functions that someone defines)
            $(document).on('click', 'a.' + options.class + '.holder-function', function(event) { options[$(this).attr('holder-function')](event,$(this)); } );
            $(document).on('change', 'input.' + options.class + '.holder-function', function(event) { options[$(this).attr('holder-function')](event,$(this)); } );
            $(document).on('change', 'textarea.' + options.class + '.holder-function', function(event) { options[$(this).attr('holder-function')](event,$(this)); } );
            // TODO bind holder option buttons
            // TODO bind holder sliders (once interpreting sliders into the query has also been done)
            // bind holder element toggle functions
            $('.' + options.class + '.holder-toggle').on('click',function(e) {
                e.preventDefault; 
                $('.' + options.class + '.holder-' + $(this).attr('holder-toggle')).toggle(); 
            });
            if ( typeof options.after.ui === 'function' ) options.after.ui();
        };
        
        // functions to be bound for paging the results
        defaults.prev = function(event) {
            if (event) event.preventDefault();
            if ( options.query.from !== 0 ) {
                options.query.from = options.query.from - options.query.size;
                if (options.query.from < 0) options.query.from = 0;
                options.execute();
            }
            if ( typeof options.after.prev === 'function' ) options.after.prev();
        };
        defaults.next = function(event) {
            if (event) event.preventDefault();
            if ( options.query.from + options.query.size < options.response.hits.total ) {
                options.query.from = options.query.from + options.query.size;
                options.execute();
            }
            if ( typeof options.after.next === 'function' ) options.after.next();
        };
        // current example does not actually use from and to boxes at the moment, but could be easily bound to these functions
        defaults.from = function() {
            options.query.from = parseInt($(this).val());
            options.execute();
            if ( typeof options.after.from === 'function' ) options.after.from();
        };
        defaults.to = function() {
            options.query.size = parseInt($(this).val()) - options.query.from;
            if (options.query.size < 0) options.query.size = parseInt($(this).val());
            options.execute();
            if ( typeof options.after.to === 'function' ) options.after.to();
        };

        // this function should be bound via holder-function to anything that updates the query
        // it should do whatever is required to add the new search param to the query and then run execute
        // for different UI elements other types of add function could be created, or this one could be overwritten
        // all it must do is somehow add to the options.query, then execute the new search
        // the render function that follows a response being received should render query and results into the UI
        // so if this addition adds something that does not affect the query or results, it may also be necessary to 
        // have a way to represent that on the page (or maybe not...)
        defaults.add = function(event,th) {
            if ( event ) event.preventDefault();
            scrollin($('.' + options.class + '.holder-search'));
            $('.' + options.class + '.holder-options').hide('fast');
            if (event) event.preventDefault();
            if (!th) th = $(this);
            options.query.from = 0;
            if ( th.attr('holder-query') ) {
                options.query.query.filtered.query.bool.must.push({"query_string": {"query": th.attr('holder-query')}});
            } else if ( th.attr('holder-filter') ) {
                var fq = {term:{}};
                fq.term[th.attr('holder-filter')] = th.attr('holder-value');
                if (options.query.query.filtered.filter === undefined) options.query.query.filtered.filter = {"bool": {"must":[]}};
                options.query.query.filtered.filter.bool.must.push(fq);
            } else {
                // this is a searchbox with value in it - append the value as a text search
                if ( th.val().indexOf('options.') === 0 ) {
                    // a loophole to directly pass options via the searchbox
                    var k = th.val().substring(8,th.val().indexOf('=')).replace(' ','');
                    var v = th.val().substring(th.val().indexOf('=')+1);
                    if (v.indexOf(' ') === 0) v = v.substring(1);
                    if (parseInt(v)) v = parseInt(v);
                    dot(options,k,v);
                } else if ( th.val().length ) {
                    var v = th.val();
                    if (options.fuzzify) v = fuzzify(v, options.fuzzify);
                    options.query.query.filtered.query.bool.must.push({"query_string":{"query": v }});
                }
                th.val("");
            }
            // TODO can add in other types of add functionality here, or new function to handle particular buttons can be written
            options.execute();
            if ( typeof options.after.add === 'function' ) options.after.add();
        }
        // this function should be bound to anything on the UI that removes something from the query
        // it should do whatever necessary to remove a part of the query and then run execute
        defaults.remove = function(event,th) {
            if (event) event.preventDefault();
            if (!th) th = $(this);
            var tgt = th.attr('holder-remove').replace('options.','');
            dot(options, tgt, false);
            th.remove(); // TODO should this look for a remove attribute to target a possible parent?
            options.query.from = 0;
            options.execute();
            if ( typeof options.after.remove === 'function' ) options.after.remove();
        };
        
        // this function should bind itself to the search box and do stuff on change, keypress, whatever, that gets suggestions back
        // and there is a default suggestions rendering in the defaults.results below too
        defaults.suggesting = false; // just tracks the suggesting state
        defaults.suggest = function(event,th) {
            if (event) event.preventDefault();
            if (!th) th = $(this);
            var code = (event.keyCode ? event.keyCode : event.which);
            if ( code == 13 ) {
                if ( options.query.query.filtered.query.bool.must.length !== 0 ) options.query.query.filtered.query.bool.must.splice(-1,1);
                options.add(event,th);
            } else {
                options.suggesting = true;
                options.query.from = 0;
                var v = th.val();
                if ( options.query.query.filtered.query.bool.must.length !== 0 ) options.query.query.filtered.query.bool.must.splice(-1,1);
                if ( v.length !== 0 ) {
                    if (options.fuzzify) v = fuzzify(v, options.fuzzify);
                    options.query.query.filtered.query.bool.must.push({"query_string":{"query": v }});
                }
                options.execute();
            }
            if ( typeof options.after.suggest === 'function' ) options.after.suggest();
        };
         
        // a function to scroll just the results for infinte page scrolling
        defaults.scrolling = false;
        defaults.scrollresults = function() {
          if ( options.query.from + options.query.size < options.response.hits.total ) {
            options.scrolling = true;
            options.query.from = options.query.from + options.query.size;
            options.execute();
          }
          if ( typeof options.after.scrollresults === 'function' ) options.after.scrollresults();
        }

        // a function that prepares the query based on the default, the first time it runs, if there is not one provided
        defaults.initialisequery = function() {
            if ( options.aggregations ) options.defaultquery.aggregations = options.aggregations;
            if ( options.facets ) options.defaultquery.facets = options.facets;
            options.query = $.extend(true, {}, options.defaultquery);
        }
        
        defaults.execute = function(event) {
            // show the loading placeholder (although one is not defined by default, it can be added anywhere to the page)
            $('.' + options.class + '.holder-loading').show();
            $('.' + options.class + '.holder-search').attr('placeholder','searching...');
            // get the current query
            if (options.query === undefined) options.initialisequery();
            // need a check for empty filters and queries for older versions of ES
            if ( options.query.query.filtered ) {
                if ( options.query.query.filtered.filter ) {
                    if ( options.query.query.filtered.filter.bool ) {
                        if ( options.query.query.filtered.filter.bool.must ) {
                            if ( options.query.query.filtered.filter.bool.must.length === 0 ) delete options.query.query.filtered.filter;
                        }
                    }
                }
                if ( options.query.query.filtered.query ) {
                    if ( options.query.query.filtered.query.bool ) {
                        if ( options.query.query.filtered.query.bool.must ) {
                            if ( options.query.query.filtered.query.bool.must.length === 0 ) {
                                options.query.query.filtered.query.bool.must = [{"match_all":{}}];
                            }
                        }
                    }
                }
            }
            var tq = options.query;
            if ( options.scrolling ) {
              delete tq.aggregations;
              delete tq.facets;
            }
            // TODO could simplify query if suggesting on facets, drop out ones that are not needed and set result size to zero
            // set the ajax options then execute
            var opts = {
                url: options.url,
                type: options.type,
                cache: false,
                //contentType: "application/json; charset=utf-8",
                dataType: options.datatype,
                // TODO: may have to pass this context in for the success object to run... check once online
                success: function(resp) {
                    //obj = $(this); TODO check if this works with or without passing the this context
                    $('.' + options.class + '.holder-loading').hide();
                    options.response = resp;
                    if (!options.suggesting && !options.scrolling) options.render(); // don't render the query if it was just a suggestion update
                    if ( typeof options.results === 'function' ) {
                        options.results(options.response);
                    } else if ( typeof options.results === 'object' ) {
                        if ( options.scrolling ) {
                          options.results.scroll(options.response);
                          options.scrolling = false;
                        } else if ( options.suggesting ) {
                          options.results.suggestions(options.response);                          
                          options.suggesting = false;
                        } else {
                          for ( var r in options.results ) {
                              if ( typeof options.results[r] === 'function') {
                                  options.results[r](options.response);
                              }
                          }
                        }
                    }
                },
                error: function(resp) {
                    // TODO catching errors from the API may need to be smarter than this...
                    console.log('Terribly sorry chappie! There has been an error when executing your query.');
                }
            };
            if ( options.type != 'POST' ) {
                opts.url += '?source=' + encodeURIComponent(JSON.stringify(tq));
            } else {
                // TODO: add the query as data to the ajax opts
            }
            if (options.username && options.password) opts.headers = { "Authorization": "Basic " + btoa(options.username + ":" + options.password) };
            $.ajax(opts);
            if ( typeof options.after.execute === 'function' ) options.after.execute();
        };

        defaults.render = function() {
            // render info about the query and what it found
            // TODO: maybe this should be shortened if on small screen?
            var found = options.what + ' found ';
            if (options.query.from !== 0) {
                found += options.query.from + ' to ' + (options.query.from + options.query.size);
            } else {
                options.query.size < options.response.hits.total ? found += options.query.size : found += options.response.hits.total;
            }
            found += ' of ' + options.response.hits.total;
            $('.' + options.class + '.holder-search').val("").attr('placeholder',found);
            if ( options.pushstate && (!options.suggesting && !options.scrolling ) ) {
                try {
                    if ('pushState' in window.history) window.history.pushState("", "search", '?source=' + JSON.stringify(options.query));
                } catch(err) {
                    console.log('pushstate not working! Although, note, it seems to fail on local file views these days...' + err);
                }
            }
            $('.' + options.class + '.holder-from').val(options.query.from);
            $('.' + options.class + '.holder-to').val(options.query.from + options.query.size);
            // TODO render the query values so they can be edited for next query
            $('.' + options.class + '.holder-filters').html("");
            for ( var q in options.query.query.filtered.query.bool.must ) {
                if ( options.query.query.filtered.query.bool.must[q].query_string ) {
                    var query = options.query.query.filtered.query.bool.must[q].query_string.query;
                    // TODO: what if this is not a query string? May need to check for other sorts of query - or is everything else in the filters?
                    var btn = '<a style="margin:5px;" class="btn btn-default ' + options.class + ' holder-function" holder-function="remove" holder-remove="options.query.query.filtered.query.bool.must.' + q + '"><b>X</b> ' + query + '</a>';
                    $('.' + options.class + '.holder-filters').append(btn);
                }
            }
            if ( options.query.query.filtered.filter ) {
                for ( var f in options.query.query.filtered.filter.bool.must ) {
                    var filter = options.query.query.filtered.filter.bool.must[f];
                    // TODO could be different kinds of filter - term, range, need to deal with each
                    var desc = ''
                    for (var k in filter.term) desc += k + ':' + filter.term[k];
                    var btn = '<a style="margin:5px;" class="btn btn-default ' + options.class + ' holder-function" holder-function="remove" holder-remove="options.query.query.filtered.filter.bool.must.' + f + '"><b>X</b> ' + desc + ' <i class="glyphicon glyphicon-remove></i></a>';
                    $('.' + options.class + '.holder-filters').append(btn);            
                }
            }
            if ( typeof options.after.render === 'function' ) options.after.render();
        };
        
        defaults.results = {
            suggestions: function(data) {
                if (data === undefined) data = options.response;
                $('.' + options.class + '.holder-suggestions').html('');
                for ( var f in data.aggregations ) {
                    var disp = '<div style="float:left;margin-right:10px;max-width:300px;">';
                    for ( var r in data.aggregations[f].buckets ) {
                        var j = data.aggregations[f].buckets[r];
                        disp += searchify({class: options.class, val: j.key + ' (' + j.doc_count + ')', attrs: {function: 'add', filter: f, value: j.key} });
                        disp += '<br>';
                    }
                    disp += '</div>';
                    $('.' + options.class + '.holder-suggestions').append(disp);
                }
            },
            default: function(data) {
                if (data === undefined) data=options.response;
                var res = '';
                res += '<div class="row"><div class="col-md-12' + options.class + ' holder-innerresults">';
                for ( var r in data.hits.hits ) {
                    res += '<p>' + JSON.stringify( data.hits.hits[r] ) + '</p>';
                }     
                res += '</div></div>';
                $('.' + options.class + '.holder-results').html(res);                  
                if ( typeof options.after.results === 'function' ) options.after.results();
            },
            scroll: function(data) {
              for ( var r in data.hits.hits ) {
                  $('.' + options.class + '.holder-innerresults').append('<p>' + JSON.stringify( data.hits.hits[r] ) + '</p>');
              }                  
            }
        };

        $.fn.holder.options = $.extend(defaults, options);
        var options = $.fn.holder.options;
        if (options.defaultquery.from === undefined) options.defaultquery.from = 0;
        if (options.defaultquery.size === undefined) options.size ? options.defaultquery.size = options.size : options.defaultquery.size = 10;

        var obj = $(this);
        return this.each(function() {
            options.ui();
            if ( $.getUrlVar('source') ) options.query = $.getUrlVar('source');
            if ( $.getUrlVar('q') ) {
                if (options.query === undefined) options.initialisequery();
                options.query.query.filtered.query.bool.must = [{"query_string": { "query": $.getUrlVar('q') } } ];
            }
            for ( var p in $.getUrlVars() ) {
                if (p !== 'source' && p !== 'q') options[p] = $.getUrlVar(p);
                options.execute();
            }
            if ( options.executeonload && JSON.stringify($.getUrlVars()) === "{}" ) options.execute();
            if ( options.scroll ) {
              $(window).scroll(function() {
                if ( !options.scrolling && $(window).scrollTop() == $(document).height() - $(window).height() ) {
                  options.scrollresults();
                }
            }); 
            }
        });

    };
    
    // define options here then they are written to above, then they become available externally
    $.fn.holder.options = {};
    
})(jQuery);
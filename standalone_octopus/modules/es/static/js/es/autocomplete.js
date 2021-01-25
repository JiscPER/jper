jQuery(document).ready(function($) {
    $.extend(octopus, {
        esac : {

            termAutocomplete : function(params) {
                var q = params.q;
                var size = params.size ? params.size : 10;
                var type = params.type;
                var success_callback = params.success ? params.success : function () {};
                var complete_callback = params.complete ? params.complete : function () {};
                var error_callback = params.error ? params.error : function () {};

                var url = octopus.config.es_term_endpoint + "/" + type

                // make the call to the autocomplete web service
                $.ajax({
                    type: "get",
                    url: url,
                    data: {q: q, size: size},
                    dataType: "jsonp",
                    success: success_callback,
                    complete: complete_callback,
                    error: error_callback
                });
            },

            bindTermAutocomplete : function(params) {
                var selector = params.selector;
                var minimumInputLength = params.minimumInputLength || 3;
                var placeholder = params.placeholder || "";
                var type = params.type;
                var format = params.format || function (result) {
                    return {id: result, text: result}
                };
                var allow_clear = params.allow_clear || true;
                var allow_any = params.allow_any || false;
                var multiple = params.multiple || false;

                function initSel(element, callback) {
                    var data = {id: element.val(), text: element.val()};
                    callback(data);
                }

                function successFunctionClosure(query) {
                    function successFunction(resp) {
                        var data = {results: []};
                        if (allow_any) {
                            data.results.push({id: query.term, text: query.term});
                        }
                        for (var i = 0; i < resp.length; i++) {
                            var r = resp[i];
                            data.results.push(format(r))
                        }
                        query.callback(data);
                    }

                    return successFunction
                }

                function queryFunction(query) {
                    octopus.esac.termAutocomplete({
                        q: query.term,
                        type: type,
                        success: successFunctionClosure(query)
                    })
                }

                var options = {
                    minimumInputLength: minimumInputLength,
                    placeholder: placeholder,
                    query: queryFunction,
                    initSelection: initSel,
                    allowClear: allow_clear
                };
                if (multiple) {
                    options["tags"] = []
                }
                $(selector).select2(options);
            },

            compoundAutocomplete: function (params) {
                var q = params.q;
                var size = params.size ? params.size : 10;
                var type = params.type;
                var success_callback = params.success ? params.success : function () {};
                var complete_callback = params.complete ? params.complete : function () {};
                var error_callback = params.error ? params.error : function () {};

                var url = octopus.config.es_compound_endpoint + "/" + type

                // make the call to the autocomplete web service
                $.ajax({
                    type: "get",
                    url: url,
                    data: {q: q, size: size},
                    dataType: "jsonp",
                    success: success_callback,
                    complete: complete_callback,
                    error: error_callback
                });
            },

            bindCompoundAutocomplete: function (params) {
                var selector = params.selector;
                var minimumInputLength = params.minimumInputLength || 3;
                var placeholder = params.placeholder || "";
                var type = params.type;
                var format = params.format || function (result) {
                    return {id: result.term, text: result.term}
                };
                var allow_clear = params.allow_clear || true;
                var allow_any = params.allow_any || false;
                var multiple = params.multiple || false;

                function initSel(element, callback) {
                    var data = {id: element.val(), text: element.val()};
                    callback(data);
                }

                function successFunctionClosure(query) {
                    function successFunction(resp) {
                        var data = {results: []};
                        if (allow_any) {
                            data.results.push({id: query.term, text: query.term});
                        }
                        for (var i = 0; i < resp.length; i++) {
                            var r = resp[i];
                            data.results.push(format(r))
                        }
                        query.callback(data);
                    }

                    return successFunction
                }

                function queryFunction(query) {
                    octopus.esac.compoundAutocomplete({
                        q: query.term,
                        type: type,
                        success: successFunctionClosure(query)
                    })
                }

                var options = {
                    minimumInputLength: minimumInputLength,
                    placeholder: placeholder,
                    query: queryFunction,
                    initSelection: initSel,
                    allowClear: allow_clear
                };
                if (multiple) {
                    options["tags"] = []
                }
                $(selector).select2(options);
            }
        }
    });
});

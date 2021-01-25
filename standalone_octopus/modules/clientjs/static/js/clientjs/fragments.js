jQuery(document).ready(function($) {
    $.extend(octopus, {
        fragments : {
            cache : {},

            cacheCallbackClosure : function(id, callback) {
                function fragCallback(html) {
                    octopus.fragments.cache[id] = html;
                    callback(html)
                }
                return fragCallback;
            },

            frag : function(params) {
                var frag_id = params.id;
                var callback = params.callback;

                if (octopus.fragments.cache[frag_id]) {
                    callback(octopus.fragments.cache[frag_id]);
                    return
                }

                $.ajax({
                    type: "GET",
                    dataType: "html",
                    url: octopus.config.fragments_endpoint + "/" + frag_id,
                    success: octopus.fragments.cacheCallbackClosure(frag_id, callback)
                });
            },

            preload : function(params) {
                // for the moment this is literally the same as calling "frag", but in the future
                // we may want to accept multiple frag ids, for example
                octopus.fragments.frag(params);
            },

            cached : function(params) {
                var frag_id = params.id;
                if (octopus.fragments.cache[frag_id]) {
                    return octopus.fragments.cache[frag_id]
                }
            }
        }
    });
});

jQuery(document).ready(function($) {

    // when the update button is clicked, disable it and show the waiting gif
    $("#register").click(function(event) {
        event.preventDefault();
        $("#register").attr("disabled", "disabled")
                    .html("Creating <img src='/static/images/white-transparent-loader.gif'>");
        $("#registration-details").submit();
    });

});

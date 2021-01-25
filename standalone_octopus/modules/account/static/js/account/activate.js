jQuery(document).ready(function($) {

    // when the update button is clicked, disable it and show the waiting gif
    $("#activate").click(function(event) {
        event.preventDefault();
        $("#activate").attr("disabled", "disabled")
                    .html("Activating <img src='/static/images/white-transparent-loader.gif'>");
        $("#activate-form").submit();
    });

});

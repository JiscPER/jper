jQuery(document).ready(function($) {

    // when the update button is clicked, disable it and show the waiting gif
    $("#update").click(function(event) {
        event.preventDefault();
        $("#update").attr("disabled", "disabled")
                    .html("Updating <img src='/static/images/white-transparent-loader.gif'>");
        $("#user_details").submit();
    });

    // when the delete button is clicked, check that the user is really sure
    $("#user_delete").submit(function(event) {
        var confirmed = confirm("Are you sure you want to delete your account?  This action cannot be undone.");
        if (confirmed) {
            return true;
        }
        return false;
    });
});

function resetSidebarToSigninState() {
    $.get("/information", function(data) {
        $('#status_info').html('<span name="not_oauthed" id="oauth_span">There is no data stored for this Google Account.</span>' + data);
        $("#left-lower").html("");
	});
}

$(document).ready(function() {
  $('#dimension_error').hide();
  $("#regenerate_status").hide();
  $("#delete_map_status").hide();
  $.get("static_map_html", function(data){
    if (data == "") {
      $("#delete_map_button").hide();
    }
    else {
      $('#static_instructions').show();
      $("#static_map").html(data);
    }
  });
  $('#fetching_span').hide();
  $('#delete_all_span').show();

  $('#delete_all_button').click(function() {
    $('#checkin_count').html("");
    $('#delete_all_span').html("deleting your data... <img src='static/spinner-small.gif'/>");
    $.get("/delete_data/user", function() {
      $("#hello img").attr("src", "/static/foursquare_girl.png"); //TODO also in constants.py - this duplication is ugly, but oh well for now
      $("#left-lower").html("");
      $("#regenerate").html("");
      $("#static_map").html("");
      $("#map_canvas").html("");
      resetSidebarToSigninState();
    });
  });

  $('#delete_map_button').click(function() {
    $("#delete_map_button").hide();
    $("#delete_map_status").show();
    $.get("delete_data/mapimage", function() {
      $("#static_map").html("");
      $("#delete_map_status").hide();
    });
  });
});

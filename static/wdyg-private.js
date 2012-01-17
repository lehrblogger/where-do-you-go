var map,
  tile_timeout,
  geocoder,
  level_offset = 0,
  uncacher = 0,
  user_is_ready_interval,
  map_is_done_interval;

function redrawTiles() {
  var myCopyright = new GCopyrightCollection("© ");
  myCopyright.addCopyright(new GCopyright('', new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)), 0,''));

  var tilelayer = new GTileLayer(myCopyright);
  tilelayer.getTileUrl = function(point, zoom) { 
		return "tile/" + $("#color_select").val() + uncacher + "/" + zoom + "/" + point.y + "," + point.x +".png";
	};
  tilelayer.isPng = function() { return true; };
  tilelayer.getOpacity = function() { return 1.0; };

  var tilelayeroverlay = new GTileLayerOverlay(tilelayer);
  map.addOverlay(tilelayeroverlay);
}
function createHeatMap(timeout) {
	map.clearOverlays();
	clearTimeout(tile_timeout);
	tile_timeout = setTimeout('redrawTiles();', timeout);
}

function resizeMapToWidthHeight(width, height) {
  var style_str = $("#map_canvas").attr('style');
  style_str = style_str.replace(/width: (\d+)px/, 'width: ' + width + 'px');
  style_str = style_str.replace(/height: (\d+)px/, 'height: ' + height + 'px');
  $("#map_canvas").attr('style', style_str);
  map.checkResize();
}

function updateLevels(offset) {
  var bounds = map.getBounds(),
    north = bounds.getNorthEast().lat(),
    east = bounds.getNorthEast().lng(),
    south = bounds.getSouthWest().lat(),
    west = bounds.getSouthWest().lng();
  level_offset += offset;
  $.get("/update_user_level/" + level_offset + "/" + north + "," + west + "/" + south + "," + east, function(){
    createHeatMap(500);
  });
}

function resetSidebarToSigninState() {
	$.get("/information", function(data) {
  	$('#status_info').html('<span name="not_oauthed" id="oauth_span"><a href="/go_to_foursquare"><img src="static/signinwith-foursquare.png"></a></span>' + data);
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
  if (($('#delete_all_span').attr('name') == 'started_ready') || ($('#oauth_span').attr('name') == 'not_oauthed')) {
    $('#fetching_span').hide();
    $('#delete_all_span').show();
  } else {
    $('#fetching_span').show();
    $('#delete_all_span').hide();
    user_is_ready_interval = setInterval(function() {
			uncacher++;
      $.ajax({
        type: "GET",
        url: "/user_is_ready/" + uncacher + "/",
        success: function(data){
          data_arr = data.split(',');
	   		  $('#checkin_count').html(data_arr[2] + ' check-ins mapped!');
	  		  if (data_arr[0] == 'True') {
            clearInterval(user_is_ready_interval);
            resetSidebarToSigninState();
            level_offset = 0;
            uncacher++;
            updateLevels(0);
          } else if (data_arr[1] == 'True') {
            clearInterval(user_is_ready_interval);
            $('#fetching_span').hide();
            $('#delete_all_span').show();
            level_offset = 0;
            uncacher++;
            updateLevels(0);
          } else if (data == 'error') {
            clearInterval(user_is_ready_interval);
          }
        }
      });
    }, 3000);
  }
  if (GBrowserIsCompatible() && is_logged_in) {
    map = new GMap2(document.getElementById("map_canvas"));
    map.setCenter(new GLatLng(global_centerlat, global_centerlng), global_zoom);
		
		GEvent.addListener(map, "zoomend", function(oldLevel, newLevel) {
			createHeatMap(1000);
		});
    var customUI = map.getDefaultUI();
    customUI.maptypes.satellite  = false;
    customUI.maptypes.hybrid  = false;
    customUI.maptypes.physical  = false;
    customUI.maptypes.normal = true;
    customUI.zoom.scrollwheel = false;
    customUI.controls.smallzoomcontrol3d = true;
    customUI.controls.scalecontrol   = false;
    map.setUI(customUI);
		map.disableDoubleClickZoom();
	  var mt = map.getMapTypes(); //http://groups.google.com/group/google-maps-api/browse_thread/thread/1fca64809be388a8
	  for (var i=0; i<mt.length; i++) {
	    mt[i].getMinimumResolution = function() {return 3;}; // note these must also be in constants.py
	    mt[i].getMaximumResolution = function() {return 18;};
	  }
    createHeatMap();
    geocoder = new GClientGeocoder();
  }

  $('#search_button').click(function() {
    geocoder.getLatLng(
      $('#search_field').val(),
      function(point) {
        if (!point) {
          alert(address + " not found");
        } else {
          map.setCenter(point);
          level_offset = 0;
          uncacher++;
          updateLevels(0);
        }
        $('#search_field').val('');
      });
  });

  $('#delete_all_button').click(function() {
    $('#checkin_count').html("");
    $('#delete_all_span').html("deleting your data... <img src='static/spinner-small.gif'/>");
    $.get("/delete_data/user", function() {
      map.clearOverlays();
      $("#hello img").attr("src", "/static/foursquare_girl.png"); //TODO also in constants.py - this duplication is ugly, but oh well for now
      $("#left-lower").html("");
      $("#regenerate").html("");
      resizeMapToWidthHeight(640, 640);
      $("#static_map").html("");
			resetSidebarToSigninState();
    });
  });

  $('#delete_map_button').click(function() {
    $("#delete_map_button").hide();
    $("#delete_map_status").show();
    $.get("delete_data/mapimage", function() {
      $("#static_map").html('');
      $("#delete_map_status").hide();
    });
  });

  $("#color_select").change(function() {
    $.get("/update_user_color/" + $("#color_select").val(), function(){
      createHeatMap(0);
    });
  });

  $('#size_button').click(function() { // http://net.tutsplus.com/tutorials/javascript-ajax/submit-a-form-without-page-refresh-using-jquery/
    $('#dimension_error').hide();
    var width = parseInt($("input#width_field").val());
    if (isNaN(width) || (0 >= width) || (640 < width)) {
      $("label#dimension_error").show();
      $("input#width_field").focus();
      return false;
    }
    var height = parseInt($("input#height_field").val());
    if (isNaN(height) || (0 >= height) || (640 < height)) {
      $("label#dimension_error").show();
      $("input#height_field").focus();
      return false;
    }
    resizeMapToWidthHeight(width, height);
  });

  $('#hot_button').click(function() {
    uncacher++;
    updateLevels(+1);
  });
  $('#cold_button').click(function() {
    uncacher++;
    updateLevels(-1);
  });

  $('#regenerate_button').click(function() {
    var bounds = map.getBounds(),
			north = bounds.getNorthEast().lat(),
      west = bounds.getSouthWest().lng(),
      center = map.getCenter(),
      center_lat = center.lat(),
      center_lng = center.lng(),
      zoom = map.getZoom(),
      size = map.getSize();
    $("#regenerate_button").hide();
    $("#regenerate_status").show();
    $.get("generate_static_map/" + size.width + "x" + size.height + "/" + zoom + "/" + center_lat + "," + center_lng + "/" + north + "," + west, function() {
      $.get("static_map_html", function(html_data){
      	$("#delete_map_button").show();
        $("#static_map").html(html_data);
				var img = $("#static_map_div img");
				map_is_done_interval = setInterval(function() {
				  $.ajax({
				    type: "GET",
				    url: "/map_is_done/",
				    success: function(done_data){
							img.attr('src', img.attr('src'));
							if (done_data == 'True') {
				        clearInterval(map_is_done_interval);
				        $("#regenerate_button").show();
				        $("#regenerate_status").hide();
				      }
				    }
				  });
				}, 3000);
      });
    });
  });
});

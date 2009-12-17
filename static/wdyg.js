var map;
var geocoder;

function createHeatMap(map) {
  var myCopyright = new GCopyrightCollection("© ");
  myCopyright.addCopyright(new GCopyright('', new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)), 0,''));

  var tilelayer = new GTileLayer(myCopyright);
  tilelayer.getTileUrl = function(point, zoom) { return "tile/" + $("#color_select").val() + "/" + zoom + "/" + point.y + "," + point.x +".png"; };
  tilelayer.isPng = function() { return true; };
  tilelayer.getOpacity = function() { return 1.0; };

  var tilelayeroverlay = new GTileLayerOverlay(tilelayer);
  map.addOverlay(tilelayeroverlay);
}

function resizeMapToWidthHeight(width, height) {
  var style_str = $("#map_canvas").attr('style');
  style_str = style_str.replace(/width: (\d+)px/, 'width: ' + width + 'px');
  style_str = style_str.replace(/height: (\d+)px/, 'height: ' + height + 'px');
  $("#map_canvas").attr('style', style_str);
  map.checkResize();
}

function updateLevels() {
  var bounds = map.getBounds();
  var north = bounds.getNorthEast().lat();
  var east = bounds.getNorthEast().lng();
  var south = bounds.getSouthWest().lat();
  var west = bounds.getSouthWest().lng();

  map.clearOverlays();
  $.get("/update_user_level/" + north + "," + west + "/" + south + "," + east, function(){
    createHeatMap(map);
  });
}

$(function() {
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

  if (GBrowserIsCompatible()) {
    map = new GMap2(document.getElementById("map_canvas"));
    map.setCenter(new GLatLng(global_centerlat, global_centerlng), global_zoom);

    var customUI = map.getDefaultUI();
    customUI.maptypes.satellite  = false;
    customUI.maptypes.hybrid  = false;
    customUI.maptypes.physical  = false;
    customUI.maptypes.normal = true;
    customUI.zoom.scrollwheel = false;
    customUI.controls.smallzoomcontrol3d = true;
    customUI.controls.scalecontrol   = false;
    map.setUI(customUI);

    createHeatMap(map);

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
          updateLevels();
        }
        $('#search_field').val('');
      });
  });

  $('#delete_all_button').click(function() {
    $('#checkin_count').html("<img src='static/spinner-small.gif'/>");
    $('#delete_all_span').html("deleting your data...");
    $.get("/delete_data/user", function(){
      map.clearOverlays();
      $("#options").html("");
      $("#regenerate").html("");
      resizeMapToWidthHeight(640, 640);
      $("#static_map").html("");
      $('#status_info').html('<a href="/go_to_foursquare">Login with Foursquare using OAuth</a><br/>');
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
    map.clearOverlays();
    $.get("/update_user_color/" + $("#color_select").val(), function(){
      createHeatMap(map);
    });
  });


  $('#size_button').click(function() { // http://net.tutsplus.com/tutorials/javascript-ajax/submit-a-form-without-page-refresh-using-jquery/
    $('#dimension_error').hide();

    var width = parseInt($("input#width_field").val());
    if (isNaN(width) || (0 >= width) || (640 < width)) {
      $("label#dimension_error").show();
      $("input#width_field").focus();
    }

    var height = parseInt($("input#height_field").val());
    if (isNaN(height) || (0 >= height) || (640 < height)) {
      $("label#dimension_error").show();
      $("input#height_field").focus();
    }

    resizeMapToWidthHeight(width, height);
  });

  $('#level_button').click(updateLevels);

  $('#regenerate_button').click(function() {
    var bounds = map.getBounds();
    var north = bounds.getNorthEast().lat();
    var west = bounds.getSouthWest().lng();

    var center = map.getCenter();
    var center_lat = center.lat();
    var center_lng = center.lng();

    var zoom = map.getZoom();
    var size = map.getSize();

    $("#regenerate_button").hide();
    $("#regenerate_status").show();
    $.get("generate_static_map/" + size.width + "x" + size.height + "/" + zoom + "/" + center_lat + "," + center_lng + "/" + north + "," + west, function() {
      $.get("static_map_html", function(data){
        $("#static_map").html(data);
        $("#delete_map_button").show();
        $("#regenerate_button").show();
        $("#regenerate_status").hide();
      });
    });
  });

  var mt = map.getMapTypes(); //http://groups.google.com/group/google-maps-api/browse_thread/thread/1fca64809be388a8
  for (var i=0; i<mt.length; i++) {
    mt[i].getMinimumResolution = function() {return 10;}; // note these must also be in constants.py
    mt[i].getMaximumResolution = function() {return 18;};
  }
});

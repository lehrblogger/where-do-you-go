var map;

function createHeatMap(map) {
  // Set up the copyright information. Each image used should indicate its copyright permissions
  var myCopyright = new GCopyrightCollection("© ");
  myCopyright.addCopyright(new GCopyright('lala', new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)), 0,'la la la'));

  // Create the tile layer overlay and implement the three abstract methods
  var tilelayer = new GTileLayer(myCopyright);
  tilelayer.getTileUrl = function(point, zoom) { return "tile/" + zoom + "/" + point.y + "," + point.x +".png"; };
  tilelayer.isPng = function() { return true; };
  tilelayer.getOpacity = function() { return 1.0; };

  var tilelayeroverlay = new GTileLayerOverlay(tilelayer);
  map.addOverlay(tilelayeroverlay);
}

$(document).ready(function() {
  $('.error').hide();
  $.get("static_map_html", function(data){
    $("#current_map").html(data);
    return false;
  });

  if (GBrowserIsCompatible()) {
    map = new GMap2(document.getElementById("map_canvas"));
    map.setCenter(new GLatLng(global_centerlat, global_centerlong), global_zoom);

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
  }

  var orig_delete_string = $('#delete_link').html();
  $('#delete_link').click(function() {
    $('#delete_link').html("Deleting data... please wait.");
    $.get("/delete_data/user", function(){
      map.clearOverlays();
      $("#current_map").html("");
      $('#status_info').html('<a href="/go_to_foursquare">OAuth with Foursquare</a><br/>');
      return false;
    });
    return false;
  });


  $("#color_menu form select").change(function() {
    map.clearOverlays();
    $.get("/update_user_color/" + $("#color_menu form select").val(), function(){
      createHeatMap(map);
      return false;
    });
    return false;
  });


  $('#submit_btn').click(function() { // http://net.tutsplus.com/tutorials/javascript-ajax/submit-a-form-without-page-refresh-using-jquery/
    $('.error').hide();

    var isInt = function(n){
        var reInt = new RegExp(/^-?\d+$/);
        if (!reInt.test(n)) {
            return false;
        }
        return true;
    }

    var width = parseInt($("input#width").val());
    if (isNaN(width) || (0 >= width) || (640 < width)) {
      $("label#width_error").show();
      $("input#width").focus();
      return false;
    }

    var height = parseInt($("input#height").val());
    if (isNaN(height) || (0 >= height) || (640 < height)) {
      $("label#height_error").show();
      $("input#height").focus();
      return false;
    }

    var style_str = $("#map_canvas").attr('style');
    style_str = style_str.replace(/width: (\d+)px/, 'width: ' + width + 'px');
    style_str = style_str.replace(/height: (\d+)px/, 'height: ' + height + 'px');
    $("#map_canvas").attr('style', style_str);
    map.checkResize();
    return false;
  });

  $('#generate_map').click(function() {
    var bounds = map.getBounds();
    var north = bounds.getNorthEast().lat();
    var west = bounds.getSouthWest().lng();

    var center = map.getCenter();
    var center_lat = center.lat();
    var center_long = center.lng();

    var zoom = map.getZoom();
    var size = map.getSize();

    $.get("generate_static_map/" + size.width + "x" + size.height + "/" + zoom + "/" + center_lat + "," + center_long + "/" + north + "," + west, function() {
      $.get("static_map_html", function(data){
        $("#current_map").html(data);
        return false;
      });
      return false;
    });
    return false;
  });

  var mt = map.getMapTypes(); //http://groups.google.com/group/google-maps-api/browse_thread/thread/1fca64809be388a8
  for (var i=0; i<mt.length; i++) {
          mt[i].getMinimumResolution = function() {return 3;}
          mt[i].getMaximumResolution = function() {return 20;}
  }
});
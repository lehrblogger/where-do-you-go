var map;

function initialize() {
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

    //addPlaceMarks(map);
    addHeatMap(map);
  }
}

function addHeatMap(map) {
  // Set up the copyright information. Each image used should indicate its copyright permissions
  var myCopyright = new GCopyrightCollection("© ");
  myCopyright.addCopyright(new GCopyright('lala', new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)), 0,'la la la'));

  // Create the tile layer overlay and implement the three abstract methods
  var tilelayer = new GTileLayer(myCopyright);
  tilelayer.getTileUrl = function(point, zoom) { return "tile/classic/" + zoom + "/" + point.y + "," + point.x +".png" };
  tilelayer.isPng = function() { return true;};
  tilelayer.getOpacity = function() { return 1.0; }

  var myTileLayer = new GTileLayerOverlay(tilelayer);
  map.addOverlay(myTileLayer);
}

function generateStaticMap() {
  var bounds = map.getBounds();
  var north = bounds.getNorthEast().lat();
  var west = bounds.getSouthWest().lng();

  var center = map.getCenter();
  var center_lat = center.lat();
  var center_long = center.lng();

  var zoom = map.getZoom();

  $.get("generate_static_map/" + zoom + "/" + center_lat + "," + center_long + "/" + north + "," + west);
}

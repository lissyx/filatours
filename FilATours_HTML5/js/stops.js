/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var map;
var stops;
var stopsIcon;

function showmap() {
  // Options of the map
  var options = {
    projection: new OpenLayers.Projection("EPSG:900913"),
    displayProjection: new OpenLayers.Projection("EPSG:4326"),
    units: "m",
    maxResolution: 156543.0339,
    maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34,
                     20037508.34, 20037508.34),
    controls: [
      new OpenLayers.Control.Attribution(),
      new OpenLayers.Control.TouchNavigation({
          dragPanOptions: {
              enableKinetic: true
          }
      }),
      new OpenLayers.Control.Zoom()
    ],
    numZoolLevels: 10,
  };

  // Initialiaze the map and the main layer
  map = new OpenLayers.Map('map', options);
  var mapnik = new OpenLayers.Layer.OSM("OpenStreetMap (Mapnik)");
  map.addLayers([mapnik]);

  stops = new OpenLayers.Layer.Markers( "Stops" );
  map.addLayer(stops);

  var size = new OpenLayers.Size(21,25);
  var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);

  stopsIcon = new OpenLayers.Icon('ext/OpenLayers/img/marker-green.png', size, offset);
}

function showstops() {
  var all = BusStops.getAllStops();
  for (var s in all) {
    var se = all[s];
    var stopPos = new OpenLayers.LonLat(se._longitude, se._latitude)
      .transform(map.options.displayProjection, map.options.projection);
    var mm = new OpenLayers.Marker(stopPos, stopsIcon.clone());
    stops.addMarker(mm);
  }
  map.zoomToExtent(stops.getDataExtent());
}

window.addEventListener('DOMContentLoaded', function() {
  showmap();
  showstops();
});

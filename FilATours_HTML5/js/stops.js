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

  stops = new OpenLayers.Layer.Vector("Stops", {
      isBaseLayer: false,
      features: [],
      visibility: true
  });
  map.addLayer(stops);

  stopsIcon = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
  stopsIcon.graphicWidth = 21;
  stopsIcon.graphicHeight = 25;
  stopsIcon.graphicXOffset = -(21/2);
  stopsIcon.graphicYOffset = -25;
  stopsIcon.externalGraphic = 'ext/OpenLayers/img/marker-green.png';
  stopsIcon.fillOpacity = 1;
}

function showstops() {
  var all = BusStops.getAllStops();
  var features = [];
  for (var s in all) {
    var se = all[s];
    var stopPos = new OpenLayers.LonLat(se._longitude, se._latitude)
      .transform(map.options.displayProjection, map.options.projection);
    features.push(new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(stopPos.lon, stopPos.lat), {}, stopsIcon));
  }
  stops.addFeatures(features);
  map.zoomToExtent(stops.getDataExtent());
}

window.addEventListener('DOMContentLoaded', function() {
  showmap();
  showstops();
});

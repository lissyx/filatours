/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var map;
var select;
var stops;
var stopsIcon;
var selectedStopsIcon;

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
  stops.events.on({
    "featureselected": onFeatureSelect,
    "featureunselected": onFeatureUnselect
  });
  map.addLayer(stops);

  select = new OpenLayers.Control.SelectFeature(stops,
    {
      clickout: true,
      toggle: false,
      multiple: false,
      hover: false
    });

  stopsIcon = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
  stopsIcon.graphicWidth = 21;
  stopsIcon.graphicHeight = 25;
  stopsIcon.graphicXOffset = -(21/2);
  stopsIcon.graphicYOffset = -25;
  stopsIcon.externalGraphic = 'ext/OpenLayers/img/marker-green.png';
  stopsIcon.fillOpacity = 1;

  selectedStopsIcon = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
  selectedStopsIcon.graphicWidth = 21;
  selectedStopsIcon.graphicHeight = 25;
  selectedStopsIcon.graphicXOffset = -(21/2);
  selectedStopsIcon.graphicYOffset = -25;
  selectedStopsIcon.externalGraphic = 'ext/OpenLayers/img/marker-blue.png';
  selectedStopsIcon.fillOpacity = 1
  select.selectStyle = selectedStopsIcon;

  map.addControl(select);
  select.activate();
}

function featureToHtml(feature) {
  var o = feature.data;
  return '<h1>' + o._name + '</h1>';
}

function onFeatureSelect(event) {
  var f = event.feature;
  var popup = new OpenLayers.Popup.FramedCloud("chicken",
    f.geometry.getBounds().getCenterLonLat(),
    new OpenLayers.Size(200, 100),
    featureToHtml(f),
    null,
    true,
    null);
  map.addPopup(popup, false);
}

function onFeatureUnselect(event) {
  var f = event.feature;
  if (f.popup) {
    map.removePopup(f.popup);
    f.popup.destroy();
    delete f.popup;
  }
}

function showstops() {
  var all = BusStops.getAllStops();
  var features = [];
  for (var s in all) {
    var se = all[s];
    var stopPos = new OpenLayers.LonLat(se._longitude, se._latitude)
      .transform(map.options.displayProjection, map.options.projection);
    features.push(
        new OpenLayers.Feature.Vector(
          new OpenLayers.Geometry.Point(stopPos.lon, stopPos.lat),
          se,
          stopsIcon));
  }
  stops.addFeatures(features);
  map.zoomToExtent(stops.getDataExtent());
}

window.addEventListener('DOMContentLoaded', function() {
  showmap();
  showstops();
});

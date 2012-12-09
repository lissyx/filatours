/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var all;
var map;
var select;
var stops;
var stopsIcon;
var selectedStopsIcon;
var selectActivity = null;

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

  map.events.on({
    "moveend": onMapMove
  });

  var tours = new OpenLayers.LonLat(0.683, 47.383)
      .transform(map.options.displayProjection, map.options.projection);
  map.setCenter(tours, 11, false, true);
}

function featureToHtml(feature) {
  var o = feature.data;
  var html = '<h1>' + o._name + '</h1>';
  var lines = BusLines.getLine(o._name);
  html += '<p>The following lines stops here: ' + lines.join(", ") + '.</p>';
  if (selectActivity != null) {
    html += '<p data-stopname="' + o._name + '" data-stopcity="' + o._city + '">';
    html += '<button class="recommended" name="departure">Departure</button>';
    html += '<button class="recommended" name="arrival">Arrival</button>';
    html += '</p>';
  }
  return html;
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
  var bDep = popup.contentDiv.querySelector('button[name="departure"]');
  if (bDep) {
    bDep.addEventListener('click', function(e) {
      console.debug("Got event: " + JSON.stringify(e));
      handleSelectEvent(bDep)
    });
  }
  var bArr = popup.contentDiv.querySelector('button[name="arrival"]');
  if (bArr) {
    bArr.addEventListener('click', function(e) {
      console.debug("Got event: " + JSON.stringify(e));
      handleSelectEvent(bArr)
    });
  }
}

function onFeatureUnselect(event) {
  var f = event.feature;
  if (f.popup) {
    map.removePopup(f.popup);
    f.popup.destroy();
    delete f.popup;
  }
}

function onMapMove(event) {
  var viewport = map.getExtent();
  var features = [];
  stops.removeAllFeatures();

  /* if we will display too much points, avoid */
  if (map.getZoom() <= 14) {
    document.getElementById('zoom-needed').style.display = 'block';
    return;
  }

  document.getElementById('zoom-needed').style.display = 'none';

  for (var s in all) {
    var se = all[s];
    var stopPos = new OpenLayers.LonLat(se._longitude, se._latitude)
      .transform(map.options.displayProjection, map.options.projection)
    if (viewport.containsLonLat(stopPos)) {
      features.push(
          new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(stopPos.lon, stopPos.lat),
            se,
            stopsIcon));
      }
  }
  stops.addFeatures(features);
}

window.addEventListener('DOMContentLoaded', function() {
  showmap();
  all = BusStops.getAllStops();
});

function handleSelectEvent(button) {
  var resp = {
    type: button.name,
    stop: {
      name: button.parentNode.dataset['stopname'],
      city: button.parentNode.dataset['stopcity']
    }
  };

  if (selectActivity != null) {
    selectActivity.postResult(resp);
    endSelect();
  }
}

function startSelect(request) {
  selectActivity = request;
}

function endSelect() {
  selectActivity = null;
}

window.onload = function() {
  if (!navigator.mozSetMessageHandler) {
    return;
  }

  navigator.mozSetMessageHandler('activity', function handler(activityRequest) {
    var activityName = activityRequest.source.name;
    if (activityName !== 'select-stop')
      return;
    startSelect(activityRequest);
    document.location.hash = 'stops-map';
  });
};

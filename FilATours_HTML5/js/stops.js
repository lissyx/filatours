/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var _ = window.navigator.mozL10n.get;

var all;
var map;
var select;
var stops;
var stopsIcon;
var selectedStopsIcon;
var selectActivity = null;

var selectNominatim;
var nominatimResults;
var nominatimResultsIcon;

var toursExtent;

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

  nominatimResults = new OpenLayers.Layer.Vector("NominatimResults", {
      isBaseLayer: false,
      features: [],
      visibility: true
  });
  nominatimResults.events.on({
    "featureselected": onFeatureSelectNominatim,
    "featureunselected": onFeatureUnselect
  });
  map.addLayer(nominatimResults);

  nominatimResultsIcon = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
  nominatimResultsIcon.graphicWidth = 21;
  nominatimResultsIcon.graphicHeight = 25;
  nominatimResultsIcon.graphicXOffset = -(21/2);
  nominatimResultsIcon.graphicYOffset = -25;
  nominatimResultsIcon.externalGraphic = 'ext/OpenLayers/img/marker-gold.png';
  nominatimResultsIcon.fillOpacity = 1;

  select = new OpenLayers.Control.SelectFeature([stops, nominatimResults],
    {
      clickout: true,
      toggle: false,
      multiple: false,
      hover: false
    });
  select.selectStyle = selectedStopsIcon;
  map.addControl(select);
  select.activate();

  map.events.on({
    "moveend": onMapMove
  });

  var tours = new OpenLayers.LonLat(0.683, 47.383)
      .transform(map.options.displayProjection, map.options.projection);
  map.setCenter(tours, 11, false, true);
  toursExtent = map.getExtent().transform(map.options.projection, map.options.displayProjection);
}

function featureToHtml(feature) {
  var o = feature.data;
  var html = '<h1>' + o._name + '</h1>';
  var lines = BusLines.getLine(o._name);
  html += '<p>' + _('lines-stops') + ': ' + lines.join(", ") + '.</p>';
  if (selectActivity != null) {
    html += '<p data-stopname="' + o._name + '" data-stopcity="' + o._city + '">';
    html += '<button class="recommended" name="departure">' + _('departure') + '</button>';
    html += '<button class="recommended" name="arrival">' + _('arrival') + '</button>';
    html += '</p>';
  }
  return html;
}

function NominatimFeatureToHtml(feature) {
  var o = feature.data;
  var html = '<h1>' + _('address') + '</h1>';
  html += '<p>' + o.display_name + '</p>';
  return html;
}

function onFeatureSelectNominatim(event) {
  var f = event.feature;
  var popup = new OpenLayers.Popup.FramedCloud("chicken",
    f.geometry.getBounds().getCenterLonLat(),
    new OpenLayers.Size(200, 100),
    NominatimFeatureToHtml(f),
    null,
    true,
    null);
  map.addPopup(popup, false);
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

function handleNominatim(obj) {
  var progress = document.getElementById('nominatim-search');
  var url = "http://nominatim.openstreetmap.org/search?";
  var params = "&format=json&bounded=1&limit=5";
  var query = obj.value;
  var bounds = toursExtent;
  params += "&viewbox=" + bounds.left + "," + bounds.bottom + "," + bounds.right + "," + bounds.top;
  var fullURL = url + "q=" + encodeURI(query) + params;
  console.log(fullURL);
  progress.style.visibility = "visible";

    var self = this;
    var xhr = new XMLHttpRequest({mozSystem: true});
    xhr.open("GET", fullURL, true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState == XMLHttpRequest.DONE) {
        var feats = JSON.parse(xhr.responseText);
        if (feats.length > 0) {
          showNominatimResults(feats);
        } else {
          alert(_('no-result'));
        }
        obj.blur();
        progress.style.visibility = "hidden";
      }
    };
    xhr.onerror = function() {
      progress.style.visibility = "hidden";
      alert(_("error-nominatim"));
    }
    xhr.send(null);
}

function showNominatimResults(feats) {
  var features = [];
  nominatimResults.removeAllFeatures();

  for (var s in feats) {
    var se = feats[s];
    var resultPos = new OpenLayers.LonLat(se.lon, se.lat)
      .transform(map.options.displayProjection, map.options.projection)
      features.push(
          new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(resultPos.lon, resultPos.lat),
            se,
            nominatimResultsIcon));
  }

  nominatimResults.addFeatures(features);

  var ex = nominatimResults.getDataExtent();
  map.zoomToExtent(ex);
}

window.addEventListener('DOMContentLoaded', function() {
  showmap();
  all = BusStops.getAllStops();
  var address = document.getElementById('address');
  if (address) {
    address.addEventListener('keydown', function(ev) {
      if (ev.keyCode == 13) {
        handleNominatim(address);
      }
    });
  }
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

function cancelSelectActivity() {
  var resp = {
    type: "",
    stop: {
      name: "",
      city: ""
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
    var mapback = document.getElementById('map-back');
    if (mapback) {
      mapback.setAttribute('href', '');
      mapback.addEventListener('click', function(e) {
        cancelSelectActivity();
        document.location = 'index.html#schedule';
      });
    }
  });
};

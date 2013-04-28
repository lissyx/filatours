/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var wid;
var prev = undefined;

var markers;
var curPosMarker;
var curPosIcon;

function whereami() {
  markers = new OpenLayers.Layer.Markers( "Markers" );
  map.addLayer(markers);

  var size = new OpenLayers.Size(21,25);
  var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
  curPosIcon = new OpenLayers.Icon('ext/OpenLayers/img/marker-gold.png', size, offset);
  curPosMarker = new OpenLayers.Marker(new OpenLayers.LonLat(0, 0), curPosIcon)
  markers.addMarker(curPosMarker);
}

function error(msg) {
  console.log("Geolocation error:" + msg);
}

function updateCurPosMarker(newPos) {
  markers.removeMarker(curPosMarker);
  curPosMarker = new OpenLayers.Marker(newPos, curPosIcon);
  markers.addMarker(curPosMarker);
}

function showPosition(ev) {
  updateStatus(_('updating-location'));
  var olc = new OpenLayers.LonLat(
        ev.coords.longitude,
        ev.coords.latitude)
      .transform(
        map.options.displayProjection,
        map.options.projection);
  map.setCenter(olc, 15);
  updateCurPosMarker(olc);

  if (prev) {
    var dist = distance(prev, ev.coords);
    console.debug("distance: " + dist);
    console.debug("accuracy: " + ev.coords.accuracy);
    if (dist <= ev.coords.accuracy && ev.coords.accuracy <= 100) {
      navigator.geolocation.clearWatch(wid);
      updateStatus(_('final-location'));
      window.setTimeout(function() {
        var s = document.getElementById('status-section');
        s.style.display = 'none';
      }, 10000);
    } else {
      updateStatus(_('waiting-better-location'));
    }
  }

  prev = ev.coords;
}

function distance(coords1, coords2) {
  var R = 6378000.0;

  // to rad
  var sourcelatitude = (Math.PI * coords2.latitude) / 180.0;
  var sourcelongitude = (Math.PI * coords2.longitude) / 180.0;

  var latitude = (Math.PI * coords1.latitude) / 180.0;
  var longitude = (Math.PI * coords1.longitude) / 180.0;

  // Distance en metre
  // http://www.zeguigui.com/weblog/archives/2006/05/calcul-de-la-di.php
  return (R * (Math.PI/2 - Math.asin( Math.sin(latitude) * Math.sin(sourcelatitude) + Math.cos(longitude - sourcelongitude) * Math.cos(latitude) * Math.cos(sourcelatitude))));
}

function findme() {
  wid = navigator.geolocation.watchPosition(showPosition, error);
}

function updateStatus(msg) {
  var s = document.getElementById('status');
  if (s) {
    s.innerHTML = msg;
  }
}

window.addEventListener('DOMContentLoaded', function() {
  updateStatus(_('waiting-location'));
  whereami();
  findme();
});

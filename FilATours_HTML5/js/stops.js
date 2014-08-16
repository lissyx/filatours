/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var _ = window.navigator.mozL10n.get;

var map;
var selectActivity = null;

var nominatimResults;
var nominatimResultsIcon;

var tours = [47.383, 0.683];
var toursBounds;

function showmap() {
  map = L.map('map', {
    center: tours,
    zoom: 11,
    closePopupOnClick: false
  });

  L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  var busStopIcon = L.AwesomeMarkers.icon({
    icon: 'car',
    markerColor: 'green',
    prefix: 'fa'
  });

  nominatimResultsIcon = L.AwesomeMarkers.icon({
    icon: 'star',
    markerColor: 'orange',
    prefix: 'fa'
  });

  var stops = L.markerClusterGroup();
  BusStops.getAllStops().forEach(function(stop) {
    var title = stop._name + " (" + stop._city + ")";
    var stopMark = L.marker(
      [ stop._latitude, stop._longitude ],
      { title: title, icon: busStopIcon }
    );
    stopMark._stop = stop;
    stopMark.addEventListener('click', onMarkerClick);
    stopMark.bindPopup(title);
    stops.addLayer(stopMark);
  });
  map.addLayer(stops);

  // Use featureGroup to benefit from getBounds()
  nominatimResults = L.featureGroup().addTo(map);

  toursBounds = map.getBounds();
}

function createButton(name, stopValues) {
  var btn = document.createElement('button');
  btn.className = 'recommended';
  btn.setAttribute('name', name);
  btn.textContent = _(name);

  btn.addEventListener('click', handleSelectEvent.bind(this, name, stopValues));
  return btn;
}

function buildStopElements(o) {
  var root = document.createElement('div');

  var title = document.createElement('h1');
  title.textContent = o._name;

  var p = document.createElement('p');
  var lines = BusLines.getLine(o._name);
  p.textContent = _('lines-stops') + ': ' + lines.join(", ");

  root.appendChild(title);
  root.appendChild(p);

  if (selectActivity) {
    var stopData = document.createElement('p');

    var btnDep = createButton('departure', o);
    var btnArr = createButton('arrival', o);

    stopData.appendChild(btnDep);
    stopData.appendChild(btnArr);

    root.appendChild(stopData);
  }

  return root;
}

function onMarkerClick(evt) {
  console.debug("Click:", evt);
  var stop = evt.target._stop;
  var elements = buildStopElements(stop);
  var popup = evt.target._popup;
  popup._content = elements;
}

function handleNominatim(obj) {
  var progress = document.getElementById('nominatim-search');
  var url = "http://nominatim.openstreetmap.org/search?";
  var params = "&format=json&bounded=1&limit=5";
  var query = obj.value;
  params += "&viewbox=" + toursBounds.getWest() + "," + toursBounds.getSouth() +
                    "," + toursBounds.getEast() + "," + toursBounds.getNorth();
  var fullURL = url + "q=" + encodeURI(query) + params;
  console.log(fullURL);
  progress.style.visibility = "visible";

  var xhr = new XMLHttpRequest();
  xhr.open("GET", fullURL, true);
  xhr.onreadystatechange = function() {
    if (xhr.readyState == XMLHttpRequest.DONE) {
      obj.blur();
      progress.style.visibility = "hidden";
      if (xhr.response.length > 0) {
        showNominatimResults(xhr.response);
      } else {
        alert(_('no-result'));
      }
    }
  };

  xhr.ontimeout = xhr.onabort = xhr.onerror = function() {
    progress.style.visibility = "hidden";
    alert(_("error-nominatim"));
  }

  xhr.responseType = 'json';
  xhr.send(null);
}

function showNominatimResults(feats) {
  nominatimResults.clearLayers();
  feats.forEach(function(feat) {
    var title = feat.display_name;
    var nominatimMarker =
      new L.marker([feat.lat, feat.lon], {
        icon: nominatimResultsIcon, title: title
      });
    nominatimMarker.bindPopup(title);
    nominatimResults.addLayer(nominatimMarker);
  });
  map.fitBounds(nominatimResults.getBounds());
}

function handleSelectEvent(type, stop) {
  var resp = {
    type: type,
    stop: {
      name: stop._name,
      city: stop._city
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

window.addEventListener('load', function() {
  showmap();
  var address = document.getElementById('address');
  if (address) {
    address.addEventListener('keydown', function(ev) {
      if (ev.keyCode == 13) {
        handleNominatim(address);
      }
    });
  }

  if (!navigator.mozSetMessageHandler) {
    return;
  }

  navigator.mozSetMessageHandler('activity', function handler(activityRequest) {
    var activityName = activityRequest.source.name;
    if (activityName !== 'select-stop') {
      return;
    }

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
});

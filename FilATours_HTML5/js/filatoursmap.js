/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var _ = window.navigator.mozL10n.get;

function FilAToursMap() {
  this.map = null;
  this.selectActivity = null;

  this.nominatimResults = null;
  this.nominatimResultsIcon = null;

  this.tours = [47.383, 0.683];
  this.toursBounds = null;
}

FilAToursMap.prototype = {
  init: function() {
    this.map = L.map('map', {
      center: this.tours,
      closePopupOnClick: false
    });

    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(this.map);

    var busStopIcon = L.AwesomeMarkers.icon({
      icon: 'car',
      markerColor: 'green',
      prefix: 'fa'
    });

    this.nominatimResultsIcon = L.AwesomeMarkers.icon({
      icon: 'star',
      markerColor: 'orange',
      prefix: 'fa'
    });

    var stops = L.markerClusterGroup({
      disableClusteringAtZoom: 15,
      maxClusterRadius: 40
    });
    BusStops.getAllStops().forEach((function(stop) {
      var title = stop._name + " (" + stop._city + ")";
      var stopMark = L.marker(
        [ stop._latitude, stop._longitude ],
        { title: title, icon: busStopIcon }
      );
      stopMark._stop = stop;
      stopMark.addEventListener('click', this.onMarkerClick.bind(this));
      stopMark.bindPopup(title);
      stops.addLayer(stopMark);
    }).bind(this));
    this.map.addLayer(stops);

    // Use featureGroup to benefit from getBounds()
    this.nominatimResults = L.featureGroup().addTo(this.map);

    // Set the bounds to cover the whole Tours area
    this.toursBounds = stops.getBounds();
    this.map.fitBounds(this.toursBounds);

    var address = document.getElementById('address');
    if (address) {
      var checkKeyCode = (function(ev) {
        if (ev.keyCode === 13) {
          this.handleNominatim(address);
        }
      }).bind(this);
      address.addEventListener('keydown', checkKeyCode);
    }

    return;
  },

  createButton: function(name, stopValues) {
    var btn = document.createElement('button');
    btn.className = 'recommended';
    btn.setAttribute('name', name);
    btn.textContent = _(name);

    btn.addEventListener('click',
      this.handleSelectEvent.bind(this, name, stopValues));
    return btn;
  },

  buildStopElements: function(o) {
    var root = document.createElement('div');

    var title = document.createElement('h2');
    title.textContent = o._name;

    var p = document.createElement('p');
    var lines = BusLines.getLine(o._name);
    p.textContent = _('lines-stops') + ': ' + lines.join(", ");

    root.appendChild(title);
    root.appendChild(p);

    if (this.selectActivity) {
      var stopData = document.createElement('p');

      var btnDep = this.createButton('departure', o);
      var btnArr = this.createButton('arrival', o);

      stopData.appendChild(btnDep);
      stopData.appendChild(btnArr);

      root.appendChild(stopData);
    }

    return root;
  },

  onMarkerClick: function(evt) {
    console.debug("Click:", evt);
    var stop = evt.target._stop;
    var elements = this.buildStopElements(stop);
    var popup = evt.target._popup;
    popup._content = elements;
  },
            
  handleNominatim: function(obj) {
    var progress = document.getElementById('nominatim-search');
    var url = "http://nominatim.openstreetmap.org/search?";
    var params = "&format=json&bounded=1&limit=5";
    var query = obj.value;
    params += "&viewbox=" + this.toursBounds.getWest() + "," + this.toursBounds.getSouth() +
                      "," + this.toursBounds.getEast() + "," + this.toursBounds.getNorth();
    var fullURL = url + "q=" + encodeURI(query) + params;
    console.log(fullURL);
    progress.style.visibility = "visible";

    var xhr = new XMLHttpRequest();
    xhr.open("GET", fullURL, true);
    xhr.onreadystatechange = (function() {
      if (xhr.readyState == XMLHttpRequest.DONE) {
        obj.blur();
        progress.style.visibility = "hidden";
        if (xhr.response.length > 0) {
          this.showNominatimResults(xhr.response);
        } else {
          alert(_('no-result'));
        }
      }
    }).bind(this);

    xhr.ontimeout = xhr.onabort = xhr.onerror = function() {
      progress.style.visibility = "hidden";
      alert(_("error-nominatim"));
    }

    xhr.responseType = 'json';
    xhr.send(null);
  },

  showNominatimResults: function(feats) {
    this.nominatimResults.clearLayers();
    feats.forEach((function(feat) {
      var title = feat.display_name;
      var nominatimMarker =
        new L.marker([feat.lat, feat.lon], {
          icon: this.nominatimResultsIcon, title: title
        });
      nominatimMarker.bindPopup(title);
      this.nominatimResults.addLayer(nominatimMarker);
    }).bind(this));
    this.map.fitBounds(this.nominatimResults.getBounds());
  },

  getActivityReply: function(type, stop) {
    return {
      type: type || '',
      stop: {
        name: stop._name || '',
        city: stop._city || ''
      }
    };
  },

  handleSelectEvent: function(type, stop) {
    if (this.selectActivity) {
      this.selectActivity.postResult(this.getActivityReply(type, stop));
      this.endSelect();
    }
  },

  cancelSelectActivity: function() {
    if (this.selectActivity) {
      this.selectActivity.postResult(this.getActivityReply(null, null));
      this.endSelect();
    }
  },

  startSelect: function(request) {
    this.selectActivity = request;
  },

  endSelect: function() {
    this.selectActivity = null;
  }
};

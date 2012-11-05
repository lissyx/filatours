/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var DialogSelectStop = function DialogSelectStop(stops, callback) {
  this._stops = stops;
  this._callback = callback;

  this.ensureClean();
  this.bindButtons();
  this.fillStops();
  this.showDialog();
};

DialogSelectStop.prototype.bindButtons = function() {
  var cancel = document.getElementById('cancel-select-stop');
  if (!cancel) {
    return;
  }

  var showMap = document.getElementById('show-map-select');
  if (!showMap) {
    return;
  }

  cancel.addEventListener('click', function() {
    document.location.hash = 'schedule';
  });

  showMap.addEventListener('click', function() {
    console.log("Showing on a map ...");
  })
};

DialogSelectStop.prototype.ensureClean = function() {
  var cont = document.getElementById('select-stop-list');
  if (!cont) {
    return;
  }

  while (cont.hasChildNodes()) {
    cont.removeChild(cont.lastChild);
  }
}

DialogSelectStop.prototype.fillStops = function() {
  var cont = document.getElementById('select-stop-list');
  if (!cont) {
    return;
  }

  for (var s in this._stops) {
    var se = this._stops[s];
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.textContent = se._name + ' (' + Math.floor(se._dist) + 'm)';
    a.private = se;
    a.addEventListener('click', this._callback);
    li.appendChild(a);
    cont.appendChild(li);
  }
};

DialogSelectStop.prototype.showDialog = function() {
  document.location.hash = '#select-stop';
};

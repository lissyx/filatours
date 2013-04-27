/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var GeolocFiller = function(target) {
  this._target = target;
  this._orig = document.location.hash;
  this._dialog = 'waiting-location';
}

GeolocFiller.prototype.startGeoloc = function() {
  document.getElementById(this._dialog)
    .addEventListener('click', this.geolocCancel.bind(this));
  this.showWaiting();
  this._cancel = false;
  navigator.geolocation.getCurrentPosition(
    this.geolocSuccess.bind(this),
    this.geolocError.bind(this));
};

GeolocFiller.prototype.geolocCancel = function(ev) {
  this._cancel = true;
  this.hideWaiting();
};

GeolocFiller.prototype.geolocSuccess = function(ev) {
  if (!this._cancel) {
    var stops = BusStops.getNearestStop(ev.coords);
    new DialogSelectStop(stops, this.geolocFill.bind(this));
  }
};

GeolocFiller.prototype.geolocError = function(ev) {
  this.hideWaiting();
  console.log("Geolocation error:" + ev);
};

GeolocFiller.prototype.geolocFill = function(ev) {
  var stop = ev.target.private;
  document.location.hash = 'schedule';
  var el = document.getElementById(this._target);
  if (!el) {
    return;
  }
  el.value = stop._name + ' (' + stop._city + ')';
  this.hideWaiting();
};

GeolocFiller.prototype.showWaiting = function() {
  document.location.hash = this._dialog;
};

GeolocFiller.prototype.hideWaiting = function() {
  document.location.hash = this._orig;
};

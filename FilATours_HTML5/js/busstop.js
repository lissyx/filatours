/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var BusStop = function(name, city, lat, lon) {
  this._name = name;
  this._city = city;
  this._latitude = lat;
  this._longitude = lon;
  this.init();
};

BusStop.prototype.init = function() {
};

function InvalidBusStopException () {

}

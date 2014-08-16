/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var _ = window.navigator.mozL10n.get;

function WhereAmI() {
  this.filatoursmap = null;
  this.locate = null;
  this.userStatus = null;
  this.goodAccuracy = 50;
}

WhereAmI.prototype = {
  init: function() {
    this.userStatus = document.getElementById('status');
    this.filatoursmap = new FilAToursMap();
    this.filatoursmap.init();
    this.locate = L.control.locate({
      showPopup: false,
      follow: true,
      enableHighAccuracy: true,
      onLocationError: this.locationError.bind(this)
    });
    this.locate.addTo(this.filatoursmap.map);
    this.showUserStatus(_('waiting-location'));
    this.locate.locate();
    this.filatoursmap.map.on('locationfound', this.locationFound.bind(this));
  },

  locationError: function(err) {
    console.debug("Location error:", err);
    this.showUserStatus(_('error-location'));
  },

  locationFound: function(location) {
    if (location.accuracy <= this.goodAccuracy) {
      this.hideUserStatus();
      this.locate.stopFollowing();
    } else {
      this.showUserStatus(_('waiting-better-location'));
    }
  },

  setElementVisible: function(element, visible) {
    var newVal = visible ? 'visible' : 'hidden';
    if (newVal !== element.style.visibility) {
      element.style.visibility = newVal;
      console.debug('Setting', element, newVal);
    }
  },

  showUserStatus: function(msg) {
    this.setElementVisible(document.querySelector('div.leaflet-control-attribution', false));
    this.userStatus.textContent = msg;
    this.setElementVisible(document.querySelector('#status-section'), true);
  },

  hideUserStatus: function() {
    this.setElementVisible(document.querySelector('div.leaflet-control-attribution', true));
    this.userStatus.textContent = '';
    this.setElementVisible(document.querySelector('#status-section'), false);
  }
};

var w = new WhereAmI();
window.addEventListener('localized', function() {
  w.init();
});

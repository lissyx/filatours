/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var m = new FilAToursMap();

window.addEventListener('localized', function() {
  m.init();

  if (!navigator.mozSetMessageHandler) {
    return;
  }

  navigator.mozSetMessageHandler('activity', function handler(activityRequest) {
    console.debug('Activity:', activityRequest);
    var activityName = activityRequest.source.name;
    if (activityName !== 'select-stop') {
      return;
    }

    m.startSelect(activityRequest);

    var mapback = document.getElementById('map-back');
    if (mapback) {
      mapback.removeAttribute('href');
      mapback.addEventListener('click', function(evt) {
        m.cancelSelectActivity();
      });
    }
  });
});

/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var m = new FilAToursMap();

window.addEventListener('localized', function() {
  var mapback = document.getElementById('map-back');
  if (mapback) {
    mapback.addEventListener('click', function(evt) {
      window.history.back();
    });
  }

  var pickStop = document.location.search.indexOf('pickStop');
  // Query string includes the '?', so indexOf cannot be lower than 1
  console.debug(pickStop);
  m.init(pickStop >= 1);
});

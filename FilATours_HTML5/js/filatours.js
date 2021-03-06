/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var _ = window.navigator.mozL10n.get;

function XHRHttpErrorException(code, body) {
  this.statusCode = code;
  this.httpBody = body;
}

function XHRTimeoutException() {
}

function XHRErrorException() {
}

function JourneysListNotFoundException() {
}

function JourneyDetailsNotFoundException() {
}

function JourneyDetailsUnexpectedElementsException() {
}

var FilBleu = (function FilBleu() {
  return {
    _api: "http://api.filatours.fr",
    _entry: undefined,
    _cookie: undefined,
    _journeys: new Array(),
    _scrapping: 'scrapping',
    _journeysList: 'journeys-list',
    _journeyDetails: 'journey-details',
    _journeyDetailsInfo: {},
    _currentJourneyDetailsId: undefined,
    _statuses: {
      'starting':           [10,  'initializing'],
      'start-get-cookie':   [20,  'search-get-cookie'],
      'end-get-cookie':     [40,  'search-got-cookie'],
      'start-get-journeys': [60,  'search-get-journeys'],
      'end-get-journeys':   [100, 'search-got-journeys'],
      'start-get-details':  [50,  'details-get-journey'],
      'end-get-details':    [100, 'details-got-journey'],
      'checking-cache':     [15,  'checking-cache'],
      'cache-hit':          [100, 'cache-hit'],
      'cache-miss':         [35,  'cache-miss']
    },

    XHR: function(entry, method, query, payload, callback) {
      var xhr = new XMLHttpRequest();
      var url = [ this._api, entry ].join('/');

      if (this._cookie) {
        url += '?cookie_name=' + this._cookie.name
             + '&cookie_value=' + this._cookie.value;
      }

      if (method === 'GET') {
        if (typeof query === 'object') {
          for (var o in query) {
            url += '&' + o + '=' + query[o];
          }
        }
      }

      xhr.onreadystatechange = (function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          if (xhr.status === 200) {
            callback(xhr);
          } else {
            this._entry = entry;
            this.handleNotFound();
          }
        }
      }).bind(this);

      xhr.timeout = 30*1000; // 30 secs
      xhr.ontimeout = (function() {
        this.handleException(new XHRTimeoutException());
      }).bind(this);

      xhr.onabort = xhr.onerror = (function() {
        this.handleException(new XHRErrorException());
      }).bind(this);

      xhr.open(method, url, true);
      xhr.responseType = 'json';

      if (method === 'POST') {
        xhr.setRequestHeader("Content-Type", "application/json; charset=UTF-8");
        if (typeof payload === 'object') {
          payload = JSON.stringify(payload);
        }
      }

      xhr.send(payload);
    },

    handleNotFound: function(xhr) {
      var ex;
      switch (this._entry) {
        case "search":
          ex = new JourneysListNotFoundException();
          break;
        case "details":
          ex = new JourneyDetailsNotFoundException();
          break;
        default:
          var status = xhr.status || -1;
          var text = xhr.response.error.message || xhr.statusText || 'Invalid XHR';
          ex = new XHRHttpErrorException(status, text);
      }
      this.handleException(ex);
    },

    getCookie: function(callback) {
      var handler = (function(xhr) {
        console.debug('XHR:', xhr);
        if (xhr.response.cookie) {
          this._cookie = xhr.response.cookie;
        }
        this.updateStatus('end-get-cookie');
        callback();
      }).bind(this);
      this.XHR('cookie', 'GET', null, null, handler);
      this.updateStatus('start-get-cookie');
    },

    postSearch: function(callback) {
      var d, a;
      try {
        d = BusStops.getMatchingStop(document.getElementById('departure').value);
        a = BusStops.getMatchingStop(document.getElementById('arrival').value);
      } catch (e) {
        this.handleException(e);
      }

      var search = {
        "departure": {
          "stop": d._name,
          "city": d._city
        },
        "arrival": {
          "stop": a._name,
          "city": a._city
        },
        "date": this.buildISODate(),
        "criteria": document.getElementById('crit').value,
        "sens": document.getElementById('sens').value
      }

      var handler = (function(xhr) {
        console.debug('XHR:', xhr);
        this.updateStatus('end-get-journeys');
        callback(xhr.response.journeys);
      }).bind(this);
      this.XHR('search', 'POST', null, search, handler);
      this.updateStatus('start-get-journeys');
    },

    postDetails: function(id, callback) {
      var handler = (function(xhr) {
        console.debug('XHR:', xhr);
        this.updateStatus('end-get-details');
        callback(xhr.response.journeysteps);
      }).bind(this);
      this.XHR('details', 'GET', {'journey': id}, null, handler);
      this.updateStatus('start-get-details');
    },

    pad: function(n) { return n < 10 ? '0' + n : n },

    getJSDate: function(str) {
      var ar = str.split("-");
      str = parseInt(ar[0]) + "-" + this.pad(parseInt(ar[1])) + "-" + this.pad(parseInt(ar[2]));
      return new Date(str);
    },

    getDate: function(str) {
      var date = this.getJSDate(str);
      return date.getFullYear() + '-' +
        this.pad(date.getMonth() + 1) + '-' +
        this.pad(date.getDate());
    },

    getHour: function(str) {
      return parseInt(str.split(':')[0], 10);
    },

    getMin: function(str) {
      return parseInt(str.split(':')[1], 10);
    },

    buildISODate: function() {
      var date = this.getDate(document.getElementById('date').value);
      var hour = this.getHour(document.getElementById('time').value);
      var min = this.getMin(document.getElementById('time').value);
      return date + 'T' + hour + ':' + min + ':00';
    },

    buildTime: function(datetime) {
      var retval = "";
      var hours = -1;
      var minutes = -1;
      switch(typeof datetime) {
        case "number":
          hours = parseInt(datetime / 3600);
          minutes = parseInt((datetime - (hours * 3600)) / 60);
          break;
        case "string":
          datetime = new Date(datetime);
        case "object":
          if (!(datetime instanceof Date)) {
            throw new Error("Unexpected date type: " + datetime);
          }
          hours = datetime.getHours();
          minutes = datetime.getMinutes();
          break;
      }

      return {h: hours, m: minutes};
    },

    formatTime: function(time) {
      var hm = this.buildTime(time);
      var retval = "";
      if (hm.h > -1) {
        retval += this.pad(hm.h) + "h";
      }
      return retval + this.pad(hm.m);
    },

    formatDuration: function(duration) {
      var hm = this.buildTime(duration);
      var retval = "";
      if (hm.h > 0) {
        retval += this.pad(hm.h) + "h";
      }
      return retval + this.pad(hm.m) + "min";
    },

    getJourney: function() {
      this.updateStatus('starting');
      this._journeyDetailsInfo = {};
      this.getCookie((function() {
        this.postSearch((function(journeys) {
          console.debug("Got list:", journeys);
          this._journeys = journeys.list;
          this.showJourneysList();
        }).bind(this));
      }).bind(this));
    },

    showJourneysList: function() {
      this.ensureClean('journeys-list-container');
      document.getElementById('close-journeys-list')
        .addEventListener('click', function(ev) {
          document.location.hash = 'schedule';
        });
      document.location.hash = this._journeysList;
      var c = document.getElementById('journeys-list-container');
      if (!c) {
        return;
      }

      for (var j in this._journeys) {
        var bj = this._journeys[j];
        var li = document.createElement('li');
        li.className = 'journey';
        var a = document.createElement('a');
        a.className = 'journey';
        a.textContent =
          this.formatTime(bj.departure) + ' - ' + this.formatTime(bj.arrival) +
          ' (' + this.formatDuration(bj.duration) + ')';

        var licont = document.createElement('li');
        licont.style.display = 'none';
        var details = document.createElement('span');
        details.textContent = _('connections') + ': ' + bj.connections;
        details.dataset['link'] = bj.details;

        details.addEventListener('click', (function(ev) {
          this.getJourneyDetails(ev.target.dataset['link']);
        }).bind(this));

        a.addEventListener('click', function(ev) {
          var pnode = ev.target.parentNode;
          var snode = ev.target.nextSibling;
          if (snode.style.display == 'none') {
            snode.style.display = 'block';
            pnode.className = 'journey journey-details';
          } else {
            snode.style.display = 'none';
            pnode.className = 'journey';
          }
        });

        licont.appendChild(details);

        li.appendChild(a);
        li.appendChild(licont);
        c.appendChild(li);
        console.debug(bj);
      }
    },

    getJourneyDetails: function(link) {
      this.updateStatus('starting');
      this.updateStatus('checking-cache');
      var cache = this._journeyDetailsInfo[link];
      console.debug(cache);
      if (cache != undefined) {
        this.updateStatus('cache-hit');
        this.showJourneyDetails(link);
        return;
      }

      this.updateStatus('cache-miss');
      this._journeyDetailsInfo[link] = new Array();
      this.postDetails(link, (function(steps) {
        console.debug("Got steps:", steps);
        this._journeyDetailsInfo[link] = steps.list;
        this.showJourneyDetails(link);
      }).bind(this));
    },

    addOneStep: function(step, indic, title, detailsText) {
      var c = document.getElementById('journey-details-container');

      var li = document.createElement('li');
      li.className = 'journeypart journey' + step.type;

      var a = document.createElement('a');
      a.className = 'journeypart journey' + step.type;

      if (indic && step.type === 'indication') {
        li.className += ' journey' + indic.type;
        a.className += ' journey' + indic.type;
      }

      var cont = document.createElement('p');
      cont.style.display = 'none';
      var details = document.createElement('span');

      a.textContent = title;
      details.innerHTML = detailsText;

      a.addEventListener('click', function(ev) {
        var pnode = ev.target.parentNode;
        var snode = ev.target.nextSibling;
        if (snode.style.display == 'none') {
          snode.style.display = 'block';
        } else {
          snode.style.display = 'none';
        }
      });

      cont.appendChild(details);

      li.appendChild(a);
      li.appendChild(cont);
      c.appendChild(li);
    },

    showJourneyDetails: function(id) {
      this._currentJourneyDetailsId = id;
      this.ensureClean('journey-details-container');
      document.location.hash = this._journeyDetails;

      for (var si in this._journeyDetailsInfo[id]) {
        var step = this._journeyDetailsInfo[id][si];
        console.debug("Step:", step);

        switch(step.type) {
          case 'indication':
            for (var indId in step.indic) {
              var stepInd = step.indic[indId];
              var detailsText, title;

              switch(stepInd.type) {
                case 'mount':
                  title = this.formatTime(step.time.start) + ': ' + stepInd.stop;
                  detailsText = '<strong>' + _('line') + '</strong>: ' +
                                stepInd.line + '<br />' +
                                '<strong>' + _('direction') + '</strong>: ' +
                                stepInd.direction;
                  break;
                case 'umount':
                  title = this.formatTime(step.time.end) + ': ' + stepInd.stop;
                  detailsText = _('get-off');
                  break;
                case 'walk':
                  title = this.formatTime(step.time.start) + ': ' + stepInd.stop;
                  detailsText = _('from-stop') +
                                ' <strong>' + stepInd.stop + '</strong> ' +
                                _('walk-to') +
                                ' <strong>' + stepInd.direction + '</strong>';
                  break;

              }

              console.debug("Indication:", stepInd, title);
              this.addOneStep(step, stepInd, title, detailsText);
            }
            break;

          case 'connection':
            var detailsText = _('waiting-time') + ': <strong>' +
              this.formatDuration(step.duration) + '</strong>';
            this.addOneStep(step, null, _('connection'), detailsText);
            break;
        }

        console.debug(step);
      }
    },

    updateStatus: function(step) {
      if (!step) {
        console.error("updateStatus called with no step");
        return;
      }

      var v = this._statuses[step];
      if (!v) {
        console.error("updateStatus called with invalid step: " + step);
        return;
      }

      var p = document.getElementById('scrapping-progress');
      var m = document.getElementById('scrapping-status');
      p.value = v[0] / 100.0;
      m.textContent = _(v[1]);
      document.location.hash = this._scrapping;
    },

    findAndBind: function(id, name, fun) {
      var e = document.getElementById(id);
      if (!e) {
        console.error('Element "' + id + '" not found.');
        return;
      }
      e.addEventListener(name, fun);
      console.debug('Added <' + name + '> handler for <' + id + '>');
    },

    bindButtons: function() {
      this.findAndBind('start', 'click', this.getJourney.bind(this));
      this.findAndBind('pick', 'click', this.sendPick.bind(this));
      this.findAndBind('add-journey-alarm', 'click', this.addJourneyAlarm.bind(this));
      this.findAndBind('share-journey', 'click', this.shareJourney.bind(this));
      this.findAndBind('journey-details-back', 'click', function(e) {
        document.location.hash = 'journeys-list'
      });
      this.findAndBind('journey-details-close', 'click', function(e) {
        document.location.hash = 'schedule';
      });

      var date = document.getElementById('date');
      var time = document.getElementById('time');
      if (date && time) {
        var d = new Date();
        date.value = d.getFullYear() + '-' +
          this.pad(d.getMonth() + 1) + '-' + this.pad(d.getDate());
        time.value = this.pad(d.getHours()) + ':' + this.pad(d.getMinutes());
      }
    },

    handleJourneyAlarm: function(message) {
      console.log("alarm fired: " + JSON.stringify(message));
      var link = "alarm://" + message.id;
      this._journeyDetailsInfo[link] = message.data.journey;
      this.showJourneyDetails(link);

      var journeyDetailsBack = document.getElementById('journey-details-back');
      journeyDetailsBack.style.visibility = "hidden";

      var journeyAddAlarm = document.getElementById('add-journey-alarm');
      journeyAddAlarm.style.visibility = "hidden";

      var journeyDetailsClose = document.getElementById('journey-details-close');
      if (journeyDetailsClose) {
        journeyDetailsClose.addEventListener('click', function(e) {
          document.location.hash='root';
          journeyDetailsBack.style.visibility = "visible";
          journeyAddAlarm.style.visibility = "visible";
        });
      }
    },

    addJourneyAlarm: function() {
      var cjd = this._journeyDetailsInfo[this._currentJourneyDetailsId];
      console.log("Journeys: " + JSON.stringify(this._journeys));
      console.log("Journey: " + JSON.stringify(this._currentJourneyDetailsId));
      console.log("Will add an alarm for" + JSON.stringify(cjd));

      var dep = cjd[0].time.start;
      // set to 15 min before actual departure
      var date = new Date(new Date(dep).getTime() - 15*60*1000);
      console.log("addJourneyAlarm: startTime=" + date);
      var request = navigator.mozAlarms.add(date, "honorTimezone", {dep: this.formatTime(dep), journey: cjd});
      request.onsuccess = function (e) {
        var banner = document.getElementById("alarm-status");
        banner.style.visibility = "visible";
        window.setTimeout(function() {
          banner.style.visibility = "hidden";
        }, 4000);
      };
      request.onerror = function (e) {
        var msg = e.target.error.name;
        if (e.target.error.name == "InvalidStateError") {
          msg = _('alarm-set-in-past') + ' ' + date;
        } else {
          msg = _('alarm-unknown-error');
        }

        alert(msg);
      };
    },

    shareJourney: function() {
      var cjd = this._journeyDetailsInfo[this._currentJourneyDetailsId];
      var payload = this.journeyToHuman(cjd);
      var subject = encodeURI(_('steps-subject'));
      console.log("Will share: (" + JSON.stringify(cjd) + ") as (" + payload + ")");
      var a = new MozActivity({
        name: 'new',
        data: {
          url: "mailto:?subject=" + subject + "&body=" + encodeURI(payload), // for emails,
          body: payload, // for SMS
          number: "", // empty number for SMS
          type: [
            "websms/sms", "mail"
          ]
        }
      });
    },

    journeyToHuman: function(journey) {
      var humanJourney = new Array();
      for (var si in journey) {
        var step = journey[si];
        console.debug("Step:", step);

        var stepDuration = this.formatDuration(step.duration);

        switch(step.type) {
          case 'indication':
            for (var ii in step.indic) {
              var indic = step.indic[ii];
              console.debug("Indic:", indic);

              var str, time;
              switch(indic.type) {
                case 'mount':
                  time = step.time.start;
                  str = 'steps-mount';
                  break;
                case 'umount':
                  time = step.time.end;
                  str = 'steps-umount';
                  break;
                case 'walk':
                  time = step.time.start;
                  str = 'steps-walk';
                  break;
              }

              var params = {
                time: this.formatTime(time),
                duration: stepDuration,
                line: indic.line,
                stop: indic.stop,
                to: indic.direction,
                direction: indic.direction
              };

              humanJourney.push(_(str, params));
            }
            break;

          case 'connection':
            humanJourney.push(_('steps-connection', {duration: stepDuration}));
            break;
        }
      }

      return humanJourney.join('\n');
    },

    sendPick: function() {
      console.debug("changing: " + document.location.href);
      window.open('stops.html?pickStop#stops-map');
    },

    fillStops: function(source) {
      var ar = source.split('&');
      console.debug(ar);

      var type, name, city;
      ar.forEach(function(e) {
        if (e.indexOf('type=') >= 0) {
          type = e.split('=')[1];
        }
        if (e.indexOf('name=') >= 0) {
          name = decodeURI(e.split('=')[1]);
        }
        if (e.indexOf('city=') >= 0) {
          city = decodeURI(e.split('=')[1]);
        }
      });

      var input = document.getElementById(type);
      if (!input) {
        console.debug('Cannot find id:', type);
      }

      input.value = name + ' (' + city + ')';
    },

    ensureClean: function(id) {
      var cont = document.getElementById(id);
      if (!cont) {
        return;
      }

      while (cont.hasChildNodes()) {
        cont.removeChild(cont.lastChild);
        console.debug("deleted " + cont.lastChild);
      }
    },

    handleException: function(ex) {
      console.warn("Excepton:", ex);
      var error = document.getElementById('error-dialog');
      if (!error) {
        console.error("No error dialog!");
      }

      var ack = document.getElementById('ack-error');
      if (ack) {
        ack.addEventListener('click', function() {
          document.location.hash = 'schedule';
        });
      }

      var errmsg = document.getElementById('error-message');
      var msgvalue = "Unknown error";

      if (ex instanceof InvalidBusStopException) {
        msgvalue = _('error-invalid-busstop');
      }

      if (ex instanceof JourneysListNotFoundException) {
        msgvalue = _('error-no-result');
      }

      if (ex instanceof JourneyDetailsNotFoundException) {
        msgvalue = _('error-no-details');
      }

      if (ex instanceof XHRHttpErrorException) {
        if (ex.statusCode === 404) {
          msgvalue = ex.httpBody;
        } else {
          msgvalue = _('error-http-error', {code: ex.statusCode, body: ex.httpBody});
        }
      }

      if (ex instanceof XHRTimeoutException) {
        msgvalue = _('error-network-timeout');
      }

      if (ex instanceof XHRErrorException) {
        msgvalue = _('error-network-error');
      }

      errmsg.innerHTML = msgvalue;

      document.location.hash = 'error-dialog';
    }
  }
})();

function addGeolocButton(id) {
  var e = document.getElementById(id);
  if (e){
    e.addEventListener('click', function(ev) {
      new GeolocFiller(ev.target.dataset["target"]).startGeoloc();
    });
  }
}

window.addEventListener('localized', function() {
  if (!document.location.hash) {
    document.location.hash = 'root';
  }

  var stopsList = document.getElementById('stops-list');
  if (stopsList) {
    BusStops.attach(stopsList);
  }

  FilBleu.bindButtons();

  addGeolocButton('geoloc-dep');
  addGeolocButton('geoloc-arr');

  window.FilBleu = FilBleu;

  if (!navigator.mozSetMessageHandler) {
    return;
  }

  navigator.mozSetMessageHandler("alarm", function(message) {
    console.log("calling handler for alarm: " + JSON.stringify(message));

    navigator.mozApps.getSelf().onsuccess = function(evt) {
      var app = evt.target.result;
      var iconURL = NotificationHelper.getIconURI(app);
      var shortname = _('alarm-title');
      var description = _('alarm-description', {time: message.data.dep});
      var handleFunction = function() {
        console.log("Notification!!!!");
        app.launch();
        FilBleu.handleJourneyAlarm(message);
      };
      var notification = NotificationHelper.send(shortname, description, iconURL, handleFunction);
    };
  });
});

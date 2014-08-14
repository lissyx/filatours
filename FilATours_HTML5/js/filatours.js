/* -*- Mode: js; js-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set shiftwidth=2 tabstop=2 autoindent cindent expandtab nospell: */

'use strict';

var _ = window.navigator.mozL10n.get;

function JourneyNotFoundException() {
}

function InvalidJourneyException() {
}

function JourneysListNotFoundException() {
}

function JourneyDetailsNotFoundException() {
}

function JourneyDetailsUnexpectedElementsException() {
}

var FilBleu = (function FilBleu() {
  return {
    _api: "http://127.0.0.1:5000",
    _cookie: undefined,
    _journeys: new Array(),
    _scrapping: 'scrapping',
    _journeysList: 'journeys-list',
    _journeyDetails: 'journey-details',
    _journeyDetailsInfo: {},
    _currentJourneyDetailsId: undefined,

    XHR: function(url, method, payload, callback) {
      var xhr = new XMLHttpRequest();

      if (this._cookie) {
        url += '?cookie_name=' + this._cookie.name
             + '&cookie_value=' + this._cookie.value;
      }

      if (method === 'GET' || method === 'POST') {
        if (typeof payload === 'object') {
          for (var o in payload) {
            url += '&' + o + '=' + payload[o];
          }
        }
      }

      xhr.open(method, url, true);
      xhr.responseType = 'json';

      if (method === 'POST') {
        xhr.setRequestHeader("Content-Type", "application/json; charset=UTF-8");
        if (typeof payload === 'object') {
          payload = JSON.stringify(payload);
        }
      }

      xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          if (xhr.status === 200) {
            callback(xhr);
          }
        }
      };
      xhr.send(payload);
    },

    getCookie: function(callback) {
      var handler = (function(xhr) {
        console.debug('XHR:', xhr);
        if (xhr.response.cookie) {
          this._cookie = xhr.response.cookie;
        }
        callback();
      }).bind(this);
      this.XHR([ this._api, 'cookie' ].join('/'), 'GET', null, handler);
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
        callback(xhr.response.journeys);
      }).bind(this);
      this.XHR([ this._api, 'search' ].join('/'), 'POST', search, handler);
    },

    postDetails: function(id, callback) {
      var handler = (function(xhr) {
        console.debug('XHR:', xhr);
        callback(xhr.response.journeysteps);
      }).bind(this);
      this.XHR([ this._api, 'details' ].join('/'), 'GET', {'journey': id}, handler);
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

    formatTime: function(datetime) {
      var retval = "";
      var hours = 0;
      var minutes = 0;
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

      if (hours > 0) {
        retval += hours + "h";
      }

      return (retval + this.pad(minutes));
    },

    formatDuration: function(duration) {
      return this.formatTime(duration) + "min";
    },

    getJourney: function() {
      this.updateStatus(0, _('initializing'));
      this._journeyDetailsInfo = {};

      this.updateStatus(10, _('asked-for-clearing'));
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
      this.updateStatus(0, _('checking-cache'));
      var cache = this._journeyDetailsInfo[link];
      console.debug(cache);
      if (cache != undefined) {
        this.showJourneyDetails(link);
        return;
      }

      this.updateStatus(10, _('cache-miss'));
      this._journeyDetailsInfo[link] = new Array();
      this.postDetails(link, (function(steps) {
        console.debug("Got steps:", steps);
        this._journeyDetailsInfo[link] = steps.list;
        this.showJourneyDetails(link);
      }).bind(this));
    },

    showJourneyDetails: function(id) {
      this._currentJourneyDetailsId = id;
      this.ensureClean('journey-details-container');
      document.location.hash = this._journeyDetails;
      var c = document.getElementById('journey-details-container');
      if (!c) {
        return;
      }

      for (var si in this._journeyDetailsInfo[id]) {
        var step = this._journeyDetailsInfo[id][si];
        console.debug("Step:", step);

        for (var indId in step.indic) {
          var stepInd = step.indic[indId];
          console.debug("Indication:", stepInd);

          var li = document.createElement('li');
          li.className = 'journeypart journey' + step.type;
          var a = document.createElement('a');
          a.className = 'journeypart journey' + step.type;

          var cont = document.createElement('p');
          cont.style.display = 'none';
          var details = document.createElement('span');
          var detailsText, title;

          if (step.type == 'indication') {
            li.className += ' journey' + stepInd.type;
            a.className += ' journey' + stepInd.type;

            if (step.time && step.time.start) {
              title = this.formatTime(step.time.start) + ': ' + stepInd.stop;
            } else {
              title = stepInd.stop;
            }

            if (stepInd.type == 'mount') {
              detailsText = '<strong>' + _('line') + '</strong>: ' +
                stepInd.line + '<br />' +
                '<strong>' + _('direction') + '</strong>: ' + stepInd.direction;
            }
            if (stepInd.type == 'umount') {
              detailsText = _('get-off');
            }
            if (stepInd.type == 'walk') {
              detailsText = _('from-stop') + ' <strong>' + stepInd.stop +
                '</strong> ' + _('walk-to') + ' <strong>' + stepInd.direction + '</strong>';
            }
          }

          if (step.type == 'connection') {
            title = _('connection');
            detailsText = _('waiting-time') + ': <strong>' +
              this.formatDuration(step.duration) + '</strong>';
          }

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
          console.debug(step);
        }
      }
    },

    updateStatus: function(progress, message) {
      var p = document.getElementById('scrapping-progress');
      var m = document.getElementById('scrapping-status');
      p.value = progress / 100.0;
      m.textContent = message;
      document.location.hash = this._scrapping;
    },

    bindButtons: function() {
      var button = document.getElementById('start');
      if (button) {
        button.addEventListener('click', this.getJourney.bind(this));
      }
      var pick = document.getElementById('pick');
      if (pick) {
        pick.addEventListener('click', this.sendPick.bind(this));
      }

      var journeyDetailsBack = document.getElementById('journey-details-back');
      if (journeyDetailsBack) {
        journeyDetailsBack.addEventListener('click', function(e) {
          document.location.hash='journeys-list';
        });
      }
      var journeyDetailsClose = document.getElementById('journey-details-close');
      if (journeyDetailsClose) {
        journeyDetailsClose.addEventListener('click', function(e) {
          document.location.hash='root';
        });
      }

      var date = document.getElementById('date');
      var time = document.getElementById('time');
      if (date && time) {
        var d = new Date();
        date.value = d.getFullYear() + '-' +
          this.pad(d.getMonth() + 1) + '-' + this.pad(d.getDate());
        time.value = this.pad(d.getHours()) + ':' + this.pad(d.getMinutes());
      }

      var alarm = document.getElementById('add-journey-alarm');
      if (alarm) {
        alarm.addEventListener('click', this.addJourneyAlarm.bind(this));
      }

      var share = document.getElementById('share-journey');
      if (share) {
        share.addEventListener('click', this.shareJourney.bind(this))
      }
    },

    handleJourneyAlarm: function(message) {
      console.log("alarm fired: " + JSON.stringify(message));
      var link = "alarm://" + message.id;
      this._journeyDetailsInfo[link] = message.data.journey;
      this.showJourneyDetails(link);

      var journeyDetailsBack = document.getElementById('journey-details-back');
      journeyDetailsBack.style.visibility = "hidden";

      var journeyDetailsTb = document.getElementById('journey-details-toolbar');
      journeyDetailsTb.style.visibility = "hidden";

      var journeyDetailsClose = document.getElementById('journey-details-close');
      if (journeyDetailsClose) {
        journeyDetailsClose.addEventListener('click', function(e) {
          document.location.hash='root';
          journeyDetailsBack.style.visibility = "visible";
          journeyDetailsTb.style.visibility = "visible";
        });
      }
    },

    addJourneyAlarm: function() {
      var cjd = this._journeyDetailsInfo[this._currentJourneyDetailsId][0];
      console.log("Journeys: " + JSON.stringify(this._journeys));
      console.log("Journey: " + JSON.stringify(this._currentJourneyDetailsId));
      console.log("Will add an alarm for" + JSON.stringify(cjd));

      var dep = cjd.time.start;
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
        var text;

        var stepDuration = this.formatDuration(step.duration);

        for (var ii in step.indic) {
          var indic = step.indic[ii];
          console.debug("Indic:", indic);

          var params = {
            time: this.formatTime(step.time.start),
            duration: stepDuration,
            line: indic.line,
            stop: indic.stop,
            to: indic.direction,
            direction: indic.direction
          };

          if (step.type == 'indication') {
            if (indic.type == 'mount') {
              text = _('steps-mount', params);
            }
            if (indic.type == 'umount') {
              text = _('steps-umount', params);
            }
            if (indic.type == 'walk') {
              text = _('steps-walk', params);
            }
          }
        }

        if (step.type == 'connection') {
          text = _('steps-connection', {duration: stepDuration});
        }

        humanJourney.push(text);
      }

      return humanJourney.join('\n');
    },

    sendPick: function() {
      var a = new MozActivity({
        name: 'select-stop'
      });

      a.onerror = function(e) {
        console.warn("select stop activity error:", a.error.name);
      };

      a.onsuccess = function(e) {
        var type = a.result.type;
        var stop = a.result.stop;
        console.log("got stop: " + JSON.stringify(stop));
        var target = document.getElementById(type);
        if (!target) {
          console.error('No target, cannot fill stop name');
          return;
        }
        target.value = stop.name + ' (' + stop.city + ')';
      };
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

      if (ex instanceof InvalidJourneyException) {
        msgvalue = _('error-invalid-journey');
      }

      if (ex instanceof JourneyDetailsNotFoundException) {
        msgvalue = _('error-no-details');
      }

      if (ex instanceof JourneyDetailsUnexpectedElementsException) {
        msgvalue = _('error-unexpected-details');
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

window.addEventListener('DOMContentLoaded', function() {
  var stopsList = document.getElementById('stops-list');
  if (stopsList) {
    BusStops.attach(stopsList);
  }
  FilBleu.bindButtons();
  addGeolocButton('geoloc-dep');
  addGeolocButton('geoloc-arr');
  document.location.hash = 'root';

  /*
  var alarms = navigator.mozAlarms;
  if (alarms != null) {
    var cDate = new Date();
    var aDate = new Date(Date.now() + 30*1000);
    console.log("Alarm at " + aDate + " -- " + cDate);
    var request = alarms.add(aDate, "honorTimezone", {dep: "00h00", journey: [{"mode":"Bus","type":"indication","time":"08h31","duration":"08min","indic":{"type":"mount","line":"30","direction":"Ballan Gare","stop":"La Taillerie"}},{"type":"indication","time":"08h39","indic":{"type":"umount","stop":"Ballan Gare"}},{"type":"connection","duration":"06min"},{"mode":"Bus","type":"indication","time":"08h45","duration":"28min","indic":{"type":"mount","line":"31","direction":"Joué Centre (Jean Jaurès)","stop":"Ballan Gare"}},{"type":"indication","time":"09h13","indic":{"type":"umount","stop":"Joué Gare"}},{"mode":"Marche à pied","type":"indication","duration":"05min","indic":{"type":"walk","direction":"La Grange","stop":"Joué Gare"}},{"type":"connection","duration":"14min"},{"mode":"Bus","type":"indication","time":"09h32","duration":"07min","indic":{"type":"mount","line":"01B","direction":"Douets Lycée Choiseul","stop":"La Grange"}},{"type":"indication","time":"09h39","indic":{"type":"umount","stop":"2 Lions"}},{"mode":"Marche à pied","type":"indication","duration":"09min","indic":{"type":"walk","direction":"Polytech","stop":"2 Lions"}}]});
    console.log("Alarm at " + aDate + " -- " + cDate);

    var request = alarms.getAll();
    request.onsuccess = function (e) { console.log(JSON.stringify(e.target.result)); };
    request.onerror = function (e) { console.log(e.target.error.name); };
  } else {
    alert("No mozAlarms!");
  }
  */

});

window.onload = function() {
  var now = new Date();
  console.log("Alarm fired " + now);
  if (!navigator.mozSetMessageHandler) {
    return;
  }
  console.log("Alarm fired " + now);

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
};

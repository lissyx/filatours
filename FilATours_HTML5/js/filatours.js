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
    _baseurl: 'http://www.filbleu.fr/',
    _raz: '&raz',
    _page: 'page.php',
    _idJourney: 'id=1-1',
    _etapeJourney: 'etape=1',
    _journeys: new Array(),
    _scrapping: 'scrapping',
    _journeysList: 'journeys-list',
    _journeyDetails: 'journey-details',
    _journeyDetailsInfo: {},
    _currentJourneyDetailsId: undefined,

    XHR: function(url, method, params, callback) {
      var self = this;
      var xhr = new XMLHttpRequest({mozSystem: true});
      xhr.open(method, url, true);
      xhr.withCredentials = true;
      if (method == 'POST') {
        var form = "";
        for (var param in params) {
          form += param + "=" + this.htmlescape(params[param]) + "&";
        }
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
      }
      xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          callback(xhr);
        }
      };
      xhr.send(form);
    },

    prepareXHR: function(id, callback) {
      var self = this;
      this.XHR(
          this._baseurl + this._page + '?' + id,
          'GET', {}, function(e) {
        if (e.status != 200) {
          return;
        }
        self.XHR(
            self._baseurl + self._page + '?' + id + self._raz ,
            'GET', {}, function(e) {
          if (e.status != 200) {
            return;
          }
          callback(e);
        });
      });
    },

    htmlescape: function(s) {
      var ns = new String(s);
      return escape(ns.latinize())
        .replace(new RegExp('%20', 'g'), '+')
        .replace(new RegExp('\/', 'g'), '%2F');
    },

    htmlpurify: function(s) {
      return s.replace(/\s+/g, ' ')
        .replace(/\\n/g, '');
    },

    parseTime: function(s) {
      return s.replace(new RegExp('.*: ([0-9]+)h([0-9]+)', 'g'), "$1h$2");
    },

    parseDuree: function(s) {
      return s.replace(new RegExp('([0-9]+)h([0-9]+)min', 'g'), "$1h$2");
    },

    pad: function(n) { return n < 10 ? '0' + n : n },

    getJSDate: function(str) {
      var ar = str.split("-");
      str = parseInt(ar[0]) + "-" + this.pad(parseInt(ar[1])) + "-" + this.pad(parseInt(ar[2]));
      return new Date(str);
    },

    getDate: function(str) {
      var date = this.getJSDate(str);
      return this.pad(date.getDate()) + '/' +
        this.pad(date.getMonth() + 1) + '/' +
        date.getFullYear();
    },

    getHour: function(str) {
      return parseInt(str.split(':')[0], 10);
    },

    getMin: function(str) {
      return parseInt(str.split(':')[1], 10);
    },

    getJourney: function() {
      this.updateScrappingStatus(0, _('initializing'));
      var date = this.getDate(document.getElementById('date').value);
      var hour = this.getHour(document.getElementById('time').value);
      var min = this.getMin(document.getElementById('time').value);
      var d = BusStops.getMatchingStop(document.getElementById('departure').value);
      var a = BusStops.getMatchingStop(document.getElementById('arrival').value);
      // Expected:
      // Departure=Ballan-Mir%E9+-+La+Taillerie&Arrival=Saint-Pierre-des-Corps+-+St+Pierre+Gare&Date=06%2F11%2F2012&Sens=1&Hour=8&Minute=0&Criteria=1
      // Got:
      // Departure=Ballan-Mir%E9+-+La+Taillerie&Arrival=Saint-Pierre-des-Corps+-+St+Pierre+Gare&Date=06%2F11%2F2012&Sens=1&Hour=8&Minute=0&Criteria=1&
      var params = {
        Departure: d._city + ' - ' + d._name,
        Arrival: a._city + ' - ' + a._name,
        Date: date,
        Sens: document.getElementById('sens').value,
        Hour: hour,
        Minute: min,
        Criteria: document.getElementById('crit').value
      }

      var targeturl = this._baseurl + this._page + '?' +
        this._idJourney + '&' + this._etapeJourney;
      console.debug("params: " + JSON.stringify(params));

      this.updateScrappingStatus(10, _('asked-for-clearing'));
      var self = this;
      this.prepareXHR(this._idJourney, function(e) {
        if (e.status != 200) {
          return;
        }
        self.updateScrappingStatus(30, _('got-clearing'));
        self.XHR(targeturl, 'POST', params, function(e) {
          if (e.status != 200) {
            return;
          }
          console.debug(e.status);
          self.updateScrappingStatus(60, _('got-reply'));
          try {
            self.extractJourneysList(e.responseText);
          } catch (e) {
            self.handleException(e);
          }
        });
      });
    },

    html2dom: function(html) {
      var parser = new DOMParser();
      var doc = parser.parseFromString(html, "text/html");
      console.debug(doc);
      return doc;
    },

    extractJourneysList: function(html) {
      var tree = this.html2dom(html);
      var propositions = tree.querySelector('table[summary="Propositions"]');
      console.debug(propositions);
      if (!propositions) {
        throw new JourneysListNotFoundException();
      }
      
      this.updateScrappingStatus(70, _('found-journeys'));

      var journeys = propositions.getElementsByTagName('tr');
      console.debug(journeys);
      if (!journeys) {
        throw new JourneysListNotFoundException();
      }

      this.updateScrappingStatus(80, _('extracting-journeys'));

      this._journeys = new Array();
      // first one is header, skip it
      for (var j = 1; j < journeys.length; j++) {
        try {
          var journey = this.extractJourney(journeys[j]);
          console.debug(JSON.stringify(journey));
          this._journeys.push(journey);
        } catch (e) {
          this.handleException(e);
        }
      }

      this.updateScrappingStatus(100, _('displaying-journeys'));
      this.showJourneysList();
    },

    extractJourney: function(trnode) {
      var parts = trnode.getElementsByTagName('td');
      if (parts.length < 1) {
        throw new InvalidJourneyException();
        return {};
      }
      var dates = parts[0];
      return {
        dep: this.parseTime(this.htmlpurify(dates.firstChild.textContent)),
        arr: this.parseTime(this.htmlpurify(dates.lastChild.textContent)),
        link: this.htmlpurify(parts[1].getElementsByTagName('a')[0].attributes["href"].textContent),
        duree: this.parseDuree(this.htmlpurify(parts[2].textContent)),
        conn: this.htmlpurify(parts[3].textContent)
      };
    },

    showJourneysList: function() {
      this.ensureClean('journeys-list-container');
      document.getElementById('close-journeys-list')
        .addEventListener('click',
            function(ev) { document.location.hash = 'schedule'; });
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
        a.textContent = bj.dep + ' - ' + bj.arr + ' (' + bj.duree + ')';

        var licont = document.createElement('li');
        licont.style.display = 'none';
        var details = document.createElement('span');
        details.textContent = _('connections') + ': ' + bj.conn;
        details.dataset['link'] = bj.link;
        
        var self = this;
        details.addEventListener('click', function(ev) {
          self.getJourneyDetails(ev.target.dataset['link']);
        });

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
      this.updateScrappingStatus(0, _('checking-cache'));
      var cache = this._journeyDetailsInfo[link];
      console.debug(cache);
      if (cache != undefined) {
        this.showJourneyDetails(link);
        return;
      }

      this.updateScrappingStatus(10, _('cache-miss'));
      this._journeyDetailsInfo[link] = new Array();
      var self = this;
      this.XHR(this._baseurl + link, 'GET', {}, function(e) {
        if (e.status != 200) {
          return;
        }
        console.debug(e.status);
        self.updateScrappingStatus(20, _('got-reply'));
        try {
          self.extractJourneyDetails(e.responseText, link);
        } catch (e) {
          self.handleException(e);
        }
      });
    },

    extractJourneyDetails: function(html, link) {
      var tree = this.html2dom(html);
      var itineraire = tree.querySelector('fieldset[class="itineraire"]');
      console.debug(itineraire);
      if (!itineraire) {
        throw new JourneyDetailsNotFoundException();
      }
      
      this.updateScrappingStatus(30, _('found-journey-details'));

      var list = itineraire.querySelector('table');
      console.debug(list);
      if (!list) {
        throw new JourneyDetailsNotFoundException();
      }

      var journey = itineraire.getElementsByTagName('tr');
      console.debug(journey);
      if (!journey) {
        throw new JourneyDetailsNotFoundException();
      }

      this.updateScrappingStatus(40, _('extracting-journey-details'));

      // first one is header, skip it
      for (var j = 1; j < journey.length; j++) {
        var step = this.extractJourneyStepDetails(journey[j]);
        console.debug(JSON.stringify(step));
        this._journeyDetailsInfo[link].push(step);
      }

      this.updateScrappingStatus(100, _('displaying-journey-details'));
      this.showJourneyDetails(link);
    },

    extractJourneyStepDetails: function(trnode) {
      var tds = trnode.querySelectorAll('td');
      if (!tds) {
        throw new JourneyDetailsNotFoundException();
      }

      var mode = undefined;
      var indic = undefined;
      var type = undefined;
      var time = undefined;
      var duration = undefined;

      var nbs = tds.length;
      switch(nbs) {
        case 3: // connection
          var cls = tds[0].className;
          if (cls == 'indication') {
            type = 'indication';
            indic = this.extractIndication(tds[0]);
            time = this.parseTime(tds[1].textContent);
          }

          if (cls == 'correspondance') {
            type = 'connection';
            duration = this.parseTime(tds[1].textContent);
          }

          break;

        case 4: // by foot
        case 5: // journey part
          var cls = tds[1].className;
          mode = tds[0].getElementsByTagName('img')[0].attributes['alt'].textContent;
          if (cls == 'indication') {
            type = 'indication';
            indic = this.extractIndication(tds[1]);

            if (nbs == 4) {
              duration = this.parseTime(tds[2].textContent);
            }

            if (nbs == 5) {
              time = this.parseTime(tds[2].textContent);
              duration = this.parseTime(tds[3].textContent);
            }
          }
          break;

        default:
          throw new JourneyDetailsUnexpectedElementsException();
          break;
      }

      return {
        mode: mode,
        type: type,
        time: time,
        duration: duration,
        indic: indic
      };
    },

    extractIndication: function(node) {
      var type = undefined;
      var line = undefined;
      var direction = undefined;
      var stop = undefined;

      var take = node.textContent.match(/^Prendre/g);
      var out = node.textContent.match(/^Descendre/g);
      var walk = node.textContent.match(/^De l'arrêt/g);

      var Bs = node.querySelectorAll('b');

      if (take) {
        type = 'mount';
        line = Bs[0].textContent;
        direction = Bs[1].textContent;
        stop = Bs[2].textContent;
      }

      if (out) {
        type = 'umount';
        stop = Bs[0].textContent;
      }

      if (walk) {
        type = 'walk';
        stop = Bs[0].textContent;
        direction = Bs[1].textContent;
      }

      return {
        type: type,
        line: line,
        direction: direction,
        stop: stop
      };
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
        var li = document.createElement('li');
        li.className = 'journeypart journey' + step.type;
        var a = document.createElement('a');
        a.className = 'journeypart journey' + step.type;

        var cont = document.createElement('p');
        cont.style.display = 'none';
        var details = document.createElement('span');
        var detailsText, title;

        if (step.type == 'indication') {
          li.className += ' journey' + step.indic.type;
          a.className += ' journey' + step.indic.type;
          if (step.time) {
            title = step.time + ': ' + step.indic.stop;
          } else {
            title = step.indic.stop;
          }

          if (step.indic.type == 'mount') {
            detailsText = '<strong>' + _('line') + '</strong>: ' +
              step.indic.line + '<br />' +
              '<strong>' + _('direction') + '</strong>: ' + step.indic.direction;
          }
          if (step.indic.type == 'umount') {
            detailsText = _('get-off');
          }
          if (step.indic.type == 'walk') {
            detailsText = _('from-stop') + ' <strong>' + step.indic.stop +
              '</strong> ' + _('walk-to') + ' <strong>' + step.indic.direction + '</strong>';
          }
        }

        if (step.type == 'connection') {
          title = _('connection');
          detailsText = _('waiting-time') + ': <strong>' + step.duration + '</strong>';
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
    },

    updateScrappingStatus: function(progress, message) {
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

      navigator.vibrate([100, 200, 300, 200, 100, 1000, 500, 500]);
      return;
    },

    addJourneyAlarm: function() {
      var cjd = this._journeyDetailsInfo[this._currentJourneyDetailsId];
      console.log("Journeys: " + JSON.stringify(this._journeys));
      console.log("Journey: " + JSON.stringify(this._currentJourneyDetailsId));
      console.log("Will add an alarm for" + JSON.stringify(cjd));
      var date = this.getJSDate(document.getElementById('date').value);
      var hour = this.getHour(document.getElementById('time').value);
      var dep;
      var newHours, newMins;

      for (var i = 0; i < this._journeys.length; i++) {
        if (this._journeys[i]["link"] == this._currentJourneyDetailsId) {
          dep = this._journeys[i]["dep"];
          break;
        }
      }

      var time = dep.split("h");

      newHours = parseInt(time[0]);
      newMins = parseInt(time[1]);

      date.setHours(newHours);
      date.setMinutes(newMins);

      // set to 15 min before actual departure
      var newTime = date.getTime() - 15*60*1000;

      if (newHours < hour && (hour - newHours >= 12)) {
        newTime += 86400*1000; // add a day
      }

      date.setTime(newTime);

      console.log("addJourneyAlarm: startTime=" + date);
      var request = navigator.mozAlarms.add(date, "ignoreTimezone", {dep: dep, journey: cjd});
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
      console.log("Will share" + JSON.stringify(cjd));
      var payload = JSON.stringify(cjd);
      var a = new MozActivity({
        name: 'new',
        data: {
          url: "mailto:?subject=Trajet Fil Bleu&body=" + payload, // for emails,
          body: payload // for SMS
        }
      });
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
  document.getElementById(id).addEventListener('click', function(ev) {
    new GeolocFiller(ev.target.dataset["target"]).startGeoloc();
  });
}

window.addEventListener('DOMContentLoaded', function() {
  BusStops.attach(document.getElementById('stops-list'));
  FilBleu.bindButtons();
  addGeolocButton('geoloc-dep');
  addGeolocButton('geoloc-arr');
  document.location.hash = 'root';
});

window.onload = function() {
  if (!navigator.mozSetMessageHandler) {
    return;
  }
  navigator.mozSetMessageHandler("alarm", function(message) {
    console.log("calling handler for alarm: " + JSON.stringify(message));
    FilBleu.handleJourneyAlarm(message);
  });
};

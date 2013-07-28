/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.io.IOException;
import java.net.SocketTimeoutException;
import java.util.Map;
import java.util.ArrayList;
import java.util.Iterator;

import android.util.Log;

import android.os.AsyncTask;

import org.jsoup.Jsoup;
import org.jsoup.Connection.Response;
import org.jsoup.Connection.Method;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

public class BusJourney {
    private String cityDep;
    private String cityArr;
    private String stopDep;
    private String stopArr;
    private String date;
    private String hour;
    private String minute;
    private String sens;
    private String criteria;

    private String urlbase;
    private String urlraz;

    private Map<String, String> cookies;
    private ArrayList<Journey> journeys;

    public BusJourney() {
        this.urlraz = new URLs("view=itineraire").getURLraz();
        this.urlbase = new URLs("view=itineraire").getURL();
        this.journeys = new ArrayList<Journey>();
    }

    public ArrayList<Journey> getBusJourneys(BusToursActivity.ProcessScrapping parent) throws java.io.IOException, java.net.SocketTimeoutException, ScrappingException {
        String dep = this.cityDep + " - " + this.stopDep;
        String arr = this.cityArr  + " - " + this.stopArr;

        Log.e("BusTours:BusJourney", "RAZ=" + this.urlraz);
        Log.e("BusTours:BusJourney", "URL=" + this.urlbase);

        parent.progress(20, R.string.jsoupAskRaz);

        Log.e("BusTours:BusJourney", "dep='" + dep + "'");
        Log.e("BusTours:BusJourney", "arr='" + arr + "'");

        Response res = URLs.getConnection(this.urlraz).method(Method.GET).execute();
        Log.e("BusTours:BusJourney", "Got RAZ.");

        parent.progress(30, R.string.jsoupGotRaz);

        this.cookies = res.cookies();

        Document reply = URLs.getConnection(this.urlbase)
            .cookies(this.cookies)
            .data("iform[Departure]", dep)
            .data("iform[Arrival]", arr)
            .data("iform[Sens]", this.sens)
            .data("iform[Date]", this.date)
            .data("iform[Hour]", this.hour)
            .data("iform[Minute]", this.minute)
            .data("iform[Criteria]", this.criteria)
            .post();
        Log.e("BusTours:BusJourney", "Posted form:");
        Log.e("BusTours:BusJourney", "    Departure=" + dep);
        Log.e("BusTours:BusJourney", "    Arrival=" + arr);
        Log.e("BusTours:BusJourney", "    Sens=" + this.sens);
        Log.e("BusTours:BusJourney", "    Date=" + this.date);
        Log.e("BusTours:BusJourney", "    Hour=" + this.hour);
        Log.e("BusTours:BusJourney", "    Minute=" + this.minute);
        Log.e("BusTours:BusJourney", "    Criteria=" + this.criteria);

        Elements optgroups = reply.getElementsByAttributeValue("label", "Arrêts");
        if (!optgroups.isEmpty()) {
            Log.e("BusTours:BusJourney", "Need to select first optgroup");

            dep = reply.getElementById("Departure").attr("value");
            arr = reply.getElementById("Arrival").attr("value");
            String depJvmalin = reply.getElementById("DepJvmalin").attr("value");
            String arrJvmalin = reply.getElementById("ArrJvmalin").attr("value");

            Log.e("BusTours:BusJourney", "Reusing dep='" + dep + "'");
            Log.e("BusTours:BusJourney", "Reusing arr='" + arr + "'");

            Iterator<Element> it = optgroups.iterator();
            while (it.hasNext()) {
                Element current = it.next();
                Element parentElement = current.parent();
                Log.e("BusTours:BusJourney", "Parent: " + parentElement.tagName() + ":" + parentElement.id());
                Element firstChoice = current.child(0);
                String newValJvmalin = firstChoice.attr("value");
                String newValue = firstChoice.text();

                if (parentElement.id().equals("DepJvmalin")) {
                    dep = newValue;
                    depJvmalin = newValJvmalin;
                    Log.e("BusTours:BusJourney", "new depJvmalin='" + depJvmalin + "'; dep='" + dep + "'");
                }

                if (parentElement.id().equals("ArrJvmalin")) {
                    arr = newValue;
                    arrJvmalin = newValJvmalin;
                    Log.e("BusTours:BusJourney", "new arrJvmalin='" + arrJvmalin + "'; arr='" + arr + "'");
                }
            }

            this.cookies = res.cookies();
            Log.e("BusTours:BusJourney", "new cookies: '" + this.cookies + "'");

            reply = URLs.getConnection(this.urlbase)
                .cookies(this.cookies)
                .data("iform[Departure]", dep)
                .data("iform[DepJvmalin]", depJvmalin)
                .data("iform[Arrival]", arr)
                .data("iform[ArrJvmalin]", arrJvmalin)
                .data("iform[Sens]", this.sens)
                .data("iform[Date]", this.date)
                .data("iform[Hour]", this.hour)
                .data("iform[Minute]", this.minute)
                .data("iform[Criteria]", this.criteria)
                .post();

            Log.e("BusTours:BusJourney", "Re-posted form: ");
            Log.e("BusTours:BusJourney", "    Departure=" + dep);
            Log.e("BusTours:BusJourney", "    DepJvmalin=" + depJvmalin);
            Log.e("BusTours:BusJourney", "    Arrival=" + arr);
            Log.e("BusTours:BusJourney", "    ArrJvmalin=" + arrJvmalin);
            Log.e("BusTours:BusJourney", "    Sens=" + this.sens);
            Log.e("BusTours:BusJourney", "    Date=" + this.date);
            Log.e("BusTours:BusJourney", "    Hour=" + this.hour);
            Log.e("BusTours:BusJourney", "    Minute=" + this.minute);
            Log.e("BusTours:BusJourney", "    Criteria=" + this.criteria);
        }

        parent.progress(40, R.string.jsoupPostedForm);

        Elements alerte = reply.getElementsByClass("alert");
        if (alerte.isEmpty()) {
            Log.e("BusTours:BusJourney", "No alerte, cool.");
        } else {
            Log.e("BusTours:BusJourney", "Got alerte:" + alerte.first().text());
            String exceptionText = alerte.first().text();
            if (alerte.first().html().contains("itineraire.enlarge")) {
                Elements alerteA = alerte.first().getElementsByClass("submit_bt");
                if (!alerteA.isEmpty()) {
                    String enlargeUrl = URLs.siteBase + alerteA.first().attr("href");
                    Log.e("BusTours:BusJourney", "Got an enlarge:" + alerteA.first().html());
                    Log.e("BusTours:BusJourney", "Got an enlarge URL:" + enlargeUrl);
                    parent.progress(45, R.string.askingEnlargement);
                    reply = URLs.getConnection(enlargeUrl)
                        .cookies(this.cookies)
                        .get();
                }
            } else {
                throw new ScrappingException(exceptionText);
            }
        }

        Elements navig = reply.getElementsByAttributeValue("id", "jvmalinList");
        Log.e("BusTours:BusJourney", "Retrieved elements: " + navig.size());
        if (navig.isEmpty()) {
            Log.e("BusTours:BusJourney", "NO Navig !!!");
            String[] parts = reply.body().html().split("\\r?\\n");
            for (int i = 0; i < parts.length; i++) {
                Log.e("BusTours:BusJourney", "BODY::" + parts[i]);
            }
            throw new ScrappingException("Not a result page");
        }

        parent.progress(50, R.string.jsoupGotNavig);

        Elements trips = navig.first().getElementsByTag("table");
        if (trips.isEmpty()) {
            Log.e("BusTours:BusJourney", "NO Trips !!!");
            Log.e("BusTours:BusJourney", "table::" + navig.html());
            throw new ScrappingException("No journey");
        }

        parent.progress(60, R.string.jsoupGotJourneys);

        Iterator<Element> it = trips.iterator();
        int iProgress = 60;
        while (it.hasNext()) {
            parent.progress(iProgress, R.string.jsoupGotTrip);
            this.journeys.add(new Journey(it.next(), this.cookies));
            iProgress += 10;
        }

        return this.journeys;
    }

//    public void getBusJourneysDetails() {
//        Iterator<Journey> jit = this.journeys.iterator();
//        while (jit.hasNext()) {
//            jit.next().getDetails();
//        }
//    }

    public String pruneAccents(String s) {
        s = s.replaceAll("[èéêë]","e");
        s = s.replaceAll("[ûù]","u");
        s = s.replaceAll("[ïî]","i");
        s = s.replaceAll("[àâ]","a");
        s = s.replaceAll("ô","o");
        s = s.replaceAll("[ÈÉÊË]","E");
        s = s.replaceAll("[ÛÙ]","U");
        s = s.replaceAll("[ÏÎ]","I");
        s = s.replaceAll("[ÀÂ]","A");
        s = s.replaceAll("Ô","O");
        return s;
    }

    public void setCityDep(String v) {
        this.cityDep = this.pruneAccents(v);
    }

    public void setCityArr(String v) {
        this.cityArr = this.pruneAccents(v);
    }

    public void setStopDep(String v) {
        this.stopDep = this.pruneAccents(v);
    }

    public void setStopArr(String v) {
        this.stopArr = this.pruneAccents(v);
    }

    public void setDate(String v) {
        this.date = v;
    }

    public void setHour(String v) {
        this.hour = v;
    }

    public void setMinute(String v) {
        this.minute = v;
    }

    public void setSens(String v) {
        this.sens = v;
    }

    public void setCriteria(String v) {
        this.criteria = v;
    }
}

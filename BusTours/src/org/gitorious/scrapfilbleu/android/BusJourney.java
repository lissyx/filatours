/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.io.IOException;
import java.net.SocketTimeoutException;
import java.util.Map;
import java.util.Iterator;

import android.util.Log;

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

    public BusJourney() {
        this.urlraz = new URLs("id=1-1").getURLraz();
        this.urlbase = new URLs("id=1-1&etape=1").getURL();
    }

    public void getBusJourneys() throws java.io.IOException, java.net.SocketTimeoutException {
        String dep = this.cityDep + " - " + this.stopDep;
        String arr = this.cityArr  + " - " + this.stopArr;

        Log.e("BusTours:BusJourney", "RAZ=" + this.urlraz);
        Log.e("BusTours:BusJourney", "URL=" + this.urlbase);

        Log.e("BusTours:BusJourney", "dep='" + dep + "'");
        Log.e("BusTours:BusJourney", "arr='" + arr + "'");

        Response res = Jsoup.connect(this.urlraz).method(Method.GET).execute();
        Log.e("BusTours:BusJourney", "Got RAZ.");

        this.cookies = res.cookies();

        Document reply = Jsoup.connect(this.urlbase)
            .cookies(this.cookies)
            .data("Departure", dep)
            .data("Arrival", arr)
            .data("Sens", this.sens)
            .data("Date", this.date)
            .data("Hour", this.hour)
            .data("Minute", this.minute)
            .data("Criteria", this.criteria)
            .post();
        Log.e("BusTours:BusJourney", "Posted form.");

        Elements navig = reply.getElementsByAttributeValue("class", "navig");
        Log.e("BusTours:BusJourney", "Retrieved elements.");
        if (!navig.isEmpty()) {
            Elements table = reply.getElementsByAttributeValue("summary", "Propositions");
            if (!table.isEmpty()) {
                Elements trips = table.first().getElementsByTag("tr");
                if (!trips.isEmpty()) {
                    Log.e("BusTours:BusJourney", "Trips::" + trips.html());
                    Iterator<Element> it = trips.iterator();
                    // bypass first element, table heading
                    it.next();
                    while (it.hasNext()) {
                        Element trip = it.next();
                        Elements parts = trip.getElementsByTag("td");
                        Log.e("BusTours:BusJourney", "date==" + parts.get(0).html());
                        Log.e("BusTours:BusJourney", "link==" + parts.get(1).html());
                        Log.e("BusTours:BusJourney", "duration==" + parts.get(2).html());
                        Log.e("BusTours:BusJourney", "connections==" + parts.get(3).html());
                    }
                } else {
                    Log.e("BusTours:BusJourney", "NO Trips !!!");
                    Log.e("BusTours:BusJourney", "table::" + table.html());
                }
            } else {
                Log.e("BusTours:BusJourney", "NO Table !!!");
                Log.e("BusTours:BusJourney", "navig::" + navig.html());
            }
        } else {
            Log.e("BusTours:BusJourney", "NO Navig !!!");
            Log.e("BusTours:BusJourney", "BODY::" + reply.body().html());
        }
    }

    public void getBusJourneyDetails() {

    }

    public String pruneAccents(String s) {
        s = s.replaceAll("[èéêë]","e");
        s = s.replaceAll("[ûù]","u");
        s = s.replaceAll("[ïî]","i");
        s = s.replaceAll("[àâ]","a");
        s = s.replaceAll("Ô","o");
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

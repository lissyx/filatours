/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import android.util.Log;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

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

    public BusJourney() {
        this.urlbase = new URLs("id=1-1").getURL();
        this.urlraz = new URLs("id=1-1").getURLraz();
    }

    public void getBusJourneys() {
        Log.e("BusTours:BusJourney", "URL=" + this.urlbase);
        Log.e("BusTours:BusJourney", "RAZ=" + this.urlraz);
    }

    public void getBusJourneyDetails() {

    }

    public void setCityDep(String v) {
        this.cityDep = v;
    }

    public void setCityArr(String v) {
        this.cityArr = v;
    }

    public void setStopDep(String v) {
        this.stopDep = v;
    }

    public void setStopArr(String v) {
        this.stopArr = v;
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

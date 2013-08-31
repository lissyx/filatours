/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.util.Map;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

import android.util.Log;

public class Journey {
    private String departureTime;
    private String arrivalTime;
    private String duration;
    private String connections;
    private String url;

    private JourneyDetails details;

    private Map<String, String> cookies;

    private Pattern reTimeDeparture;
    private Pattern reTimeArrival;
    private Pattern reDuration;
    private Pattern reConnections;

    public Journey(Element trip, Map<String, String> cookies) {
        this.cookies = cookies;
        this.details = null;
        this.reTimeDeparture    = Pattern.compile("<strong>D&eacute;part<\\/strong> : (\\d+)h(\\d+)");
        this.reTimeArrival      = Pattern.compile("<strong>Arriv&eacute;e<\\/strong> : (\\d+)h(\\d+)");
        this.reDuration         = Pattern.compile("(\\d+)\\s*h|(\\d+)\\s*");
        this.reConnections      = Pattern.compile("<strong>correspondance\\(s\\)<\\/strong> : (\\d+)");

        Elements parts = trip.getElementsByTag("td");
        this.parseTime(parts.get(0));
        this.parseLink(parts.get(2));
        this.parseDuration(parts.get(1).getElementsByTag("p").last());
        this.parseConnections(parts.get(3));

        Log.e("BusTours:Journey", "Journey==" + this.toString());
    }

    private void parseTime(Element e) {
        // Log.e("BusTours:Journey", "date==" + e.html());
        this.departureTime = "";
        this.arrivalTime = "";

        Matcher dep = this.reTimeDeparture.matcher(e.html());
        Matcher arr = this.reTimeArrival.matcher(e.html());

        if (!dep.find() || !arr.find()) {
            Log.e("BusTours:Journey", "No time match :(");
        }

        this.departureTime = dep.group(1) + "h" + dep.group(2);
        this.arrivalTime = arr.group(1) + "h" + arr.group(2);
    }

    private void parseLink(Element e) {
        // Log.e("BusTours:Journey", "link==" + e.html());

        this.url = "";
        Elements link = e.getElementsByTag("a");
        if (link.isEmpty()) {
            Log.e("BusTours:Journey", "NO link");
        }

        this.url = link.first().attr("href");
    }

    private void parseDuration(Element e) {
        Log.e("BusTours:Journey", "duration==" + e.html());
        this.duration = "";

        Matcher m = this.reDuration.matcher(e.html());

        if (!m.find()) {
            Log.e("BusTours:Journey", "No duration match :(");
            this.duration = "0h00";
            return;
        }

        if (m.group(1) == null) {
            this.duration = "0h" + m.group(2);
        } else {
            this.duration = m.group(1) + "h";
            if (m.find()) {
                this.duration += m.group(2);
            }
        }
    }

    private void parseConnections(Element e) {
        //  Log.e("BusTours:Journey", "connections==" + e.html());
        Matcher conn = this.reConnections.matcher(e.html());
        this.connections = "";

        if (!conn.find()) {
            Log.e("BusTours:Journey", "No connection match :(");
        }

        this.connections = conn.group(1);
    }

    public String getDepartureTime() {
        return this.departureTime;
    }

    public String getArrivalTime() {
        return this.arrivalTime;
    }

    public String getDuration() {
        return this.duration;
    }

    public String getConnections() {
        return this.connections;
    }

    public String getUrl() {
        return this.url;
    }

    public JourneyDetails getJourneyDetails() {
        return this.details;
    }

    public String toString() {
        String res =
            "{ 'departure':" + this.getDepartureTime() +
            ", 'arrival': " + this.getArrivalTime() +
            ", 'duration': " + this.getDuration() +
            ", 'connections': " + this.getConnections();

        if (this.details != null) {
            res +=
            "'details': ";
        }

        res += " }";

        return res;
    }

    public void getDetails(BusToursActivity.ProcessScrapping parent) throws java.io.IOException, java.net.SocketTimeoutException, ScrappingException {
        String link = new URLs("").getURL() + this.getUrl().replace("page.php?", "");

        parent.progress(20, R.string.jsoupStartGetDetails);
        Log.e("BusTours:BusJourney", "Asking details at " + link);

        Document reply = URLs.getConnection(link)
            .cookies(this.cookies)
            .get();

        Elements itin = reply.getElementsByAttributeValue("id", "jvmalinDetail");
        if (itin.isEmpty()) {
            Log.e("BusTours:BusJourney", "NO Itin !!!");
            Log.e("BusTours:BusJourney", "BODY::" + reply.body().html());
            throw new ScrappingException("Not a details page");
        }

        parent.progress(30, R.string.jsoupGotDetails);
        Log.e("BusTours:BusJourney", "Got details page.");

        Elements trips = itin.select(
            "div[class=jvmalinDetail_item], p[class=correspondance]"
        );
        if (trips.isEmpty()) {
            Log.e("BusTours:BusJourney", "NO Trips !!!");
            Log.e("BusTours:BusJourney", "table::" + itin.html());
            throw new ScrappingException("No journey");
        }

        parent.progress(40, R.string.jsoupGotDetailsElems);
        Log.e("BusTours:BusJourney", "Got details elements.");

        this.details = new JourneyDetails(trips);

        parent.progress(100, R.string.jsoupGotFullDetails);
        Log.e("BusTours:BusJourney", "Got full details.");
        Log.e("BusTours:BusJourney", "Details: " + this.details);
    }
}

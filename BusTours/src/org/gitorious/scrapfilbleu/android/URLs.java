/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import org.jsoup.Jsoup;
import org.jsoup.Connection;

public class URLs {
    private String param;
    static final String raz = "raz";
    static final String urlBase = "http://www.filbleu.fr/horaires-et-trajets/votre-itineraire-sur-mesure";
    static final int timeout = 10000;

    public URLs(String param) {
        this.param = param;
    }

    public String getURLraz() {
        return this.urlBase + "?" + this.param + "&" + this.raz;
    }

    public String getURL() {
        return this.urlBase + "?" + this.param;
    }

    public static Connection getConnection(String url) {
        return Jsoup.connect(url).timeout(URLs.timeout);
    }
}

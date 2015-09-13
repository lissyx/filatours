/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import org.jsoup.Jsoup;
import org.jsoup.Connection;

public class URLs {
    private String param;
    static final String raz = "raz";
    static final String siteBase = "https://www.filbleu.fr/";
    static final String urlBase = "https://www.filbleu.fr/horaires-et-trajet/itineraire-sur-mesure";
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

    public String buildURL(String resource) {
        String newUrl = "";

        if (!resource.startsWith("http://") &&
            !resource.startsWith("https://") &&
            !resource.startsWith("://")) {
            newUrl = this.siteBase + resource;
        } else {
            newUrl = resource;
        }

        return newUrl;
    }

    public static Connection getConnection(String url) {
        return Jsoup.connect(url).timeout(URLs.timeout);
    }
}

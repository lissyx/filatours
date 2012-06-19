/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

public class URLs {
    private String param;
    static final String raz = "raz";
    static final String urlBase = "http://www.filbleu.fr/page.php";

    public URLs(String param) {
        this.param = param;
    }

    public String getURLraz() {
        return this.urlBase + "?" + this.param + "&" + this.raz;
    }

    public String getURL() {
        return this.urlBase + "?" + this.param;
    }
}

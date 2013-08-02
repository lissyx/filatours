/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

public class BusStop {
    public String name;
    public String city;
    public Double lat;
    public Double lon;
    public Double dist;

    public BusStop(String name, String city, Double lat, Double lon, Double dist) {
        this.name = name;
        this.city = city;
        this.lat  = lat;
        this.lon  = lon;
        this.dist = dist;
    }
}

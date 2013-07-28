/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.util.Calendar;
import android.util.Log;

public class SeasonPicker {
    public static Calendar getTramProd() {
        Calendar prodTram = Calendar.getInstance();
        prodTram.set(2013, 7, 30);
        return prodTram;
    }

    public static boolean checkDate(String season, int year, int month, int day) {
        Calendar date = Calendar.getInstance();
        date.set(year, month, day);

        if (season.equals("tram")) {
            return date.after(SeasonPicker.getTramProd());
        }

        if (season.equals("classic")) {
            return date.before(SeasonPicker.getTramProd());
        }

        // should not be reached
        return false;
    }

    public static String pickFromDate(Calendar date) {
        String seasonPicked;

        if (date.after(SeasonPicker.getTramProd())) {
            seasonPicked = "tram";
        } else {
            seasonPicked = "classic";
        }

            Log.e("BusTours:SeasonPicker", "Picked " + seasonPicked);

        return seasonPicked;
    }

    public static String pick() {
        return SeasonPicker.pickFromDate(Calendar.getInstance());
    }
}

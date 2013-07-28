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

		return date.after(SeasonPicker.getTramProd()) && season.equals("tram");
	}

	public static String pick() {
		String seasonPicked;
		Calendar today = Calendar.getInstance();

		if (today.after(SeasonPicker.getTramProd())) {
			seasonPicked = "tram";
		} else {
			seasonPicked = "classic";
		}

	        Log.e("BusTours:SeasonPicker", "Picked " + seasonPicked);

		return seasonPicked;
	}
}

/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.io.IOException;
import java.net.SocketTimeoutException;
import java.util.Map;
import java.util.List;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.Iterator;
import java.text.DecimalFormat;
import java.util.Calendar;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.app.Dialog;

import android.content.Context;
import android.content.DialogInterface;
import android.content.DialogInterface.OnCancelListener;
import android.content.Intent;
import android.content.ComponentName;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;

import android.location.Criteria;
import android.location.Location;
import android.location.LocationManager;
import android.location.LocationListener;

import android.util.Log;

import android.os.Bundle;
import android.os.AsyncTask;
import android.os.Looper;

import android.preference.PreferenceManager;

import android.net.Uri;

import android.view.View;

import android.widget.Toast;
import android.widget.Button;
import android.widget.AutoCompleteTextView;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.SimpleAdapter;
import android.widget.DatePicker;
import android.widget.TimePicker;
import android.widget.TextView;
import android.widget.ProgressBar;
import android.widget.ExpandableListView;
import android.widget.ExpandableListAdapter;
import android.widget.SimpleExpandableListAdapter;
import android.widget.ExpandableListView.OnChildClickListener;
import android.widget.ImageButton;
import android.widget.ListView;
import android.widget.AdapterView;
import android.widget.AdapterView.OnItemClickListener;
import android.widget.RadioButton;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

public class BusToursActivity extends Activity
{
	private static Context context;
    private DatePicker date;
    private TimePicker time;
    private AutoCompleteTextView txtStopDeparture;
    private Spinner sens;
    private AutoCompleteTextView txtStopArrival;
    private Spinner listCriteria;
    private ImageButton btnGetClosestStopDeparture;
    private ImageButton btnGetClosestStopArrival;
    private Button btnGetJourney;
    private RadioButton targetDeparture;
    private RadioButton targetArrival;
    private Button btnShowStops;
    private Button btnSwitchDepArr;

    private Dialog journeyList;
    private Dialog journeyDetails;
    private Dialog closestStops;

    private String[] journeyCriteriaValues;
    private String[] sensValues;

    private ArrayList<Journey> journeys;
    private int journeyDetailsProcessing;

    private URLs urls;
    private BusStops stops;
    private List<BusStop> nearests;
    private LocationManager mLocManager;
    private LocationListener locationListener;
    private String mLocProvider;
    private String geoLocTarget;
    private ProgressDialog geoLocDialog;
    private static final long maxLocationAge = 15 * 1000 * 60;
    private String mSeason;

    static int oldYear = -1;
    static int oldMonth = -1;
    static int oldDay = -1;

    private int storedVersionCode;
    private int versionCode;
    private String versionName;
    private AlertDialog updateDialog;
    private AlertDialog firstRunDialog;
    private SharedPreferences prefs;

    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);

        Log.e("BusTours", "onCreate:" + savedInstanceState);

        setContentView(R.layout.main);
        this.context = this;
        this.date               = (DatePicker)findViewById(R.id.date);
        this.time               = (TimePicker)findViewById(R.id.time);
        this.txtStopDeparture   = (AutoCompleteTextView)findViewById(R.id.txtStopDeparture);
        // this.sens               = (Spinner)findViewById(R.id.Sens);
        this.targetDeparture    = (RadioButton)findViewById(R.id.radioButtonDeparture);
        this.targetArrival    = (RadioButton)findViewById(R.id.radioButtonArrival);
        this.txtStopArrival     = (AutoCompleteTextView)findViewById(R.id.txtStopArrival);
        this.listCriteria       = (Spinner)findViewById(R.id.listCriteria);
        this.btnGetClosestStopDeparture = (ImageButton)findViewById(R.id.btnGetClosestStopDeparture);
        this.btnGetClosestStopArrival = (ImageButton)findViewById(R.id.btnGetClosestStopArrival);
        this.btnGetJourney      = (Button)findViewById(R.id.btnGetJourney);
        this.btnShowStops       = (Button)findViewById(R.id.btnShowStops);
        this.btnSwitchDepArr    = (Button)findViewById(R.id.btnSwitchDepArr);

        this.journeyCriteriaValues  = getResources().getStringArray(R.array.journeyCriteriaValues);
        this.sensValues             = getResources().getStringArray(R.array.sensValues);
        this.mSeason = SeasonPicker.pick();

        this.mLocManager = (LocationManager)getSystemService(Context.LOCATION_SERVICE);
        Criteria crit = new Criteria();
        crit.setAccuracy(Criteria.ACCURACY_FINE);
        this.mLocProvider = this.mLocManager.getBestProvider(crit, true);

        this.fill(savedInstanceState);
        this.bindWidgets();
        this.checkFirstRun();
    }

    @Override
    public void onSaveInstanceState(Bundle outState)
    {
        Log.e("BusTours", "onSaveInstanceState");
        outState.putString("arrivalStopName", this.getArrivalStopName());
        outState.putString("departureStopName", this.getDepartureStopName());
        outState.putString("mSeason", this.mSeason);
        super.onSaveInstanceState(outState);
    }

    @Override
    public void onNewIntent(Intent intent)
    {
        Log.e("BusTours", "onNewIntent");
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data)
    {
        Log.e("BusTours", "onActivityResult: " + String.valueOf(requestCode) + "; " + String.valueOf(resultCode));
        if (resultCode != RESULT_OK) {
            Log.e("BusTours", "Error selecting result, aborting.");
            return;
        }

        if (requestCode == 2) {
            this.setFromIntent(data.getExtras());
        }

        if (requestCode == 1) {
            this.setFromIntent(data.getExtras());
            closestStops.dismiss();
        }
    }

    public static String getVersionName(Context context, Class cls) {
        try {
            ComponentName comp = new ComponentName(context, cls);
            PackageInfo pinfo = context.getPackageManager().getPackageInfo(comp.getPackageName(), 0);
            return pinfo.versionName;
        } catch (NameNotFoundException e) {
            return "";
        }
    }

    public static int getVersionCode(Context context, Class cls) {
        try {
            ComponentName comp = new ComponentName(context, cls);
            PackageInfo pinfo = context.getPackageManager().getPackageInfo(comp.getPackageName(), 0);
            return pinfo.versionCode;
        } catch (NameNotFoundException e) {
            return -1;
        }
    }

    public void checkFirstRun() {
        AlertDialog d = null;
        this.versionName = BusToursActivity.getVersionName(this, BusToursActivity.class);
        this.versionCode = BusToursActivity.getVersionCode(this, BusToursActivity.class);
        this.prefs = PreferenceManager.getDefaultSharedPreferences(this);
        this.storedVersionCode = this.prefs.getInt("versionCode", -1);

        Log.e("BusTours:checkFirstRun",
              "Current version=" + this.versionCode +
              " -- stored version=" + this.storedVersionCode +
              " -- version name=" + this.versionName);

        if (this.storedVersionCode < 0){
            d = alertBox(
                    getString(R.string.msgTitleWelcome),
                    getString(R.string.msgDescWelcome) + " " + getString(R.string.msgDescWelcomeUp)
                );
        } else if (this.storedVersionCode < this.versionCode) {
            d = alertBox(
                    this.versionName + " : " + getString(R.string.msgTitleWelcomeUp),
                    getString(R.string.msgDescMajornews) + " " + getString(R.string.msgDescWelcomeUp)
                );
        }

        if (d == null) {
            Log.e("BusTours:checkFirstRun", "No dialog built, bailing out ...");
            return;
        }

		d.show();
        this.prefs.edit()
            .putInt("versionCode", this.versionCode)
            .commit();
    }

    public void resetStopsAdapter() {
        // fill stop autocomplete
        ArrayAdapter<String> stopAdapter = new ArrayAdapter<String>(this, android.R.layout.simple_dropdown_item_1line, this.stops.getStops());
        this.txtStopDeparture.setAdapter(stopAdapter);
        this.txtStopArrival.setAdapter(stopAdapter);
    }

    public void fill(Bundle state)
    {
        // fill journey criteria
        ArrayAdapter<CharSequence> criteriaAdapter = ArrayAdapter.createFromResource(this, R.array.journeyCriteria, android.R.layout.simple_spinner_item);
        criteriaAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        this.listCriteria.setAdapter(criteriaAdapter);

        /*
        // fill sens
        ArrayAdapter<CharSequence> sensAdapter = ArrayAdapter.createFromResource(this, R.array.sens, android.R.layout.simple_spinner_item);
        sensAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        this.sens.setAdapter(sensAdapter);
        */

        if (state != null) {
            Log.e("BusTours:Bundle", "Restoring values ...");
            this.setDepartureStopName(state.getString("departureStopName"));
            this.setArrivalStopName(state.getString("arrivalStopName"));
            this.mSeason = state.getString("mSeason");
        }

        this.stops = new BusStops(this.mSeason);
        this.resetStopsAdapter();
        this.setFromIntent(getIntent().getExtras());
    }

    public void setFromIntent(Bundle extras)
    {
        if (extras != null) {
            Log.e("BusTours:Bundle", "Got bundle!");
            String sens = (String)extras.get("sens");
            String stop = (String)extras.get("stop");
            Log.e("BusTours:Bundle", "Got sens=" + sens);
            Log.e("BusTours:Bundle", "Got stop=" + stop);
            if (sens.contains(getString(R.string.sens_departure))) {
                this.setDepartureStopName(stop);
            }
            if (sens.contains(getString(R.string.sens_arrival))) {
                this.setArrivalStopName(stop);
            }
        }
    }

    public void bindWidgets()
    {
        this.txtStopDeparture.setThreshold(2);
        this.txtStopArrival.setThreshold(2);
        Calendar cal = Calendar.getInstance();
        this.date.init(
            cal.get(Calendar.YEAR),
            cal.get(Calendar.MONTH),
            cal.get(Calendar.DAY_OF_MONTH),
            new DatePicker.OnDateChangedListener() {
                public void onDateChanged(DatePicker view, int year, int monthOfYear, int dayOfMonth) {
                    onDateChanged_date(year, monthOfYear, dayOfMonth);
                };
        });
        this.time.setIs24HourView(true);
        this.btnGetClosestStopDeparture.setOnClickListener(new View.OnClickListener() { public void onClick(View arg0) { onClick_btnGetClosestStopDeparture(); } });
        this.btnGetClosestStopArrival.setOnClickListener(new View.OnClickListener() { public void onClick(View arg0) { onClick_btnGetClosestStopArrival(); } });
        this.btnGetJourney.setOnClickListener(new View.OnClickListener() { public void onClick(View arg0) { onClick_btnGetJourney(); } });
        this.btnShowStops.setOnClickListener(new View.OnClickListener() { public void onClick(View arg0) { onClick_btnShowStops(); } });
        this.btnSwitchDepArr.setOnClickListener(new View.OnClickListener() { public void onClick(View arg0) { onClick_btnSwitchDepArr(); } });
    }

    public int getJourneyCriteriaValue()
    {
        return Integer.parseInt(this.journeyCriteriaValues[this.listCriteria.getSelectedItemPosition()]);
    }

    public int getSensValue()
    {
        // return Integer.parseInt(this.sensValues[this.sens.getSelectedItemPosition()]);
        int retval = 0;

        if (this.targetDeparture.isChecked()) retval = 1;
        if (this.targetArrival.isChecked()) retval = -1;

        return retval;
    }

    public void onClick_btnGetJourney()
    {
        String dep = this.getDepartureStopName();
        String arr = this.getArrivalStopName();

        if (dep.length() < 1 || arr.length() < 1) {
            this.alertErrorBox(getString(R.string.missingValues), getString(R.string.descMissingValues));
            return;
        }

        String[] cityStopDep = this.stops.getStopCity(dep);
        String[] cityStopArr = this.stops.getStopCity(arr);

        if (cityStopDep[0] == null || cityStopDep[1] == null) {
            this.alertErrorBox(getString(R.string.invalidValues), getString(R.string.descInvalidValuesDep));
            return;
        }

        if (cityStopArr[0] == null || cityStopArr[1] == null) {
            this.alertErrorBox(getString(R.string.invalidValues), getString(R.string.descInvalidValuesArr));
            return;
        }

        BusJourney j = new BusJourney();
        j.setCityDep(cityStopDep[1]);
        j.setCityArr(cityStopArr[1]);
        j.setStopDep(cityStopDep[0]);
        j.setStopArr(cityStopArr[0]);
        j.setDate(new String()
            + String.valueOf(this.date.getDayOfMonth())
            + "/"
            + String.valueOf(this.date.getMonth() + 1)
            + "/"
            + String.valueOf(this.date.getYear())
        );
        j.setHour(String.valueOf(this.time.getCurrentHour()));
        j.setMinute(String.valueOf(this.time.getCurrentMinute()));
        j.setSens(String.valueOf(this.getSensValue()));
        j.setCriteria(String.valueOf(this.getJourneyCriteriaValue()));

        new ProcessScrapping().execute(j);
    }

    public void onClick_btnSwitchDepArr() {
        String dep = this.getDepartureStopName();
        String arr = this.getArrivalStopName();
        this.setDepartureStopName(arr);
        this.setArrivalStopName(dep);
    }

    public void onClick_btnShowStops() {
        List<BusStop> stops = this.stops.getStopsList();

        String[] stopsNames = new String[stops.size()];
        double[] latitudes = new double[stops.size()];
        double[] longitudes = new double[stops.size()];

        Iterator it = stops.iterator();
        int pos = 0;
        while(it.hasNext()) {
            BusStop bs = (BusStop)it.next();
            stopsNames[pos] = bs.name;
            latitudes[pos] = bs.lat;
            longitudes[pos] = bs.lon;
            pos += 1;
        }

        this.startStopsMapActivity(stopsNames, latitudes, longitudes, true, true);
    }

    public void updateLocation(String target) {
        this.setGeoLocTarget(target);

        Location lastKnown = this.getLastLocation();
        if (lastKnown == null) {
            Log.e("BusTours", "Location missing.");
        } else {
            long age = lastKnown.getTime() - System.currentTimeMillis();
            Log.e("BusTours", "Location age: " + String.valueOf(age) + "ms");
            if (age > this.maxLocationAge) {
                /* Location is not that old, keep it ... */
                Log.e("BusTours", "Location is good, keep it.");
                buildClosestStopsUi(getGeoLocTarget());
                return;
            }
        }

        Log.e("BusTours", "Location is too old, request update.");

        geoLocDialog = ProgressDialog.show(
            context, getString(R.string.waitLoc),
            getString(R.string.waitingForGeolocation),
            true, true,
                new DialogInterface.OnCancelListener() {
                    public void onCancel(DialogInterface dialog) {
                        getLocationManager().removeUpdates(getLocationListener());
                        Log.e("BusTours", "Location is old, but user want to use it.");
                        buildClosestStopsUi(getGeoLocTarget());
                    }
                }
            );

        this.locationListener = new LocationListener() {
            @Override
            public void onStatusChanged(String provider, int status, Bundle extras) {
                Log.v("BusTours:LocationListener", "onStatusChanged");
            }

            @Override
            public void onProviderEnabled(String provider) {
                Log.v("BusTours:LocationListener", "onProviderEnabled");
            }

            @Override
            public void onProviderDisabled(String provider) {
                Log.v("BusTours:LocationListener", "onProviderDisabled");
            }

            @Override
            public void onLocationChanged(Location location) {
                Log.v("BusTours:LocationListener", "onLocationChanged");
                getLocationManager().removeUpdates(this);
                buildClosestStopsUi(getGeoLocTarget());
                geoLocDialog.dismiss();
            }
        };

        this.mLocManager.requestLocationUpdates(this.mLocProvider, 0, 0, locationListener);
    }

    public void onClick_btnGetClosestStopDeparture() {
        this.updateLocation("dep");
    }

    public void onClick_btnGetClosestStopArrival() {
        this.updateLocation("arr");
    }

    public void onDateChanged_date(int year, int month, int day) {
        if (this.oldYear == year && this.oldMonth == month && this.oldDay == day) {
            Log.e("BusTours:DateChanged", "Same date ...");
            return;
        }

        this.oldYear = year;
        this.oldMonth = month;
        this.oldDay = day;

        Log.e("BusTours:DateChanged", "Set to " + year + "/" + (month+1) + "/" + day);
        if (!SeasonPicker.checkDate(this.mSeason, year, month, day)) {
            this.alertInfoBox(getString(R.string.invalidDate), getString(R.string.descInvalidDate));
            Calendar date = Calendar.getInstance();
            date.set(year, month, day);
            this.mSeason = SeasonPicker.pickFromDate(date);
            Log.e("BusTours:DateChanged", "Reloading with " + this.mSeason);
            this.stops = new BusStops(this.mSeason);
            this.resetStopsAdapter();
            this.setDepartureStopName("");
            this.setArrivalStopName("");
        }
    }

    public String getGeoLocTarget() {
        return this.geoLocTarget;
    }

    public void setGeoLocTarget(String v) {
        this.geoLocTarget = v;
    }

    public void setDepartureStopName(String name) {
        this.txtStopDeparture.setText(name);
    }

    public void setArrivalStopName(String name) {
        this.txtStopArrival.setText(name);
    }

    public String getDepartureStopName() {
        return this.txtStopDeparture.getEditableText().toString();
    }

    public String getArrivalStopName() {
        return this.txtStopArrival.getEditableText().toString();
    }

    public List<BusStop> getNearests() {
        return this.nearests;
    }

    public BusStop getNearest(int pos) {
        return this.nearests.get(pos);
    }

    public Location getLastLocation() {
        return this.mLocManager.getLastKnownLocation(this.mLocProvider);
    }

    public LocationManager getLocationManager() {
        return this.mLocManager;
    }

    public LocationListener getLocationListener() {
        return this.locationListener;
    }

    public void buildClosestStopsUi(String type) {
        ArrayAdapter<String> stopsAdapter = this.buildClosestStopsAdapter();
        if (stopsAdapter.getCount() < 1) {
            Log.e("BusTours", "No stop. Dismissing dialog.");
            return;
        }

        closestStops = new Dialog(context);
        closestStops.setContentView(R.layout.closest);
        closestStops.setTitle(getString(R.string.closest_stops));
        Button btnWhereAmI = (Button)closestStops.findViewById(R.id.btnWhereAmI);

        btnWhereAmI.setOnClickListener(new View.OnClickListener() {
            public void onClick(View arg0) {
                showClosestStopsMap();
            }
        });

        ListView list = (ListView)closestStops.findViewById(R.id.listClosestStops);
        if (type.equals("dep")) {
            list.setOnItemClickListener(new OnItemClickListener() {
                public void onItemClick(AdapterView<?> parent, View v, int position, long id) {
                    BusStop bs = getNearest(position);
                    if (bs != null) {
                        setDepartureStopName(bs.name);
                        closestStops.dismiss();
                    }
                }
            });
        }
        if (type.equals("arr")) {
            list.setOnItemClickListener(new OnItemClickListener() {
                public void onItemClick(AdapterView<?> parent, View v, int position, long id) {
                    BusStop bs = getNearest(position);
                    if (bs != null) {
                        setArrivalStopName(bs.name);
                        closestStops.dismiss();
                    }
                }
            });
        }
        list.setAdapter(stopsAdapter);
        list.setChoiceMode(ListView.CHOICE_MODE_SINGLE);

        closestStops.show();
    }

    public ArrayAdapter<String> buildClosestStopsAdapter() {
        this.getClosestStops();
        DecimalFormat df = new DecimalFormat("###");
        List<String> listClosest = new ArrayList<String>();

        if (this.nearests != null) {
            Iterator itMinDist = this.nearests.iterator();
            while(itMinDist.hasNext()) {
                BusStop bs = (BusStop)itMinDist.next();
                listClosest.add(new String(bs.name + " (" + df.format(bs.dist) + "m)"));
            }
        }

        return new ArrayAdapter<String>(this, android.R.layout.simple_list_item_1, listClosest);
    }

    public void getClosestStops() {
        List<BusStop> nearests = null;
        Log.e("BusTours", "Using provider: " + this.mLocProvider);
        Location lastLoc = this.getLastLocation();
        if (lastLoc == null) {
            Log.e("BusTours", "No last known location");
            this.alertInfoBox(getString(R.string.noLocation), getString(R.string.descNoLocation));
        } else {
            Log.e("BusTours", "From provider: " + lastLoc.getProvider() + ", fix time at " + lastLoc.getTime());
            Log.e("BusTours", "Current lastKnown (lat;lon)=(" + String.valueOf(lastLoc.getLatitude()) + ";" + String.valueOf(lastLoc.getLongitude()) + ")");
            this.nearests = this.stops.getNearestStop(lastLoc.getLatitude(), lastLoc.getLongitude());
            Iterator itMinDist = this.nearests.iterator();
            while(itMinDist.hasNext()) {
                BusStop bs = (BusStop)itMinDist.next();
                Log.e("BusTours", "Closest bus stop at (lat;lon)=(" + String.valueOf(bs.lat) + ";" + String.valueOf(bs.lon) + ") :: " + bs.name + " is " + bs.dist + "m");
            }
        }
    }

    public static void messageBox(String text) {
		Toast.makeText(context,text, Toast.LENGTH_SHORT).show();
	}

	public AlertDialog alertBox(String title, String text) {
		AlertDialog.Builder dialog = new AlertDialog.Builder(this.context);
		dialog.setTitle(title);
		dialog.setMessage(text);
		dialog.setCancelable(false);
		dialog.setPositiveButton(
			getString(R.string.okay),
			new DialogInterface.OnClickListener() {
				public void onClick(DialogInterface dialog, int id) {
					dialog.cancel();
				}
			}
		);
		return dialog.create();
	}

	public void alertInfoBox(String title, String text) {
		AlertDialog d = alertBox("[" + getString(R.string.msgInfoTitle) + "]: " + title, text);
		d.show();
	}

	public void alertErrorBox(String title, String text) {
		AlertDialog d = alertBox("[" + getString(R.string.msgErrorTitle) + "]: " + title, text);
		d.show();
	}

    public void setJourneys(ArrayList<Journey> js) {
        this.journeys = js;
    }

    public ArrayList<Journey> getJourneys() {
        return this.journeys;
    }

    public void setJourneyDetailsProcessing(int v) {
        this.journeyDetailsProcessing = v;
    }

    public void onAsyncTaskScrapJourneyDetailsComplete() {
        Log.e("BusTours", "Got details for " + this.journeyDetailsProcessing);
        Journey targetJourney = this.journeys.get(this.journeyDetailsProcessing);
        JourneyDetails details = targetJourney.getJourneyDetails();

        if (details == null) {
            Log.e("BusTours", "No details available for " + this.journeyDetailsProcessing);
            this.alertInfoBox(getString(R.string.noDetails), getString(R.string.noDetailsTxt));
            return;
        }

        ExpandableListView list;
        journeyDetails = new Dialog(this);
        journeyDetails.setContentView(R.layout.details);
        journeyDetails.setTitle(getString(R.string.journey_details));

        String[] fromGroup = new String[] { "head" };
        int[] toGroup = new int[] { android.R.id.text1 };
        String[] fromChild = new String[] { "head", "more" };
        int[] toChild = new int[] { android.R.id.text1, android.R.id.text2 };

        List<HashMap<String, String>> jList = new ArrayList<HashMap<String, String>>();
        List<List<HashMap<String, String>>> jListChild = new ArrayList<List<HashMap<String, String>>>();

        Iterator<JourneyDetails.JourneyPart> jit = details.getParts().iterator();
        while (jit.hasNext()) {
            JourneyDetails.JourneyPart jp = (JourneyDetails.JourneyPart)jit.next();
            JourneyDetails.Indication indic = jp.getIndic();
            HashMap<String, String> map = new HashMap<String, String>();
            List<HashMap<String, String>> children = new ArrayList<HashMap<String, String>>();
            HashMap<String, String> curChildMap = new HashMap<String, String>();

            if (jp.getType().equals("indication")) {
                if (indic.getType().equals("mount")) {
                    map.put("head", jp.getTime() + ": " + getString(R.string.stopIndic) + " '" + indic.getStop() + "'");
                    curChildMap.put("head", getString(R.string.detailLine) + " " + indic.getLine());
                    curChildMap.put("more", getString(R.string.detailDirection) + " " + indic.getDirection());
                }

                if (indic.getType().equals("umount")) {
                    map.put("head", jp.getTime() + ": " + getString(R.string.stopIndic) + " '" + indic.getStop() + "'");
                    curChildMap.put("head", getString(R.string.detailUmount));
                    curChildMap.put("more", "");
                }

                if (indic.getType().equals("walk")) {
                    map.put("head", getString(R.string.walkIndic) + " '" + indic.getStop() + "'" + " (" + jp.getDuration() + ")");
                    curChildMap.put("head", getString(R.string.detailWalkTo) + " " + indic.getDirection());
                    curChildMap.put("more", getString(R.string.detailWalkFrom) + " " + indic.getStop());
                }
            }

            if (jp.getType().equals("connection")) {
                map.put("head", getString(R.string.connectionInfo));
                curChildMap.put("head", getString(R.string.connectionDuration) + " " + jp.getDuration());
                curChildMap.put("more", "");
            }

            children.add(curChildMap);
            jListChild.add(children);
            jList.add(map);
        }

        list = (ExpandableListView)journeyDetails.findViewById(R.id.listJourneyDetails);
        ExpandableListAdapter journeyDetailsAdapter = new SimpleExpandableListAdapter(
            this,
            jList,
            android.R.layout.simple_expandable_list_item_2,
            fromGroup, toGroup,
            jListChild,
            android.R.layout.simple_expandable_list_item_2,
            fromChild, toChild
        );

        list.setAdapter(journeyDetailsAdapter);

        journeyDetails.show();
    }

    public void onAsyncTaskScrapJourneyListComplete() {
        if (this.journeys == null) {
            Log.e("BusTours", "No journey to display");
            return;
        }

        ExpandableListView list;
        journeyList = new Dialog(this);
        journeyList.setContentView(R.layout.journey);
        journeyList.setTitle(getString(R.string.journey_list));

        String[] fromGroup = new String[] { "head" };
        int[] toGroup = new int[] { android.R.id.text1 };
        String[] fromChild = new String[] { "head", "more" };
        int[] toChild = new int[] { android.R.id.text1, android.R.id.text2 };

        List<HashMap<String, String>> jList = new ArrayList<HashMap<String, String>>();
        List<List<HashMap<String, String>>> jListChild = new ArrayList<List<HashMap<String, String>>>();

        Iterator<Journey> jit = this.journeys.iterator();
        while (jit.hasNext()) {
            Journey j = (Journey)jit.next();

            HashMap<String, String> map = new HashMap<String, String>();
            map.put("head", j.getDepartureTime() + " - " + j.getArrivalTime() + " (" + j.getDuration() + ")");

            List<HashMap<String, String>> children = new ArrayList<HashMap<String, String>>();

            HashMap<String, String> curChildMap = new HashMap<String, String>();
            curChildMap.put("head", getString(R.string.duration) + " " + j.getDuration());
            curChildMap.put("more", getString(R.string.connections) + " " + j.getConnections());
            children.add(curChildMap);

            jListChild.add(children);

            jList.add(map);
        }

        list = (ExpandableListView)journeyList.findViewById(R.id.listJourneys);
        list.setOnChildClickListener(new OnChildClickListener() {
            public boolean onChildClick(ExpandableListView parent, View v, int groupPosition, int childPosition, long id) {
                try {
                    Journey journey = getJourneys().get(groupPosition);
                    setJourneyDetailsProcessing(groupPosition);
                    Log.e("BusTours", "groupPosition:" + String.valueOf(groupPosition));
                    Log.e("BusTours", "journey:" + journey);
                    if (journey.getJourneyDetails() == null) {
                        Log.e("BusTours", "No details for this journey, starting scrapping ...");
                        new ProcessScrapping().execute(journey);
                    } else {
                        Log.e("BusTours", "Details already available.");
                        onAsyncTaskScrapJourneyDetailsComplete();
                    }
                } catch(Exception e) {
                    e.printStackTrace();
                }
                return false;
            }
        });

        ExpandableListAdapter journeyAdapter = new SimpleExpandableListAdapter(
            this,
            jList,
            android.R.layout.simple_expandable_list_item_2,
            fromGroup, toGroup,
            jListChild,
            android.R.layout.simple_expandable_list_item_2,
            fromChild, toChild
        );

        list.setAdapter(journeyAdapter);

        journeyList.show();
    }

    public class ProcessScrapping extends AsyncTask<Object, Integer, Boolean> {
        private Exception exc;
        private String processing;

        // Showing Async progress
        private Dialog dialog;
        private TextView statusProgressHttp;
        private ProgressBar progressHttp;

        public void progress(Integer ... progress) {
            this.publishProgress(progress);
        }

        protected void onPreExecute() {
            dialog = new Dialog(context);
            dialog.setContentView(R.layout.progress);
            dialog.setTitle(getString(R.string.scrapping));

            statusProgressHttp = (TextView) dialog.findViewById(R.id.statusProgressHttp);
            progressHttp = (ProgressBar) dialog.findViewById(R.id.progressHttp);
            progressHttp.setMax(100);

            dialog.show();
        }

        protected Boolean doInBackground(Object ... journey) {
            String className = journey[0].getClass().getSimpleName();
            publishProgress(0, R.string.startHttpScrapping);

            Log.e("BusTours", "Processing " + className);
            this.processing = className;

            try {
                publishProgress(10, R.string.jsoupConnect);
                if (className.equals("BusJourney")) {
                    setJourneys(null);
                    BusJourney j = (BusJourney)journey[0];
                    setJourneys(j.getBusJourneys(this));
                }
                if (className.equals("Journey")) {
                    Journey j = (Journey)journey[0];
                    j.getDetails(this);
                }
                publishProgress(100, R.string.jsoupDocReady);
                return true;
            } catch (Exception e) {
                this.exc = e;
                e.printStackTrace();
                return false;
            }
        }

        protected void onProgressUpdate(Integer ... progress) {
            progressHttp.setProgress(progress[0]);
            statusProgressHttp.setText(getString(progress[1]));
        }

        protected void onPostExecute(Boolean result) {
            dialog.dismiss();

            if (!result) {
                String excName = this.exc.getClass().getSimpleName();
                String msg = "";

                Log.e("BusTours", "Got exception: " + excName);

                if (excName.equals("SocketTimeoutException")) {
                    Log.e("BusTours", "Got SocketTimeoutException");
                    msg = getString(R.string.networkError);
                }

                if (excName.equals("IOException")) {
                    Log.e("BusTours", "Got IOException");
                }

                if (excName.equals("ScrappingException")) {
                    Log.e("BusTours", "Got ScrappingException");
                    ScrappingException e = (ScrappingException)(this.exc);
                    msg = getString(R.string.scrappError) + ": " + e.getError();
                }

                if (msg.length() != 0) {
                    Log.e("BusTours", "msg=" + msg);
                    alertErrorBox(excName, msg);
                }
            }

            if (this.processing.equals("BusJourney")) {
                onAsyncTaskScrapJourneyListComplete();
            }

            if (this.processing.equals("Journey")) {
                onAsyncTaskScrapJourneyDetailsComplete();
            }
        }
    }

    /**
     * all arrays must be of the same size
     **/
    public void startStopsMapActivity(String[] stopsNames, double[] latitudes, double[] longitudes, boolean selectDeparture, boolean selectArrival) {

        int req = 1;
        Intent intentStopsView = new Intent(this, StopsMapActivity.class);

        intentStopsView.putExtra("stopsNames", stopsNames);
        intentStopsView.putExtra("mSeason", this.mSeason);
        intentStopsView.putExtra("latitudes", latitudes);
        intentStopsView.putExtra("longitudes", longitudes);
        intentStopsView.putExtra("location", this.getLastLocation());

        intentStopsView.putExtra("selectDeparture", selectDeparture);
        intentStopsView.putExtra("selectArrival", selectArrival);

        if (selectDeparture && selectArrival) {
            req = 2;
        }

        startActivityForResult(intentStopsView, req);
    }

    public void showClosestStopsMap() {
        String[] stopsNames = new String[10];
        double[] latitudes = new double[10];
        double[] longitudes = new double[10];
        String type = this.getGeoLocTarget();

        List<BusStop> stops = this.getNearests();
        if (stops != null) {
            Iterator it = stops.iterator();
            int pos = 0;
            while(it.hasNext()) {
                BusStop bs = (BusStop)it.next();
                stopsNames[pos] = bs.name;
                latitudes[pos] = bs.lat;
                longitudes[pos] = bs.lon;
                pos += 1;
            }
        }

        this.startStopsMapActivity(stopsNames, latitudes, longitudes, (type == "dep"), (type == "arr"));
    }
}

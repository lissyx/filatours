/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.util.ArrayList;
import java.util.List;
import java.util.Iterator;

import android.util.Log;

import android.os.Bundle;

import android.location.Location;

import android.widget.Toast;
import android.widget.EditText;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;

import android.app.AlertDialog;

import android.content.Context;
import android.content.DialogInterface;
import android.content.DialogInterface.OnCancelListener;
import android.content.Intent;

import android.graphics.drawable.Drawable;

import android.view.Menu;
import android.view.MenuItem;
import android.view.MenuInflater;

import org.osmdroid.util.GeoPoint;
import org.osmdroid.util.BoundingBoxE6;
import org.osmdroid.views.overlay.ItemizedIconOverlay;
import org.osmdroid.views.overlay.ItemizedOverlay;
import org.osmdroid.views.overlay.OverlayItem;
import org.osmdroid.DefaultResourceProxyImpl;
import org.osmdroid.ResourceProxy;

import org.osmdroid.events.MapListener;
import org.osmdroid.events.ZoomEvent;
import org.osmdroid.events.ScrollEvent;

public class StopsMapActivity extends MapViewActivity
{
	private static Context context;
    private String[] stopsNames;
    private double[] latitudes;
    private double[] longitudes;
    private boolean dep;
    private boolean arr;
    private Location whereAmI;
    private BoundingBoxE6 bbox;
    private Drawable stopsMarker;
    private Drawable posMarker;
    private boolean saveBBOX;
    private CharSequence[] selectStopsItems;
    private String selectedStop;
    private boolean showStopsOverlay;
    private BusStops stops;

    private ItemizedIconOverlay<OverlayItem> stopsOverlay;
    private ItemizedIconOverlay<OverlayItem> myLocationOverlay;
    private ItemizedIconOverlay<OverlayItem> searchOverlay;
    private ArrayList<OverlayItem> search;
    private ResourceProxy mResourceProxy;

    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        double bboxNorth = 0, bboxEast = 0, bboxSouth = 0, bboxWest = 0;
        super.onCreate(savedInstanceState);

        this.context = this;

        this.mResourceProxy = new DefaultResourceProxyImpl(getApplicationContext());
        this.stopsMarker = this.mResourceProxy.getDrawable(ResourceProxy.bitmap.marker_default);
        this.posMarker = this.mResourceProxy.getDrawable(ResourceProxy.bitmap.center);
        ArrayList<OverlayItem> items = new ArrayList<OverlayItem>();
        ArrayList<OverlayItem> pos = new ArrayList<OverlayItem>();
        this.search = new ArrayList<OverlayItem>();
        this.saveBBOX = true;
        this.showStopsOverlay = false;

        Bundle extras = getIntent().getExtras();
        if (extras != null) {
            this.stopsNames = extras.getStringArray("stopsNames");
            this.latitudes = extras.getDoubleArray("latitudes");
            this.longitudes = extras.getDoubleArray("longitudes");
            this.whereAmI = (Location)extras.get("location");
            this.dep = extras.getBoolean("selectDeparture");
            this.arr = extras.getBoolean("selectArrival");

            if (this.dep && this.arr) {
                this.selectStopsItems = new CharSequence[] { getString(R.string.sens_departure), getString(R.string.sens_arrival) };
            } else {
                if (this.dep) {
                    this.selectStopsItems = new CharSequence[] { getString(R.string.sens_departure) };
                }
                if (this.arr) {
                    this.selectStopsItems = new CharSequence[] { getString(R.string.sens_arrival) };
                }
            }
        }

        if (this.stopsNames != null && this.latitudes != null && this.longitudes != null) {
            if (this.stopsNames.length == this.latitudes.length && this.latitudes.length == this.longitudes.length && this.longitudes.length > 0) {
                // Log.e("BusTours:StopsMaps", "Got some points ...");
                int i;
                double minNorth = 180, minEast = 180, maxSouth = -180, maxWest = -180;
                for (i = 0; i < this.stopsNames.length; i++) {
                    // Log.e("BusTours:StopsMaps", "Stops @ (" + String.valueOf(this.latitudes[i]) + ", " + String.valueOf(this.longitudes[i]) + ") == " + this.stopsNames[i]);
                    items.add(new OverlayItem(this.stopsNames[i], this.stopsNames[i], new GeoPoint((int)(this.latitudes[i]*1e6), (int)(this.longitudes[i]*1e6))));
                    if (this.latitudes[i] < minNorth) {
                        minNorth = this.latitudes[i];
                    }
                    if (this.latitudes[i] > maxSouth) {
                        maxSouth = this.latitudes[i];
                    }
                    if (this.longitudes[i] < minEast) {
                        minEast = this.longitudes[i];
                    }
                    if (this.longitudes[i] > maxWest) {
                        maxWest = this.longitudes[i];
                    }
                }
                // Log.e("BusTours:StopsMaps", "minEast=" + String.valueOf(minEast));
                // Log.e("BusTours:StopsMaps", "maxWest=" + String.valueOf(maxWest));
                // Log.e("BusTours:StopsMaps", "minNorth=" + String.valueOf(minNorth));
                // Log.e("BusTours:StopsMaps", "maxSouth=" + String.valueOf(maxSouth));
                bboxNorth = minNorth;
                bboxEast = minEast;
                bboxSouth = maxSouth;
                bboxWest = maxWest;
            }
        }

        this.bbox = new BoundingBoxE6(bboxNorth, bboxEast, bboxSouth, bboxWest);

        /* OnTapListener for the Markers, shows a simple Toast. */
        this.stopsOverlay = new ItemizedIconOverlay<OverlayItem>(items,
            this.stopsMarker,
            new ItemizedIconOverlay.OnItemGestureListener<OverlayItem>() {
                @Override
                public boolean onItemSingleTapUp(final int index,
                        final OverlayItem item) {
                    displayStopInfos(item);
                    return true; // We 'handled' this event.
                }
                @Override
                public boolean onItemLongPress(final int index,
                        final OverlayItem item) {
                    selectStop(item);
                    return false;
                }
            }, mResourceProxy);

        if (this.whereAmI != null) {
            pos.add(new OverlayItem(getString(R.string.your_location), getString(R.string.your_location), new GeoPoint((int)(this.whereAmI.getLatitude()*1e6), (int)(this.whereAmI.getLongitude()*1e6))));
        } else {
            Toast.makeText(StopsMapActivity.this, getString(R.string.missing_location), Toast.LENGTH_LONG).show();
        }
        this.myLocationOverlay = new ItemizedIconOverlay<OverlayItem>(
            pos,
            this.posMarker,
            new ItemizedIconOverlay.OnItemGestureListener<OverlayItem>() {
                @Override
                public boolean onItemSingleTapUp(final int index,
                        final OverlayItem item) {
                    Toast.makeText(
                            StopsMapActivity.this,
                            item.mTitle, Toast.LENGTH_LONG).show();
                    return true; // We 'handled' this event.
                }
                @Override
                public boolean onItemLongPress(final int index,
                        final OverlayItem item) {
                    Toast.makeText(
                            StopsMapActivity.this,
                            item.mTitle ,Toast.LENGTH_LONG).show();
                    return false;
                }
            }, mResourceProxy);
        this.searchOverlay = new ItemizedIconOverlay<OverlayItem>(
            search,
            this.stopsMarker,
            new ItemizedIconOverlay.OnItemGestureListener<OverlayItem>() {
                @Override
                public boolean onItemSingleTapUp(final int index,
                        final OverlayItem item) {
                    displayStopInfos(item);
                    return true; // We 'handled' this event.
                }
                @Override
                public boolean onItemLongPress(final int index,
                        final OverlayItem item) {
                    selectStop(item);
                    return false;
                }
            }, mResourceProxy);

        this.getOsmMap().getOverlays().add(this.myLocationOverlay);
        this.getOsmMap().getOverlays().add(this.searchOverlay);
        this.getOsmMap().setMapListener(new MapListener() {
            public boolean onScroll(ScrollEvent event) {
                // Log.e("BusTours:StopsMap", "ScrollEvent");
                if (saveBBOX) {
                    bbox = getOsmMap().getBoundingBox();
                }
                return true;
            }
            public boolean onZoom(ZoomEvent event) {
                // Log.e("BusTours:StopsMap", "ZoomEvent");
                if (saveBBOX) {
                    bbox = getOsmMap().getBoundingBox();
                }
                return true;
            }
        });

        if (!this.showStopsOverlay) {
            Toast.makeText(StopsMapActivity.this, getString(R.string.stops_overlay), Toast.LENGTH_LONG).show();
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        MenuInflater inflater = getMenuInflater();
        inflater.inflate(R.menu.stops, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle item selection
        switch (item.getItemId()) {
            case R.id.layerSwitcher:
                if (this.showStopsOverlay) {
                    this.showStopsOverlay = false;
                    item.setTitle(R.string.layerSwitcher_enable);
                } else {
                    this.showStopsOverlay = true;
                    item.setTitle(R.string.layerSwitcher_disable);
                }
                this.updateStopsOverlay();
                return true;
            case R.id.searchStop:
                this.enterStopSearch();
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus)
    {
        if (hasFocus) {
            this.saveBBOX = false;
            Log.e("BusTours:StopsMap", "Got focus, zooming to " + this.bbox);
            Log.e("BusTours:StopsMap", "Targeting &lat=" + (this.bbox.getCenter().getLatitudeE6()/1E6) + "&lon=" + (this.bbox.getCenter().getLongitudeE6()/1E6) + "&zoom=15");
            this.getOsmMap().getController().setCenter(this.bbox.getCenter());
            this.getOsmMap().getController().zoomToSpan(this.bbox);
            this.saveBBOX = true;
        }
    }

    public void enterStopSearch()
    {
        this.stops = new BusStops();
        ArrayAdapter<String> stopAdapter = new ArrayAdapter<String>(this, android.R.layout.simple_dropdown_item_1line, this.stops.getStops());
        final AutoCompleteTextView inputStop = new AutoCompleteTextView(this);
        inputStop.setThreshold(1);
        inputStop.setAdapter(stopAdapter);
        AlertDialog.Builder dialog = new AlertDialog.Builder(StopsMapActivity.this);
        dialog.setTitle(getString(R.string.stop_search));
        dialog.setMessage(getString(R.string.stop_search_msg));
        dialog.setView(inputStop);
        dialog.setPositiveButton(
            getString(R.string.okay),
            new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int id) {
                    String stop = inputStop.getText().toString();
                    Log.e("BusTours:StopsMap", "Searching for: " + stop);
                    searchStop(stop);
                    dialog.dismiss();
                }
            }
        );
        dialog.setNegativeButton(
            getString(R.string.cancel),
            new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int id) {
                    dialog.cancel();
                }
            }
        );

        AlertDialog d = dialog.create();
        d.show();
    }

    public void searchStop(String name)
    {
        BusStops.BusStop foundStop = this.stops.findStop(name);
        if (foundStop == null) {
            Toast.makeText(StopsMapActivity.this, getString(R.string.no_search_result), Toast.LENGTH_LONG).show();
            return;
        }
        Log.e("BusTours:StopsMap", "Found: " + foundStop.name);

        GeoPoint target = new GeoPoint((int)(foundStop.lat*1e6), (int)(foundStop.lon*1e6));

        double minNorth = target.getLatitudeE6()/1E6, minEast = target.getLongitudeE6()/1E6, maxSouth = target.getLatitudeE6()/1E6, maxWest = target.getLongitudeE6()/1E6;

        Iterator it = this.search.iterator();
        while(it.hasNext()) {
            OverlayItem i = (OverlayItem)it.next();
            GeoPoint geo = i.getPoint();

            if ((geo.getLatitudeE6()/1E6) < minNorth) {
                minNorth = (geo.getLatitudeE6()/1E6);
            }
            if ((geo.getLatitudeE6()/1E6) > maxSouth) {
                maxSouth = (geo.getLatitudeE6()/1E6);
            }
            if ((geo.getLongitudeE6()/1E6) < minEast) {
                minEast = (geo.getLongitudeE6()/1E6);
            }
            if ((geo.getLongitudeE6()/1E6) > maxWest) {
                maxWest = (geo.getLongitudeE6()/1E6);
            }
        }

        this.saveBBOX = false;
        this.bbox = new BoundingBoxE6(minNorth, minEast, maxSouth, maxWest);
        Log.e("BusTours:StopsMap", "Found bounding box: " + this.bbox);
        this.getOsmMap().getController().setCenter(target);
        this.getOsmMap().getController().zoomToSpan(this.bbox);
        this.searchOverlay.addItem(new OverlayItem(foundStop.name, foundStop.name, target));
        this.saveBBOX = true;
    }

    public void displayStopInfos(OverlayItem item)
    {
        AlertDialog.Builder dialog = new AlertDialog.Builder(StopsMapActivity.this);
        dialog.setTitle(getString(R.string.stop_info));
        dialog.setMessage(getString(R.string.stop_info_msg) + " " + item.mTitle);
        dialog.setPositiveButton(
            getString(R.string.okay),
            new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int id) {
                    dialog.cancel();
                }
            }
        );

        AlertDialog d = dialog.create();
        d.show();
    }

    public void selectStop(OverlayItem item)
    {
        this.selectedStop = item.mTitle;
        AlertDialog.Builder dialog = new AlertDialog.Builder(StopsMapActivity.this);
        dialog.setTitle(item.mTitle);
        // dialog.setMessage(getString(R.string.select_stop_msg) + " " + item.mTitle);
        dialog.setSingleChoiceItems(
            selectStopsItems, -1,
            new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int id) {
                    dialog.dismiss();
                    pushBackSelectedStop(id);
                }
            }
        );

        AlertDialog d = dialog.create();
        d.show();
    }

    public void pushBackSelectedStop(int id)
    {
        Log.e("BusTours:StopsMap", "checked: " + this.selectStopsItems[id]);
        Intent intentMainView = this.getIntent();
        intentMainView.putExtra("sens", selectStopsItems[id]);
        intentMainView.putExtra("stop", selectedStop);
        this.setResult(RESULT_OK, intentMainView);
        this.finish();
    }

    public void updateStopsOverlay()
    {
        if (this.showStopsOverlay) {
            this.getOsmMap().getOverlays().add(this.stopsOverlay);
        } else {
            this.getOsmMap().getOverlays().remove(this.stopsOverlay);
        }
        this.getOsmMap().invalidate();
    }
}

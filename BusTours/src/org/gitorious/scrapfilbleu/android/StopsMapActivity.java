/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.util.ArrayList;

import android.util.Log;

import android.os.Bundle;

import android.widget.Toast;

import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.overlay.ItemizedIconOverlay;
import org.osmdroid.views.overlay.ItemizedOverlay;
import org.osmdroid.views.overlay.OverlayItem;
import org.osmdroid.DefaultResourceProxyImpl;
import org.osmdroid.ResourceProxy;

public class StopsMapActivity extends MapViewActivity
{
	private String[] stopsNames;
    private double[] latitudes;
    private double[] longitudes;

    private ItemizedOverlay<OverlayItem> mMyLocationOverlay;
    private ResourceProxy mResourceProxy;

    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);

        this.mResourceProxy = new DefaultResourceProxyImpl(getApplicationContext());
        ArrayList<OverlayItem> items = new ArrayList<OverlayItem>();

        Bundle extras = getIntent().getExtras();
        if (extras != null) {
            this.stopsNames = extras.getStringArray("stopsNames");
            this.latitudes = extras.getDoubleArray("latitudes");
            this.longitudes = extras.getDoubleArray("longitudes");
        }

        if (this.stopsNames != null && this.latitudes != null && this.longitudes != null) {
            if (this.stopsNames.length == this.latitudes.length && this.latitudes.length == this.longitudes.length && this.longitudes.length > 0) {
                Log.e("BusTours:StopsMaps", "Got some points ...");
                int i;
                for (i = 0; i < this.stopsNames.length; i++) {
                    Log.e("BusTours:StopsMaps", "Stops @ (" + String.valueOf(this.latitudes[i]) + ", " + String.valueOf(this.longitudes[i]) + ") == " + this.stopsNames[i]);
                    items.add(new OverlayItem(this.stopsNames[i], this.stopsNames[i], new GeoPoint((int)(this.latitudes[i]*1e6), (int)(this.longitudes[i]*1e6))));
                }
            }
        }

        /* OnTapListener for the Markers, shows a simple Toast. */
        this.mMyLocationOverlay = new ItemizedIconOverlay<OverlayItem>(items,
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

        this.getOsmMap().getOverlays().add(this.mMyLocationOverlay);
    }
}

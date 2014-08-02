/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import android.app.Activity;
import android.app.Dialog;

import android.content.Context;
import android.content.Intent;

import android.util.Log;

import android.os.Bundle;

import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapController;
import org.osmdroid.views.MapView;
import org.slf4j.LoggerFactory;

public class MapViewActivity extends Activity
{
    private MapView osmMap;
    private GeoPoint geoPointTours;

    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.mapview);

        this.geoPointTours = new GeoPoint((int)(47.3883*1e6), (int)(0.7276*1e6));

        osmMap = (MapView)findViewById(R.id.map);
        osmMap.setTileSource(TileSourceFactory.MAPQUESTOSM);
        osmMap.setBuiltInZoomControls(true);
        osmMap.setMultiTouchControls(true);
        osmMap.getController().setZoom(13);
        osmMap.getController().setCenter(this.geoPointTours);
    }

    public MapView getOsmMap() {
        return this.osmMap;
    }
}

/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;

import android.content.Context;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import android.widget.ArrayAdapter;
import android.widget.CheckBox;
import android.widget.TextView;
import android.widget.ImageView;
import android.widget.Toast;

import android.util.Log;

public class BusLineIdAdapter extends ArrayAdapter<BusLineId> {
    private ArrayList<BusLineId> linesList;
    private Context context;

    public BusLineIdAdapter(Context context, int textViewResourceId, List<BusLineId> linesList) {
        super(context, textViewResourceId, linesList);
        this.context = context;
        this.linesList = new ArrayList<BusLineId>();
        this.linesList.addAll(linesList);
    }

    private class ViewHolder {
        TextView code;
        ImageView color;
        CheckBox name;
    }

    public View getView(int position, View convertView, ViewGroup parent) {
        ViewHolder holder = null;

        if (convertView == null) {
            LayoutInflater vi = (LayoutInflater)this.context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            convertView = vi.inflate(R.layout.lines_infos, null);
               
            holder = new ViewHolder();
            holder.name = (CheckBox) convertView.findViewById(R.id.checkBox1);
            holder.color = (ImageView) convertView.findViewById(R.id.lineColor);
            convertView.setTag(holder);
           
            holder.name.setOnClickListener( new View.OnClickListener() { 
                public void onClick(View v) { 
                    CheckBox cb = (CheckBox) v ; 
                    BusLineId lineId = (BusLineId) cb.getTag(); 
                    lineId.setSelected(cb.isChecked());
                    Log.e("BusTours:BusLineIdAdapter", "Selected: " + lineId.getCode());
                }
            }); 
        } else {
            holder = (ViewHolder) convertView.getTag();
        }

        BusLineId lineId = linesList.get(position);
        holder.name.setText(lineId.getName());
        holder.name.setChecked(lineId.isSelected());
        holder.name.setTag(lineId);
        holder.color.setBackgroundColor(lineId.getColor());

        return convertView;
    }

    public ArrayList<BusLineId> getSelected() {
        ArrayList<BusLineId> lines = new ArrayList<BusLineId>();

        Iterator it = linesList.iterator();
        while(it.hasNext()) {
            BusLineId l = (BusLineId)it.next();
            if (l.isSelected()) {
                Log.e("BusTours:BusLineIdAdapter", "Found a selected line: " + l);
                lines.add(l);
            }
        }

        return lines;
    }
}

/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

public class BusLineId {
    String code = null;
    String name = null;
    int color;
    boolean selected = false;
     
    public BusLineId(String code, String name, boolean selected, int color)
    {
        super();
        this.code = code;
        this.name = name;
        this.selected = selected;
        this.color = color;
    }
     
    public String getCode()
    {
        return this.code;
    }

    public void setCode(String code)
    {
        this.code = code;
    }

    public String getName()
    {
        return this.name;
    }

    public void setName(String name)
    {
        this.name = name;
    }
    
    public boolean isSelected()
    {
        return this.selected;
    }

    public void setSelected(boolean selected)
    {
        this.selected = selected;
    }

    public int getColor()
    {
        return this.color;
    }
    
    public void setColor(int color)
    {
        this.color = color;
    }
}

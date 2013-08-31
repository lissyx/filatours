/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.Iterator;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

import android.util.Log;

public class JourneyDetails {

    private List<JourneyPart> parts;

    public class Indication {
        private String type;
        private String line;
        private String direction;
        private String stop;

        public Indication(Element html, String typeAsked) {
            this.type = new String("");
            this.line = new String("");
            this.direction = new String("");
            this.stop = new String("");

            Matcher take = Pattern.compile("Prendre").matcher(html.text());
            Matcher walk = Pattern.compile("Rejoindre").matcher(html.text());
            Elements ps = html.getElementsByTag("p");

            if (take.find()) {
                this.type = typeAsked;

                Matcher line =
                    Pattern.compile("Ligne (.*) > (.*)")
                    .matcher(ps.get(2).text());
                if (line.find()) {
                    this.line = line.group(1);
                    this.direction = line.group(2);
                }

                Matcher stop = null;
                Log.e("BusTours:JourneyDetails", "mount/unmount: " + ps.text());

                if (typeAsked.equals("mount")) {
                    Log.e("BusTours:JourneyDetails", "mount: " + ps.get(0).text());
                    stop = Pattern.compile("De : (.*), .*").matcher(ps.get(0).text());
                }

                if (typeAsked.equals("umount")) {
                    Log.e("BusTours:JourneyDetails", "umount: " + ps.get(1).text());
                    stop = Pattern.compile(".* : (.*), .*").matcher(ps.get(1).text());
                }

                if (stop != null && stop.find()) {
                    this.stop = stop.group(1);
                }
            }

            if (walk.find()) {
                this.type = "walk";

                Matcher direction =
                    Pattern.compile("Rejoindre .*: (.*), .*")
                    .matcher(ps.get(1).text());
                if (direction.find()) {
                    this.direction = direction.group(1);
                }

                Matcher stop =
                    Pattern.compile("De : (.*), .*")
                    .matcher(ps.get(0).text());
                if (stop.find()) {
                    this.stop = stop.group(1);
                }
            }
        }

        public String getType() {
            return this.type;
        }

        public String getLine() {
            return this.line;
        }

        public String getDirection() {
            return this.direction;
        }

        public String getStop() {
            return this.stop;
        }

        public String toString() {
            return "{'type': " + this.getType() + " 'line': " + this.getLine() + " 'direction': " + this.getDirection() + " 'stop': " + this.getStop() + "}";
        }
    }

    public class JourneyPart {
        private String type;
        private String mode;
        private Indication indic;
        private String time;
        private String duration;

        public JourneyPart(String type, String mode, Indication indic, String time, String duration) {
            this.type       = type;
            this.mode       = mode;
            this.indic      = indic;
            this.time       = time;
            this.duration   = duration;
        }

        public String getType() {
            return this.type;
        }

        public String getMode() {
            return this.mode;
        }

        public Indication getIndic() {
            return this.indic;
        }

        public String getTime() {
            return this.time;
        }

        public String getDuration() {
            return this.duration;
        }

        public String toString() {
            String ind;
            if (this.getIndic() == null) {
                ind = "N/A";
            } else {
                ind = this.getIndic().toString();
            }

            return "{'type': " + this.getType() + " 'mode': " + this.getMode() + " 'time': " + this.getTime() + " 'duration': " + this.getDuration() + " 'indic': " + ind;
        }
    }

    public JourneyDetails(Elements details) {
        this.parts = new ArrayList<JourneyPart>();

        Iterator<Element> it = details.iterator();
        while (it.hasNext()) {
            Element el = it.next();
            String eClass = el.attr("class");
            // Log.e("BusTours:JourneyDetails", "eClass==" + eClass);

            if(eClass.equals("jvmalinDetail_item")) {
                String type = new String("indication");
                String mode = el.select("div[class=jvmalinDetail_item_left]").text();
                String time = this.parseTime(
                    el.select("div[class=jvmalinDetail_item_middle] p")
                    .first()
                );
                String duration = this.parseDuration(
                    el.select("div[class=jvmalinDetail_item_right")
                    .last()
                );
                Element indicsStr = el.select("div[class=jvmalinDetail_item_right").first();
                Indication indic = new Indication(indicsStr, "mount");

                // Log.e("BusTours:JourneyDetails", "indic:" + indic.toString());

                this.parts.add(
                    new JourneyPart(
                        type,
                        mode,
                        indic,
                        time,
                        duration)
                );

                if (indic.type.equals("mount")) {
                    Indication indicUmount = new Indication(indicsStr, "umount");
                    duration = this.parseDuration(
                        el.select("div[class=jvmalinDetail_item_right] p")
                        .last()
                    );
                    time = this.parseTime(
                        el.select("div[class=jvmalinDetail_item_middle] p")
                        .last()
                    );
                    // Log.e("BusTours:JourneyDetails", "indicUmount:" + indicUmount.toString());

                    this.parts.add(
                        new JourneyPart(
                            type,
                            mode,
                            indicUmount,
                            time,
                            duration)
                    );
                }
            }

            if(eClass.equals("correspondance")) {
                this.parts.add(new JourneyPart("connection", "", null, "", this.parseDuration(el)));
            }
        }
    }

    public List<JourneyPart> getParts() {
        return this.parts;
    }

    public String toString() {
        String res = new String("");
        Iterator<JourneyPart> it = this.parts.iterator();
        while (it.hasNext()) {
            res += it.next().toString();
        }
        return res;
    }

    private String parseTime(Element e) {
        Pattern reTimeArrival = Pattern.compile("(\\d+)h(\\d+)");
        // Log.e("BusTours:JourneyDetails", "time==" + e.html());
        Matcher time = reTimeArrival.matcher(e.text());

        if (!time.find()) {
            Log.e("BusTours:JourneyDetails", "No time match :(");
        }

        return new String(time.group(1) + "h" + time.group(2));
    }

    private String parseDuration(Element e) {
        String duration = new String("");
        Pattern reDuration = Pattern.compile("Durée : (\\d+)\\s*h|(\\d+)\\s*min|(\\d+)\\s*s");
        Log.e("BusTours:JourneyDetails", "duration==" + e.html());
        Matcher m = reDuration.matcher(e.text());

        if (!m.find()) {
            Log.e("BusTours:JourneyDetails", "No duration match :(");
            return new String("< 1 min");
        }

        if (m.group(1) != null) {
            duration += m.group(1) + "h";
        }

        if (m.group(2) != null) {
            duration += m.group(2) + "min";
        }

        if (m.group(3) != null) {
            duration += m.group(3) + "s";
        }

        return duration;
    }
}

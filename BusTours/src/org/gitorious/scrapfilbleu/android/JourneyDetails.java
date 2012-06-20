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

        public Indication(Element html) {
            this.type = new String("");
            this.line = new String("");
            this.direction = new String("");
            this.stop = new String("");

            Matcher take = Pattern.compile("^Prendre").matcher(html.text());
            Matcher out = Pattern.compile("^Descendre").matcher(html.text());
            Elements bs = html.getElementsByTag("b");

            if (take.find()) {
                this.type = "mount";
                this.line = bs.get(0).text();
                this.direction = bs.get(1).text();
                this.stop = bs.get(2).text();
            }

            if (out.find()) {
                this.type = "umount";
                this.stop = bs.get(0).text();
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
        // bypass first element, table heading
        it.next();
        while (it.hasNext()) {
            String type = new String("");
            String mode = new String("");
            Indication indic = null;
            String time = new String("");
            String duration = new String("");

            Elements todo = it.next().getElementsByTag("td");
            int nbElems = todo.size();
            String elemClass;

            switch(nbElems) {
                case 3: // connection
                    elemClass = todo.get(0).attr("class");

                    if (elemClass.equals("indication")) {
                        type = "indication";
                        indic = new Indication(todo.get(0));
                        time = todo.get(1).html();
                    }

                    if (elemClass.equals("correspondance")) {
                        type = "connecion";
                        duration = todo.get(1).html();
                    }

                    break;
                case 5: // journey part
                    elemClass = todo.get(1).attr("class");

                    mode = todo.first().getElementsByTag("img").first().attr("alt");
                    if (elemClass.equals("indication")) {
                        type = "indication";
                        indic = new Indication(todo.get(1));
                        time = todo.get(2).html();
                        duration = todo.get(3).html();
                    }

                    break;
                default:
                    Log.e("BusTours:JourneyDetails", "Unexpected nbElems: " + String.valueOf(nbElems));
                    break;
            }

            this.parts.add(new JourneyPart(type, mode, indic, time, duration));
        }
    }

    public String toString() {
        String res = new String("");
        Iterator<JourneyPart> it = this.parts.iterator();
        while (it.hasNext()) {
            res += it.next().toString();
        }
        return res;
    }
}

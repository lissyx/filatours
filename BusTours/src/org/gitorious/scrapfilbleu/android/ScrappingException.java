/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

public class ScrappingException extends Exception {
    private String err;
    
    public ScrappingException() {
        super();
        this.err = "Unknown";
    }

    public ScrappingException(String e) {
        super(e);
        this.err = e;
    }

    public String getError() {
        return this.err;
    }
}

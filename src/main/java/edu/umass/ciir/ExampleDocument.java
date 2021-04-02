package edu.umass.ciir;

public class ExampleDocument {
    private String docid;
    private String docText;
    private String highlight;

    ExampleDocument(String docid, String docText, String highlight) {
        this.highlight = highlight;
        this.docid = docid;
        this.docText = docText;
    }

    ExampleDocument(ExampleDocument other) {
        this.docid = other.docid;
        this.docText = other.docText;
        this.highlight = other.highlight;
    }

    public String getDocid() {
        return docid;
    }

    public String getDocText() {
        return docText;
    }

    public String getHighlight() {
        return highlight;
    }

    public void setHighlight(String highlight) {
        this.highlight = highlight;
    }

    public void setDocText(String docText) {
        this.docText = docText;
    }

}


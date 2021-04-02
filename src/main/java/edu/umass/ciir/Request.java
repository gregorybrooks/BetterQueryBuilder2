package edu.umass.ciir;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.util.*;
import java.util.logging.Logger;

/**
 * Represents a specific analytic request within the larger analytic task (@see ConvertDryRunTasks.Task).
 */
public class Request {
    private static final Logger logger = Logger.getLogger("TaskQueryBuilder1");
    String reqNum;
    String reqText;
    List<ExampleDocument> reqExampleDocs;

    public boolean isInExampleDocs(String docid) {
        for (ExampleDocument d : reqExampleDocs) {
            if (docid.equals(d.getDocText())) {
                return true;
            }
        }
        return false;
    }

    Request(String reqNum, String reqText, List<ExampleDocument> exampleDocuments) {
        this.reqNum = reqNum;
        this.reqText = reqText;
        this.reqExampleDocs = new ArrayList<>(exampleDocuments);
    }

    /**
     * Copy constructor (deep copy)
     * @param otherRequest The Request to make a copy of.
     */
    Request(Request otherRequest) {
        this.reqNum = otherRequest.reqNum;
        this.reqText = otherRequest.reqText;
        this.reqExampleDocs = new ArrayList<ExampleDocument>(otherRequest.reqExampleDocs);
    }

    public List<String> getReqExtrList() {
        List<String> extractions = new ArrayList<>();
        for (ExampleDocument d : reqExampleDocs) {
            extractions.add(d.getHighlight());
        }
        return extractions;
    }

    public List<String> getExampleDocids() {
        List<String> docids = new ArrayList<>();
        for (ExampleDocument d : reqExampleDocs) {
            docids.add(d.getDocid());
        }
        return docids;
    }
}

package edu.umass.ciir;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import java.util.*;
import java.util.logging.Logger;

public class Task {
    private static final Logger logger = Logger.getLogger("BetterQueryBuilder2");
    String taskNum;
    String taskTitle;
    String taskStmt;
    String taskNarr;
    List<Request> requests;
    public List<ExampleDocument> taskExampleDocs;

    Task(String taskNum, String taskTitle, String taskStmt, String taskNarr, List<ExampleDocument> exampleDocuments,
         List<Request> requests) {
        this.taskNum = taskNum;
        this.taskTitle = taskTitle;
        this.taskNarr = taskNarr;
        this.taskExampleDocs = exampleDocuments;
        this.requests = requests;
    }

    public List<String> getExampleDocids() {
        List<String> docids = new ArrayList<>();
        for (ExampleDocument d : taskExampleDocs) {
            docids.add(d.getDocid());
        }
        return docids;
    }

   /**
     * Copy constructor (deep copy)
     * @param otherTask The Task to make a copy of.
     */
    Task(Task otherTask) {
        this.taskNum = new String(otherTask.taskNum);
        this.taskTitle = (otherTask.taskTitle == null ? null : new String(otherTask.taskTitle));
        this.taskStmt = (otherTask.taskStmt == null ? null : new String(otherTask.taskStmt));;
        this.taskNarr = (otherTask.taskNarr == null ? null : new String(otherTask.taskNarr));
        this.requests = new ArrayList<>();
        for(Request r : otherTask.requests) {
            this.requests.add(r);
        }
        this.taskExampleDocs = new ArrayList<>(otherTask.taskExampleDocs);
    }


    public List<Request> getRequests() { return requests; }

}



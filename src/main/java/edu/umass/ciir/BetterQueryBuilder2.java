package edu.umass.ciir;

import com.cedarsoftware.util.io.JsonWriter;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.*;

public class BetterQueryBuilder2 {
    private static final Logger logger = Logger.getLogger("BetterQueryBuilder2");
    private Map<String, String> queries = new ConcurrentHashMap<>();
    private Map<String, String> nonTranslatedQueries = new ConcurrentHashMap<>();
    private String analyticTasksFile;
    private String mode;
    private String programDirectory;
    private boolean targetLanguageIsEnglish;
    private String outputQueryFileName;
    private Spacy spacy;
    private String phase;
    private TranslatorInterface translator;

    public void setTranslator(TranslatorInterface translator) {
        this.translator = translator;
    }

    public void setQuery(String key, String query) {
        queries.put(key, query);
    }

    public void setNonTranslatedQuery(String key, String query) {
        nonTranslatedQueries.put(key, query);
    }

    /**
     * Configures the logger for this program.
     * @param logFileName Name to give the log file.
     */
    private void configureLogger(String logFileName) {
        SimpleFormatter formatterTxt;
        FileHandler fileTxt;
        try {
            // suppress the logging output to the console
            Logger rootLogger = Logger.getLogger("");
            Handler[] handlers = rootLogger.getHandlers();
            if (handlers[0] instanceof ConsoleHandler) {
                rootLogger.removeHandler(handlers[0]);
            }
            logger.setLevel(Level.INFO);
            fileTxt = new FileHandler(logFileName);
            // create a TXT formatter
            formatterTxt = new SimpleFormatter();
            fileTxt.setFormatter(formatterTxt);
            logger.addHandler(fileTxt);
        } catch (Exception cause) {
            throw new BetterQueryBuilderException(cause);
        }
    }

    /**
     * Sets up logging for this program.
     */
    public void setupLogging() {
        String logFileName = "./task-query-builder1.log";
        configureLogger(logFileName);
    }

    protected void writeQueryFile() {
        // Output the query list as a JSON file,
        // in the format Galago's batch-search expects as input
        logger.info("Writing query file " + outputQueryFileName);

        try {
            JSONArray qlist = new JSONArray();
            for (Map.Entry<String, String> entry : queries.entrySet()) {
                JSONObject qentry = new JSONObject();
                qentry.put("number", entry.getKey());
                String query = entry.getValue();
                /* WRONG: it's a REGEX so this just removes all "#sdm"
                query = query.replaceAll("#sdm()", " ");
                */
                query = query.replaceAll("#sdm\\(\\)", " ");   // empty #sdm causes Galago errors
                qentry.put("text", query);
                qlist.add(qentry);
            }
            JSONObject outputQueries = new JSONObject();
            outputQueries.put("queries", qlist);
            PrintWriter writer = new PrintWriter(new OutputStreamWriter(
                    new FileOutputStream(outputQueryFileName)));
            writer.write(outputQueries.toJSONString());
            writer.close();

            String niceFormattedJson = JsonWriter.formatJson(outputQueries.toJSONString());
            writer = new PrintWriter(new OutputStreamWriter(
                    new FileOutputStream(outputQueryFileName + ".PRETTY.json")));
            writer.write(niceFormattedJson);
            writer.close();

            qlist = new JSONArray();
            for (Map.Entry<String, String> entry : nonTranslatedQueries.entrySet()) {
                JSONObject qentry = new JSONObject();
                qentry.put("number", entry.getKey());
                qentry.put("text", entry.getValue());
                qlist.add(qentry);
            }
            outputQueries = new JSONObject();
            outputQueries.put("queries", qlist);
            writer = new PrintWriter(new OutputStreamWriter(
                    new FileOutputStream(outputQueryFileName + ".NON_TRANSLATED.json")));
            writer.write(outputQueries.toJSONString());
            writer.close();

            niceFormattedJson = JsonWriter.formatJson(outputQueries.toJSONString());
            writer = new PrintWriter(new OutputStreamWriter(
                    new FileOutputStream(outputQueryFileName + ".NON_TRANSLATED.PRETTY.json")));
            writer.write(niceFormattedJson);
            writer.close();

        } catch (Exception e) {
            throw new BetterQueryBuilderException(e);
        }
    }

    public static String filterCertainCharactersPostTranslation(String q) {
        if (q == null || q.length() == 0) {
            return q;
        }
        else {
            q = q.replaceAll("\\.", " ");  // with the periods the queries hang
            q = q.replaceAll("@", " ");  // Galago has @ multi-word token thing
            q = q.replaceAll("\"", " "); // remove potential of mis-matched quotes
            q = q.replaceAll("“", " ");  // causes Galago to silently run an empty query
            q = q.replaceAll("”", " ");
            return q;
        }
    }
    public static String filterCertainCharacters(String q) {
        if (q == null || q.length() == 0) {
            return q;
        }
        else {
            q = q.replaceAll("\\.", " ");  // with the periods the queries hang
            q = q.replaceAll("\\(", " ");  // parentheses are included in the token
            q = q.replaceAll("\\)", " ");  // which causes that term to not be matched
            q = q.replaceAll("@", " ");  // Galago has @ multi-word token thing
            q = q.replaceAll("#", " ");  // Galago thinks #926 is an illegal node type
            q = q.replaceAll("\"", " "); // remove potential of mis-matched quotes
            q = q.replaceAll("“", " ");  // causes Galago to silently run an empty query
            q = q.replaceAll("”", " ");
            return q;
        }
    }

    List<Task> tasks = new ArrayList<>();

    private String getOptionalValue(JSONObject t, String field) {
        if (t.containsKey(field)) {
            return (String) t.get(field);
        } else {
            return "";
        }
    }

    private void readTaskFile() {
        try {
            logger.info("Reading analytic tasks info file " + analyticTasksFile);

            Reader reader = new BufferedReader(new InputStreamReader(
                    new FileInputStream(analyticTasksFile)));
            JSONParser parser = new JSONParser();
            JSONArray tasksJSON = (JSONArray) parser.parse(reader);
            for (Object oTask : tasksJSON) {
                JSONObject t = (JSONObject) oTask;
                String taskNum = (String) t.get("task-num");
                String taskTitle = getOptionalValue(t, "task-title");
                String taskStmt = getOptionalValue(t, "task-stmt");
                String taskNarr = getOptionalValue(t, "task-narr");
                JSONObject taskDocMap = (JSONObject) t.get("task-docs");
                List<ExampleDocument> taskExampleDocuments = new ArrayList<>();
                for (Iterator iterator = taskDocMap.keySet().iterator(); iterator.hasNext(); ) {
                    String entryKey = (String) iterator.next();
                    JSONObject taskDoc = (JSONObject) taskDocMap.get(entryKey);
                    String highlight = getOptionalValue(taskDoc, "highlight");
                    String docText = (String) taskDoc.get("doc-text");
                    String docID = (String) taskDoc.get("doc-id");
                    taskExampleDocuments.add(new ExampleDocument(docID, docText, highlight));
                }
                JSONArray taskRequests = (JSONArray) t.get("requests");
                List<Request> requests = new ArrayList<>();
                for (Object o : taskRequests) {
                    JSONObject request = (JSONObject) o;
                    String reqText = getOptionalValue(request, "req-text");
                    String reqNum = (String) request.get("req-num");
                    JSONObject requestDocMap = (JSONObject) request.get("req-docs");
                    List<ExampleDocument> requestExampleDocuments = new ArrayList<>();
                    for (Iterator iterator = requestDocMap.keySet().iterator(); iterator.hasNext(); ) {
                        String entryKey = (String) iterator.next();
                        JSONObject reqDoc = (JSONObject) requestDocMap.get(entryKey);
                        String highlight = getOptionalValue(reqDoc, "highlight");
                        String docText = (String) reqDoc.get("doc-text");
                        String docID = (String) reqDoc.get("doc-id");
                        requestExampleDocuments.add(new ExampleDocument(docID, docText, highlight));
                    }
                    requests.add(new Request(reqNum, reqText, requestExampleDocuments));
                }
                tasks.add(new Task(taskNum, taskTitle, taskStmt, taskNarr, taskExampleDocuments, requests));
            }
        } catch (Exception e) {
            throw new BetterQueryBuilderException(e);
        }
    }

    protected void buildQueries() {
        logger.info("Building task-level queries");
        for (Task t : tasks) {
            buildDocsString(t);
        }
    }

    protected void buildDocsString(Task t) {
        logger.info("Building query for task " + t.taskNum);

        Map<String, Integer> soFar = new HashMap<>();
        Set<String> uniqueDocIds = new HashSet<>();
        List<String> uniqueDocTexts = new ArrayList<>();
        /*
         * Extract unique noun phrases from the example documents,
         * with document use counts (how many docs use each phrase)
         */
        for (ExampleDocument d : t.taskExampleDocs) {
            if (!uniqueDocIds.contains(d.getDocid())) {
                uniqueDocIds.add(d.getDocid());
                addNounPhrases(soFar, d.getDocText());
            }
        }
        for (Request r : t.getRequests()) {
            for (ExampleDocument d : r.reqExampleDocs) {
                if (!uniqueDocIds.contains(d.getDocid())) {
                    uniqueDocIds.add(d.getDocid());
                    addNounPhrases(soFar, d.getDocText());
                }
            }
        }
        /*
         * Also extract unique noun phrases from any "highlights"
         * provided for the requests for this task
         */
        for (Request r : t.getRequests()) {
            for (String extr : r.getReqExtrList()) {
                addNounPhrases(soFar, extr);
            }
        }

        /* Sort the unique noun phrases by document use count, descending */
        LinkedHashMap<String, Integer> reverseSortedMap = new LinkedHashMap<>();
        soFar.entrySet()
                .stream()
                .sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
                .forEachOrdered(x -> reverseSortedMap.put(x.getKey(), x.getValue()));

        /*
         * Make a final list of those unique noun phrases used in more
         * than one example doc. (Include them all if there is only one example doc.)
         */
        List<String> finalList = new ArrayList<>();
        for (Map.Entry<String, Integer> entry : reverseSortedMap.entrySet()) {
            if ((uniqueDocIds.size() == 1) || (entry.getValue() > 1)) {
                finalList.add(filterCertainCharacters(entry.getKey()));
            }
        }
        boolean useTaskParts = (mode.equals("AUTO-HITL") || mode.equals("HITL"));

        /*
         * Translate finalList, then put all those phrases into a string wrapped
         * in a #combine operator.
         * We also construct a non-translated version of the query for debugging purposes.
         */
        List<String> nonTranslatedFinalList = new ArrayList<>();
        /* First the non-translated version: */
        for (String phrase : finalList) {
            if (!phrase.contains(" ")) {
                nonTranslatedFinalList.add(phrase);
            } else {
                /* For multi-word phrases, we wrap the phrase in a sequential dependence operator */
                nonTranslatedFinalList.add("#sdm(" + phrase + ") ");
            }
        }
        /*
         * Next the translated version (translation includes adding #sdm
         * operators where appropriate
         */
        List<String> translatedFinalList;
        if (!targetLanguageIsEnglish) {
            translatedFinalList = translator.getTranslations(finalList);
        } else {
            translatedFinalList = nonTranslatedFinalList;
        }

        /*
         * Convert the final translated and non-translated lists of noun phrases
         * into strings wrapped in #combine operators
         */
        StringBuilder nonTranslatedNounPhrasesStringBuilder = new StringBuilder();
        for (String phrase : nonTranslatedFinalList) {
            nonTranslatedNounPhrasesStringBuilder.append(phrase).append(" ");
        }
        String nonTranslatedNounPhrasesString = nonTranslatedNounPhrasesStringBuilder.toString();
        nonTranslatedNounPhrasesString = "#combine(" + nonTranslatedNounPhrasesString + ") ";

        String nounPhrasesString;
        if (!targetLanguageIsEnglish) {
            StringBuilder nounPhrasesStringBuilder = new StringBuilder();
            for (String phrase : translatedFinalList) {
                nounPhrasesStringBuilder.append(filterCertainCharactersPostTranslation(phrase)).append(" ");
            }
            nounPhrasesString = nounPhrasesStringBuilder.toString();
            nounPhrasesString = "#combine(" + nounPhrasesString + ") ";
        } else {
            nounPhrasesString = nonTranslatedNounPhrasesString;
        }

        /*
         * At this point, nounPhasesString has the most important noun phrases from
         * the task's and its requests' example docs and its requests' highlights
         */

        /* Add query elements from the Task definition, which is allowed in HITL mode */
        List<String> taskParts = new ArrayList<>();
        boolean hasTaskParts = true;
        if (t.taskTitle == null && t.taskStmt == null && t.taskNarr == null) {
            hasTaskParts = false;
        } else {
            if (t.taskTitle != null) {
                taskParts.add(filterCertainCharacters(t.taskTitle));
            }
            if (t.taskStmt != null) {
                taskParts.add(filterCertainCharacters(t.taskStmt));
            }
            if (t.taskNarr != null) {
                taskParts.add(filterCertainCharacters(t.taskNarr));
            }
        }

        /* Translate taskParts (but we also keep a non-translated version for debugging purposes) */
        /*
         * Convert the translated and non-translated lists of task elements
         * into strings wrapped in #combine operators. No #sdm's are used on these
         * strings of words, which are sometimes long
         */
        String taskPartsString = "";
        String nonTranslatedTaskPartsString = "";
        if (hasTaskParts) {
            StringBuilder nonTranslatedTaskPartsStringBuilder = new StringBuilder();
            for (String phrase : taskParts) {
                nonTranslatedTaskPartsStringBuilder.append(phrase).append(" ");
            }
            nonTranslatedTaskPartsString = nonTranslatedTaskPartsStringBuilder.toString();
            nonTranslatedTaskPartsString = "#combine(" + nonTranslatedTaskPartsString + ") ";
            List<String> translatedTaskParts;
            if (!targetLanguageIsEnglish) {
                translatedTaskParts = translator.getTranslations(taskParts);
                StringBuilder taskPartsStringBuilder = new StringBuilder();
                for (String phrase : translatedTaskParts) {
                    taskPartsStringBuilder.append(filterCertainCharactersPostTranslation(phrase)).append(" ");
                }
                taskPartsString = taskPartsStringBuilder.toString();
                taskPartsString = "#combine(" + taskPartsString + ") ";
            } else {
                taskPartsString = nonTranslatedTaskPartsString;
            }
        }

        /*
         * Construct the final Galago queries, translated and non-translated versions,
         * from the noun phrases and task elements. Use the #combine's weights to heavily
         * emphasize the task elements (title, narrative and statement)
         */
        String finalString;
        String nonTranslatedFinalString;

        if (useTaskParts && hasTaskParts) {
            finalString = "#combine:0=0.2:1=0.8 (" + nounPhrasesString + " "
                    + taskPartsString + ")";
            nonTranslatedFinalString = "#combine:0=0.2:1=0.8 (" + nonTranslatedNounPhrasesString + " "
                    + nonTranslatedTaskPartsString + ")";
        } else {
            finalString = "#combine (" + nounPhrasesString + ")";
            nonTranslatedFinalString = "#combine (" + nonTranslatedNounPhrasesString + ")";
        }

        setQuery(t.taskNum, finalString);
        setNonTranslatedQuery(t.taskNum, nonTranslatedFinalString);
    }

    private void addNounPhrases(Map<String, Integer> soFar, String extr) {
        List<String> nouns = spacy.getNounPhrases(extr);
        for (String noun_phrase : nouns) {
            if (noun_phrase.length() > 2) {  // omit small single words
                if (!soFar.containsKey(noun_phrase)) {
                    soFar.put(noun_phrase, 1);
                } else {
                    int x = soFar.get(noun_phrase);
                    soFar.put(noun_phrase, x + 1);
                }
            }
        }
    }

    /**
     * Processes the analytic tasks file: generates queries for the Tasks and Requests,
     * executes the queries, annotates hits with events.
     */
    private void processTaskQueries(String analyticTasksFile, String mode, String outputQueryFileName,
                         boolean targetLanguageIsEnglish, String programDirectory, String phase) {
        logger.info("Starting task-level query construction");
        this.programDirectory = programDirectory;
        this.spacy = new Spacy(programDirectory);
        this.mode = mode;
        this.analyticTasksFile = analyticTasksFile;
        this.targetLanguageIsEnglish = targetLanguageIsEnglish;
        this.outputQueryFileName = outputQueryFileName;
        readTaskFile();
        buildQueries();
        writeQueryFile();
    }

    private static String ensureTrailingSlash(String s) {
        if (!s.endsWith("/")) {
            return s + "/";
        } else {
            return s;
        }
    }

    /**
     * Public entry point for this class.
     * ARGS:
     *  analytic tasks info file, full path name
     *  mode - AUTO, AUTO-HITL, or HITL
     *  output file full path name (will become a Galago-ready query file)
     *  target corpus language - "en" (English) or "ar" (Arabic)
     *  program directory - full path of the directory where programs needed by this program will be
     *    should end with a "/"
     *  phase - only "Task" is supported in this query builder
     */
    public static void main (String[] args) {
        for (int x = 0; x < args.length; ++x) {
            System.out.println(x + ": " + args[x]);
        }
        String analyticTasksFile = args[0];
        String mode = args[1];
        String outputQueryFileName = args[2] + ".queries.json";
        boolean targetLanguageIsEnglish = (args[3].equals("en"));
        String programDirectory = args[4];
        programDirectory = ensureTrailingSlash(programDirectory);
        String phase = args[5];
        BetterQueryBuilder2 betterIR = new BetterQueryBuilder2();
        betterIR.setupLogging();
        betterIR.setTranslator(new RabTranslator(programDirectory));
        //betterIR.setTranslator(new TableTranslator(programDirectory
        //        + "translation_tables/en-fa-3-col-ttable-no-normal.txt"));
        if (phase.equals("Task")) {
            betterIR.processTaskQueries(analyticTasksFile, mode, outputQueryFileName, targetLanguageIsEnglish,
                    programDirectory, phase);
        } else {
            System.out.println("Bad phase: " + phase);
            System.exit(-1);
        }
    }
}

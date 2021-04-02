package edu.umass.ciir;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Logger;

/**
 * Calls a Python program that uses the spacy library (@see <a href="https://spacy.io/">spaCy</a>)
 * to extract noun phrases, verbs and named entities from text.
 */
public class Spacy {
    private static final Logger logger = Logger.getLogger("TaskQueryBuilder1");

    private String program = "get_from_spacy.py";
    public void setProgram(String program) {
        this.program = program;
    }
    private String programDirectory = "./";
    public void setProgramDirectory(String programDirectory) {
        if (!programDirectory.endsWith("/")) {
            programDirectory += "/";
        }
        this.programDirectory = programDirectory;
    }

    private LineOrientedPythonDaemon sentenceDaemon = null;
    private LineOrientedPythonDaemon nounPhraseDaemon = null;

    Spacy(String programDirectory) {
        if (!programDirectory.endsWith("/")) {
            programDirectory += "/";
        }
        this.programDirectory = programDirectory;
        startSpacySentenceDaemon(programDirectory);
        startSpacyNounPhraseDaemon(programDirectory);
    }

    private void startSpacySentenceDaemon(String programDirectory) {
        logger.info("Starting spacy sentence daemon");
        sentenceDaemon = new LineOrientedPythonDaemon(programDirectory,
                "get_sentences_from_spacy_daemon.py");
    }

    private void startSpacyNounPhraseDaemon(String programDirectory) {
        logger.info("Starting spacy noun phrase daemon");
        nounPhraseDaemon = new LineOrientedPythonDaemon(programDirectory,
               "get_noun_phrases_from_spacy_daemon.py");
    }

    /**
     * Calls the spacy sentence daemon with some text, getting back the sentences.
     * It is synchronized because it is called from inside the Document method that uses a
     * ConcurrentHashMap to multi-thread through reading the corpus file, and the Python spacy
     * sentence daemon program is not thread-safe.
     * @param text the text to get sentences from
     * @return the list of sentences
     */
    public List<String> getSentences(String text) {
        return sentenceDaemon.getAnswers(text);
    }

    // No need to do this, let it run until the whole program ends
    public void stopSpacy() {
        sentenceDaemon.stop();
    }

    /**
     * Calls the spacy noun phrase daemon with some text, getting back the phrases.
     * It is synchronized because it is called from inside the Document method that uses a
     * ConcurrentHashMap to multi-thread through reading the corpus file, and the Python spacy
     * noun phrase daemon program is not thread-safe.
     * @param text the text to get phrases from
     * @return the list of noun phrases
     */
    public List<String> getNounPhrases(String text) {
        return nounPhraseDaemon.getAnswers(text);
    }

    private List<String> callSpacy(String query, String operation) {
        setProgram("get_from_spacy.py");
        List<String> l = new ArrayList<>();
        l.add(query);
        return callPythonProgram(l, operation);
    }

    private List<String> callPythonProgram(List<String> strings, String operation) {
        try {
            System.out.println("Calling " + programDirectory + program);
            ProcessBuilder processBuilder = new ProcessBuilder("python3",
                    programDirectory + program, operation);
            Process process = processBuilder.start();

            BufferedWriter called_process_stdin = new BufferedWriter(
                    new OutputStreamWriter(process.getOutputStream()));
            BufferedReader called_process_stdout = new BufferedReader(
                    new InputStreamReader(process.getInputStream()));

//            query = query.replace("\"", "");
            for (String s : strings) {
                called_process_stdin.write(s + "\n");
            }
            called_process_stdin.flush();
            called_process_stdin.close();

            List<String> phrases = new ArrayList<String>();
            String line;
            while ((line = called_process_stdout.readLine()) != null) {
                phrases.add(line);
            }
            int exitVal = process.waitFor();
            if (exitVal != 0) {
                throw new TaskQueryBuilderException("Unexpected ERROR calling "
                        + program + " for operation " + operation);
            }
            return phrases;
        } catch (Exception e) {
            throw new TaskQueryBuilderException(e);
        }
    }

    private List<String> callPythonTranslationProgram(List<String> strings)  {
        try {
            System.out.println("Calling " + programDirectory + program + " " + programDirectory );
            ProcessBuilder processBuilder = new ProcessBuilder("/usr/bin/python3",
                    programDirectory + program, programDirectory);
            processBuilder.directory(new File(programDirectory));

            Process process = processBuilder.start();

            BufferedWriter called_process_stdin = new BufferedWriter(
                    new OutputStreamWriter(process.getOutputStream()));
            BufferedReader called_process_stdout = new BufferedReader(
                    new InputStreamReader(process.getInputStream()));

//            query = query.replace("\"", "");
            for (String s : strings) {
                called_process_stdin.write(s + "\n");
            }
            called_process_stdin.flush();
            called_process_stdin.close();

            List<String> phrases = new ArrayList<String>();
            String line;
            while ((line = called_process_stdout.readLine()) != null) {
                phrases.add(line);
            }
            int exitVal = process.waitFor();
            if (exitVal != 0) {
                throw new TaskQueryBuilderException("Unexpected ERROR calling "
                        + program );
            }
            return phrases;
        } catch (Exception e) {
            throw new TaskQueryBuilderException(e);
        }
    }

    /**
     * Uses spaCy to extract the noun phrases and named entities from the query.
     * @param query The text to extract from.
     * @return The list of unique noun phrases and named entities.
     */
    public List<String> getNounPhrasesAndEntities (String query) {
        return callSpacy(query, "noun_phrases+named_entities");
    }

    /**
     * Uses spaCy to extract the noun phrases, named entities and verbs from the query.
     * @param query The text to extract from.
     * @return The list of unique noun phrases and named entities.
     */
    public List<String> getNounPhrasesVerbsAndEntities (String query) {
        List<String> strings = callSpacy(query, "noun_phrases+verbs+named_entities");

        // Remove some verbs that are not helpful
        List<String> ignoreList = new ArrayList<String>(
                Arrays.asList("identify","describe","find"));
        strings.removeAll(ignoreList);
        return strings;
    }

    /**
     * Uses spaCy to extract verbs from a query.
     * @param query The text to extract from.
     * @return The list of verbs.
     */
    public List<String> getVerbs (String query) {

        List<String> verbs = callSpacy(query, "verbs");

        List<String> ignoreList = new ArrayList<String>(
                Arrays.asList("identify","describe","find"));
        verbs.removeAll(ignoreList);

        return verbs;
    }

    public List<String> getTranslations (List<String> strings) {
        setProgram("translation_package/batch_translate.py");
        return callPythonTranslationProgram(strings);
    }
}

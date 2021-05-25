package edu.umass.ciir;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

/**
 * Calls a Python program that uses the spacy library (@see <a href="https://spacy.io/">spaCy</a>)
 * to extract noun phrases, verbs and named entities from text.
 */
public class Spacy {
    private static final Logger logger = Logger.getLogger("BetterQueryBuilder2");

    private String programDirectory = "./";
    private LineOrientedPythonDaemon sentenceDaemon = null;
    private LineOrientedPythonDaemon nounPhraseDaemon = null;

    Spacy(String programDirectory) {
        if (!programDirectory.endsWith("/")) {
            programDirectory += "/";
        }
        this.programDirectory = programDirectory;
        startSpacyNounPhraseDaemon(programDirectory);
    }

    private void startSpacyNounPhraseDaemon(String programDirectory) {
        logger.info("Starting spacy noun phrase daemon");
        nounPhraseDaemon = new LineOrientedPythonDaemon(programDirectory,
                "get_noun_phrases_from_spacy_daemon.py");
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

}

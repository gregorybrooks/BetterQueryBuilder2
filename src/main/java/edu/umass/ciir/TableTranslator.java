package edu.umass.ciir;

import cz.jirutka.unidecode.Unidecode;

import java.io.*;
import java.util.*;
import java.util.Comparator;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/**
 * A translator that uses a translation table.
 */
public class TableTranslator implements TranslatorInterface {
    private Map<String, List<TranslatedTerm>> translationTable = new HashMap<>();
    private Unidecode unidecode = Unidecode.toAscii();
    private List<String> stopWords = new ArrayList<>();

    public TableTranslator() { }

    /**
     * A translator that uses a translation table.
     * The table is a text file that has lines like this: source_word[TAB]target_word[TAB]probability
     * where probability is a float like 0.000545658.
     * @param translationTableFileName the text file containing the translation table
     */
    public TableTranslator(String translationTableFileName) {
        File f = new File(translationTableFileName);
        if (f.exists()) {

            BufferedReader br = null;

            try {
                br = new BufferedReader(new FileReader(translationTableFileName));
            } catch (FileNotFoundException e) {
                throw new BetterQueryBuilderException("Could not read translation table file "
                        + translationTableFileName);
            }

            String line;
            while(true) {
                try {
                    if (!((line =br.readLine())!=null))
                        break;
                } catch (IOException e) {
                    throw new BetterQueryBuilderException("IO error while reading translation table file "
                            + translationTableFileName);
                }
                String[] tokens = line.split("[\t]");
                String source = tokens[0];
                String target = tokens[1];
                Double prob = Double.valueOf(tokens[2]);
                if (!translationTable.containsKey(source)) {
                    List<TranslatedTerm> lst = new ArrayList<TranslatedTerm>();
                    lst.add(new TranslatedTerm(target,prob));
                    translationTable.put(source, lst);
                } else {
                    List<TranslatedTerm> lst = translationTable.get(source);
                    if (lst.contains(target)) {
                        throw new BetterQueryBuilderException("Duplicate of " + source + " to " + target
                                + " in " + translationTableFileName);
                    } else {
                        lst.add(new TranslatedTerm(target,prob));
                    }
                }
            }
        } else {
            throw new BetterQueryBuilderException("Translation table file "
                    + translationTableFileName + " not found");
        }
    }

    /**
     * Translate a string consisting of space-delimited words.
     * @param text the text to be translated
     * @return the translated text
     */
    @Override
    public String getTranslation(String text) {
        String newText = "";
        String[] words = text.split(" ");
        for (String term : words) {
            if (term.length() > 2 && !stopWords.contains(term)) {
                String decodedTerm = unidecode.decode(term).toLowerCase();
                // our TTable doesn't have most 's words
                decodedTerm = decodedTerm.replace("'s", "");
                // our TTable does not have some words with leading or trailing singlequotes
                decodedTerm = decodedTerm.replace("'", "");
                if (translationTable.containsKey(decodedTerm)) {
                    List<TranslatedTerm> sortedList = translationTable.get(decodedTerm).stream()
                            .filter(Predicate.isEqual("'").or(Predicate.isEqual("\"")).negate())  // ttable has ' as Arabic sometimes!
                            .sorted(new TranslatedTerm.SortByProbDesc())
                            .limit(1).collect(Collectors.toList());
                    for (TranslatedTerm t : sortedList) {
                        newText += (" " + t.term);
                    }
                } else {
                    newText += (" " + decodedTerm);
                }
            }
        }
        return newText;
    }

    @Override
    public List<String> getTranslations(List<String> strings) {
        List<String> outputList = new ArrayList<>();
        for (String x : strings) {
            String t = getTranslation(x);
            outputList.add(t);
        }
        return outputList;
    }
}

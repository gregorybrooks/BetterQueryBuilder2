package edu.umass.ciir;

import java.util.Comparator;

public class TranslatedTerm {
    public String term;
    public Double prob;

    public TranslatedTerm(String term, Double prob) {
        this.term = term;
        this.prob = prob;
    }

    static class SortByProbDesc implements Comparator<TranslatedTerm> {
        public int compare(TranslatedTerm a, TranslatedTerm b) {
            return b.prob.compareTo(a.prob);  // desc by prob
        }
    }
}

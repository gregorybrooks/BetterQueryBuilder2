package edu.umass.ciir;

public class BetterQueryBuilderException extends RuntimeException {
    public BetterQueryBuilderException(String errorMessage) {
        super(errorMessage);
    }
    public BetterQueryBuilderException(Exception cause) {
        super(cause);
    }
}

package edu.umass.ciir;

public class TaskQueryBuilderException extends RuntimeException {
    public TaskQueryBuilderException(String errorMessage) {
        super(errorMessage);
    }
    public TaskQueryBuilderException(Exception cause) {
        super(cause);
    }
}

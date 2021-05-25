package edu.umass.ciir;

import java.util.List;

public interface TranslatorInterface {
    List<String> getTranslations(List<String> strings);
    String getTranslation(String text);
}

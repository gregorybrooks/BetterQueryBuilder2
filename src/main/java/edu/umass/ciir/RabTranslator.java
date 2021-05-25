package edu.umass.ciir;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

/**
 * A translator that uses Rab's translator.
 */
public class RabTranslator implements TranslatorInterface {
    private static final Logger logger = Logger.getLogger("BetterQueryBuilder2");

    private String programDirectory = "./";

    RabTranslator(String programDirectory) {
        if (!programDirectory.endsWith("/")) {
            programDirectory += "/";
        }
        this.programDirectory = programDirectory;
    }

    private List<String> callPythonTranslationProgram(List<String> strings)  {
        try {
            String program = "translation_package/batch_translate.py";
            logger.info("Calling " + programDirectory + program + " " + programDirectory );
            ProcessBuilder processBuilder = new ProcessBuilder("/usr/bin/python3",
                    programDirectory + program, programDirectory);
            processBuilder.directory(new File(programDirectory));

            Process process = processBuilder.start();

            BufferedWriter called_process_stdin = new BufferedWriter(
                    new OutputStreamWriter(process.getOutputStream()));
            BufferedReader called_process_stdout = new BufferedReader(
                    new InputStreamReader(process.getInputStream()));

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
                throw new BetterQueryBuilderException("Unexpected ERROR calling " + program );
            }
            return phrases;
        } catch (Exception e) {
            throw new BetterQueryBuilderException(e);
        }
    }

    @Override
    public List<String> getTranslations (List<String> strings) {
        return callPythonTranslationProgram(strings);
    }

    @Override
    public String getTranslation(String text) {
        List<String> inputList = new ArrayList<>();
        List<String> outputList = new ArrayList<>();
        inputList.add(text);
        outputList = getTranslations(inputList);
        return outputList.get(0);
    }
}

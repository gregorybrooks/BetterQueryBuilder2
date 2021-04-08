package edu.umass.ciir;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class LineOrientedPythonDaemon {
    private  ProcessBuilder sentenceProcessBuilder = null;
    private  Process sentenceProcess = null;
    private  BufferedWriter sentenceCalledProcessStdin = null;
    private  BufferedReader sentenceCalledProcessStdout = null;

    LineOrientedPythonDaemon(String programDirectory, String programName) {
        try {
            System.out.println("Starting " + programDirectory + programName);
            sentenceProcessBuilder = new ProcessBuilder("python3",
                    programDirectory + programName);
            sentenceProcessBuilder.directory(new File(programDirectory));
            sentenceProcess = sentenceProcessBuilder.start();

            sentenceCalledProcessStdin = new BufferedWriter(
                    new OutputStreamWriter(sentenceProcess.getOutputStream()));
            sentenceCalledProcessStdout = new BufferedReader(
                    new InputStreamReader(sentenceProcess.getInputStream()));
        } catch (Exception e) {
            throw new BetterQueryBuilderException(e);
        }
    }

    public  synchronized List<String> getAnswers(String text) {
        List<String> phrases = new ArrayList<String>();
        try {
            sentenceCalledProcessStdin.write(text + "\n");
            sentenceCalledProcessStdin.write("EOD\n");
            sentenceCalledProcessStdin.flush();

            String line;
            while ((line = sentenceCalledProcessStdout.readLine()) != null) {
                if (line.equals("EOL")) {
                    break;
                }
                phrases.add(line);
            }
        } catch (Exception e) {
            throw new BetterQueryBuilderException(e);
        }
        return phrases;
    }

    // No need to do this, let it run until the whole program ends
    public  void stop() {
        try {
            sentenceProcess.destroy();
        } catch (Exception e) {
            throw new BetterQueryBuilderException(e);
        }
    }

}

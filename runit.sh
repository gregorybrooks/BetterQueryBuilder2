set -v
java -jar target/BetterQueryBuilder2-1.0.0.jar $eventExtractorFileLocation/$INPUTFILE $MODE $queryFileLocation/$QUERYFILE $OUT_LANG $HOME/programfiles $PHASE
chmod a+rw $queryFileLocation/${QUERYFILE}*

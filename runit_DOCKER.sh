set -v
java -jar target/TaskQueryBuilder1-1.0.0.jar /taskfiles/$INPUTFILE $MODE /queryfiles/${QUERYFILE} $OUT_LANG $HOME/programfiles $PHASE
chmod a+rw /queryfiles/${QUERYFILE}*

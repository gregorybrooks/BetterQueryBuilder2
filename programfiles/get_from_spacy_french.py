import spacy
import sys

"""Calls spaCy to extract noun_phrases, verbs, or named entities from a string.

Pass one argument, which is any of these operations:
    noun_phrases
    verbs
    named_entities
You can request combinations by concatenating the operations with plus signs (no spaces):
    noun_phrases+named_entites
    noun_phrases+verbs+named_entities
Returns -1 if passed an invalid operation.
Pass the string to extract from via STDIN.
This script returns the extracted phrases in STDOUT.
"""

valid_operations = ['named_entities','verbs','noun_phrases']
operation = ''
if len(sys.argv) > 1:
    operation = sys.argv[1]
else:
    operation = 'noun_phrases'  # default operation
operations = operation.split('+')
for o in operations:
    if o not in valid_operations:
        sys.exit(-1)

# Load English tokenizer, tagger, parser, NER and word vectors
nlp = spacy.load("fr_core_news_lg")

# Get query from stdin:
text = ""
for line in sys.stdin:
    text += line

doc = nlp(text)
nouns = []
verbs = []
entities = []
if 'noun_phrases' in operations:
    nouns = [chunk.text.strip() for chunk in doc.noun_chunks]
if 'verbs' in operations:
    verbs = [token.lemma_.strip() for token in doc if token.pos_ == "VERB"]
if 'named_entities' in operations:
    entities = [entity.text for entity in doc.ents]
for a in set(nouns + verbs + entities):
    print(a)
sys.exit(0)

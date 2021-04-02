#!/usr/bin/env python
import sys
import json

if __name__ == "__main__":
  inputfile = sys.argv[1]
  with open(inputfile) as f:
    data = json.load(f)
    if len(data["extractions"]) > 1:
        print("#combine(", end='')
#    example_doc_texts = data["example_doc_texts"]
#    for doc_text in example_doc_texts:
#        print("#sdm(" + doc_text + ") ")
#    print(")")
    for extr in data["extractions"]:
        print("#sdm(" + extr + ") ", end='')
    if len(data["extractions"]) > 1:
        print(")", end='')
    sys.exit(0)

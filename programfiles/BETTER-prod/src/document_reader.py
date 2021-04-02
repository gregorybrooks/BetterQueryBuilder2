
import sys
from src.sentence_weighting import get_request_doc_event_info
from src.greedy_mover_distance import greedy_mover_distance

import argparse
import os
from os import path 
import json
import argparse
import numpy as np
import re
import math 
import statistics 
import spacy   
from IPython.core.debugger import set_trace
import time

#import stanza
#stanza.download(lang='ar')
#stanza_nlp = stanza.Pipeline(lang='ar', processors='tokenize')


#importing labse and laser
import en_core_web_lg
from sentence_transformers import SentenceTransformer

#labse_model = SentenceTransformer('LaBSE')
labse_model = SentenceTransformer('labse')

#nlp = en_core_web_lg.load()
nlp = spacy.load("en_core_web_lg")

def get_event_sentences_with_weights(doc, etype2score):    
    event_sentences = [] 
    event_sentences_weights = []
    
    for event in doc['isi-events']:
        patients = []
        agents = []
        anchors = []        
        anchors.append(event['anchor']['string'])
        
        for patient in event['patients']:
            patients.append(patient['string'])

        for agent in event['agents']:
            agents.append(agent['string'])    
        
        sentence = agents + anchors + patients         
        
        if len(sentence) > 0:
            event_sentences.append(" ".join(sentence))  
            event_sentences_weights.append(etype2score[event['eventType']])
        
    if len(event_sentences) > 0: 
        doc['esentence'] = event_sentences
        if sum(event_sentences_weights) == 0:
            doc['esweights'] = np.ones(len(event_sentences_weights)) / len(event_sentences_weights)
        else:    
            doc['esweights'] = np.asarray(event_sentences_weights) / sum(event_sentences_weights)
    else:
        dummy = 20 * ["This document does not contain anything"]
        doc['esentence'] = dummy 
        doc['esweights'] = np.ones(len(dummy))/len(dummy)
    
    doc['esembed_labse'] = labse_model.encode(doc['esentence']).tolist()    
    
    
    return doc 
    
def add_labse(doc, sentences):    
    doc['sembed_labse'] = labse_model.encode(sentences).tolist()
    return doc 


def add_sentence_weight(doc, sentences):
    weights = [1.0 * len(sentence) for sentence in sentences]
    sum_weights = sum([1 * len(sentence) for sentence in sentences])
    doc['sweights'] = [(weight/sum_weights) for weight in weights]  
    return doc 

def add_event_sentences(doc, event_doc_freq, nlp):
    event_type_tf, etype2keyword = get_request_doc_event_info(doc, nlp)
    event_type_tf_idf = [(item[0], item[1]/(event_doc_freq[item[0]] * event_doc_freq[item[0]])) if item[0] in event_doc_freq else (item[0], 0) for item in event_type_tf]      
    event_type_tf_idf = sorted(event_type_tf_idf, key = lambda x:x[1], reverse=True)
    etype2score = {}
    for item in event_type_tf_idf:
        etype2score.setdefault(item[0], 0)
        etype2score[item[0]] = item[1]
    return get_event_sentences_with_weights(doc, etype2score)

def add_highlights(doc):
    doc['highlight'] = []
    doc['hembed_labse'] = []
    doc['hweight'] = []
    
    if len(doc['highlight'] ) > 0:
        for highlight in doc['highlight']:
            doc['highlight'].append(highlight)
            doc['hweight'].append(1)
            
        doc['hembed_labse'] = labse_model.encode(doc['highlight']).tolist()
        
    return doc

def enrich_doc(doc, event_doc_freq, nlp, lang='eng', req_doc=False):
    
    # if len(doc['sentences']) == 0:
    #     doc_sentences = [sentence.text for sentence in stanza_nlp(doc['docText']).sentences]
        
    # else:
    doc_sentences = [sentence['text'] for sentence in doc['sentences']]
    
    if len(doc_sentences) == 0:
        doc_sentences = 20 * ['هذه جمل عادية']
        #print(len(doc_sentences))
        print("Document does not contain any sentence")

    doc = add_sentence_weight(doc, doc_sentences)
    doc = add_labse(doc, doc_sentences)
    doc = add_event_sentences(doc, event_doc_freq, nlp)    
    if req_doc == True:
        doc = add_highlights(doc) 
    return doc 

def get_edoc_freq(task_docs): 
    event_doc_freq = {}
    for example_doc in task_docs:
        event_type_tf,_ = get_request_doc_event_info(example_doc, nlp)
        for item in event_type_tf:
            #print(item[0], item[1])
            event_doc_freq.setdefault(item[0], 0)
            event_doc_freq[item[0]]+=1   
    return event_doc_freq


def compute_score(enriched_task_docs, enriched_request_docs, enriched_retrieved_docs, req_num, sembed_model, weight_dict, VERBOSE=False): 
    
    scores = [] 
    
    for baseline_rank, retrieved_doc in enumerate(enriched_retrieved_docs): 
        #compute task_document_scores 
        #print(f"computing scores for retrieved doc {retrieved_doc['docText']}")
        task_doc_scores = []
        task_doc_event_scores = []
        request_doc_scores = [] 
        request_doc_event_scores = []
                
        for task_doc in enriched_task_docs:        
            score_sentence = greedy_mover_distance(task_doc['sembed_' + sembed_model], retrieved_doc['sembed_' + sembed_model], task_doc['sweights'].copy(), retrieved_doc['sweights'].copy())
            score_event_sentence = greedy_mover_distance(task_doc['esembed_' + sembed_model], retrieved_doc['esembed_' + sembed_model], task_doc['esweights'].copy(), retrieved_doc['esweights'].copy())
            #print(f"task doc score sentence {score_sentence}    score_event   {score_event_sentence}")
            score_combined = (1-weight_dict['wevent']) * score_sentence + weight_dict['wevent'] * score_event_sentence
            #print(f"task score combined {score_combined}")
            
            task_doc_scores.append(score_combined)
            task_doc_event_scores.append(score_event_sentence)

        for request_doc in enriched_request_docs:
            if len(request_doc['highlight']) > 0:
                h = weight_dict['whighlight'] * request_doc['hembed_' + sembed_model]
                hw = weight_dict['whighlight'] * request_doc['hweight']
                score_sentence = greedy_mover_distance(request_doc['sembed_' + sembed_model] + h, retrieved_doc['sembed_' + sembed_model], request_doc['sweights'].copy() + hw.copy(), retrieved_doc['sweights'].copy())
            else:
                score_sentence = greedy_mover_distance(request_doc['sembed_' + sembed_model], retrieved_doc['sembed_' + sembed_model], request_doc['sweights'].copy(), retrieved_doc['sweights'].copy())

            score_event_sentence = greedy_mover_distance(request_doc['esembed_' + sembed_model], retrieved_doc['esembed_' + sembed_model], request_doc['esweights'].copy(), retrieved_doc['esweights'].copy())
            
            score_combined = (1-weight_dict['wevent']) * score_sentence + weight_dict['wevent'] * score_event_sentence
            request_doc_scores.append(score_combined)
            request_doc_event_scores.append(score_event_sentence)
        
        if VERBOSE == True:
            print(f"{task_doc_scores}")
            print(f"{request_doc_scores}")
            print(f"{task_doc_event_scores}")
            print(f"{request_doc_event_scores}")

        
        score_from_request_docs = sum([((weight_dict['wrequest'] / len(request_doc_scores)) * score)  for score in request_doc_scores])
        score_from_task_docs = sum([(( (1 - weight_dict['wrequest']) / len(task_doc_scores)) * score)  for score in task_doc_scores])
        score = score_from_request_docs + score_from_task_docs        
        scores.append((req_num, retrieved_doc['docid'], 1.0/(score+1), baseline_rank+1))
    
    return scores

def write_to_file(file_to_write, scores, retrieved_docs_after_k, run_name): 
    dummy_score = 100000
    rank = 1
    qid = scores[0][0]

    for i, item in enumerate(scores):
        output = qid + " " + "Q0" + " " + item[1] + " " + str(rank) + " " + str(dummy_score) + " " + run_name 
        dummy_score-= 1
        rank+=1
        file_to_write.write(output + "\n")

    for i, doc in enumerate(retrieved_docs_after_k):
        output = qid + " " + "Q0" + " " + doc['docid'] + " " + str(rank) + " " + str(dummy_score) + " " + run_name 
        dummy_score-= 1
        rank+=1
        file_to_write.write(output + "\n")
    
    
def write_scores_to_run_file(scores, retrieved_docs_after_k, baseline_run_file, semb_run_file, fused_run_file, semb, RRF_K):     
    #(req_num, docid, labse_score, baseline_rank+1, fused_score)                
    #writing baseline scores         
    
    write_to_file(baseline_run_file, scores, retrieved_docs_after_k, "baseline")
    
    labse_scores = sorted(scores, key=lambda x: x[2], reverse=True)    
    write_to_file(semb_run_file, labse_scores, retrieved_docs_after_k, "labse")

    all_scores = [] 
    
    for rank, score in enumerate(labse_scores):
        fused_score = (1/(RRF_K + rank + 1)) + (1/(RRF_K + score[3]))
        #(req_num, docid, labse_score, baseline_rank+1, fused_score)
        all_scores.append((score[0], score[1], score[2], score[3], fused_score))
    
    fusion_scores = sorted(all_scores, key=lambda x: x[4], reverse=True)
    write_to_file(fused_run_file, fusion_scores, retrieved_docs_after_k, "fusion")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--rrf_k", 
                        default= 6, 
                        type=int,
                        required=False,
                        help="set the value of k for reciprocal rank fusion"
                        )

    parser.add_argument("--task_file", 
                        default="analytic_tasks.json", 
                        type=str,
                        required=False,
                        help="please provide the location of the query file"
                        )

    parser.add_argument("--data_dir", 
                        default="data", 
                        type=str,
                        required=False,
                        help="please provide the location of data directory"
                        )

    parser.add_argument("--prefix", 
                        default="AUTO.", 
                        type=str,
                        required=False,
                        help="please provide the prefix for the REQUESTHITS files"
                        )

    parser.add_argument("--semb", 
                        default="labse", 
                        type=str,
                        required=False,
                        help="please provide the sentence embedding to use"
                        )

    parser.add_argument("--wevent", 
                        default=0.5, 
                        type=float,
                        required=False,
                        help="please provide the weight of events"
                        )

    parser.add_argument("--wrequest", 
                        default=0.8, 
                        type=float,
                        required=False,
                        help="please provide the weight of request"
                        )

    parser.add_argument("--whighlight", 
                        default=1, 
                        type=int,
                        required=False,
                        help="please provide the weight of highlights"
                        )

         

    args = parser.parse_args()

    # wevent decides how much weight to put on events and how much weight to put on sentences 
    # wrequest determines how much weight to put on the request portion of the query and how much on task 
    # whighlight determines how much the higlight is amplitied in the request document
    weight_dict = {'wevent': args.wevent, 'wrequest': args.wrequest, 'whighlight': args.whighlight}
    

    RRF_K = args.rrf_k
    TASK_FILE = args.task_file
    DATA_DIR = args.data_dir
    PREFIX = args.prefix
    os.makedirs(os.path.join(DATA_DIR, "path_to_runs"), exist_ok=True)
    
    start_time = time.time()
    
    SEMB = args.semb

    run_file_id = str(round(args.wevent, 2)) + "_" + str(round(args.wrequest, 2)) + "_" + str(args.whighlight) + "_"
    run_file_id = ""
    semb_run_file = open(os.path.join(DATA_DIR, "path_to_runs", run_file_id + SEMB + ".run"), "w")
    baseline_run_file = open(os.path.join(DATA_DIR, "path_to_runs", run_file_id + "baseline.run"), "w")
    fused_run_file = open(os.path.join(DATA_DIR, "path_to_runs", run_file_id + "fused.run"), "w")

    tasks = json.load(open(os.path.join(DATA_DIR, TASK_FILE)))
    K = 100


    for task in tasks:
        task_num = task['task-num']
        
        print(f"processing task {task_num}")
        #set_trace()
        tdocid2enriched = {} 
        task_docs = [task['task-docs'][task_doc_id] for task_doc_id in task['task-docs'].keys()]
        
        enriched_task_docs = []
        
        event_doc_freq = get_edoc_freq(task_docs)
        print(f"Computed event document frequency for the task")

        for task_doc_id in task['task-docs']:
            print(f"Embedding task document {task_doc_id}")
            task_doc = task['task-docs'][task_doc_id]
            enriched_task_doc = enrich_doc(task_doc, event_doc_freq, nlp)
            tdocid2enriched.setdefault(task_doc_id, task_doc)
            tdocid2enriched[task_doc_id] = enriched_task_doc 
            enriched_task_docs.append(enriched_task_doc)

        for request in task['requests']:
            if path.exists(os.path.join(DATA_DIR, PREFIX + request['req-num'] + ".REQUESTHITS.events.json")):                

                retrieved_docs = json.load(open(os.path.join(DATA_DIR, PREFIX + request['req-num'] + ".REQUESTHITS.events.json")))
                to_rerank = min(K, len(retrieved_docs))
                enriched_retrieved_docs = [enrich_doc(doc, event_doc_freq, nlp) for doc in retrieved_docs[0:to_rerank]]
                other_retrieved_docs = retrieved_docs[to_rerank:]
                
                enriched_request_docs = [] 
                
                print(f"Processing request {request['req-num']}")            
                print(f"Request text is {request['req-text']}")
                
                req_docs = request['req-docs']
                print(f"There are {len(request['req-docs'])} request documents")
                
                for key in req_docs.keys():                             
                    print(f"Processing request {key}")
                    req_doc = req_docs[key]
                    enriched_request_docs.append(enrich_doc(req_doc, event_doc_freq, nlp, req_doc=True))
                
                scores = compute_score(enriched_task_docs, enriched_request_docs, enriched_retrieved_docs, request['req-num'], args.semb, weight_dict, VERBOSE=False)     
                
                write_scores_to_run_file(scores, other_retrieved_docs, baseline_run_file, semb_run_file, fused_run_file, SEMB, RRF_K)
                
    semb_run_file.close()
    baseline_run_file.close()
    fused_run_file.close() 


    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == "__main__":
    main()

import json 
import os
from re import VERBOSE
from trectools import TrecRun, TrecEval, fusion
from trectools import TrecQrel, procedures
import numpy as np 

def get_task_document_dictionary(directory, file):
    """[Given the document returns a dictionary of {document_id, document_text} ]

    Args:
        directory ([type]): [description]
        file ([type]): [description]

    Returns:
        [type]: [description]
    """
 
    documents = json.load(open(os.path.join(directory, file)))
    print(f"loading file {os.path.join(directory, file)}")
    print(f"There are {len(documents)} documents")
    document_dictionary = {}
    #print(documents[0]["docText"])
    
    for document in documents:
        document_dictionary.setdefault((document["docid"].strip(), ""))
        document_dictionary[document["docid"]] = (document["docText"], document["events"])
    return document_dictionary


def write_fused_run(DATA_DIR="../data/for_sheikh", baseline_file="baseline.run", treatment_file="laser.run", output_file="baseline_laser_slen_fused.run"):
    """[Reciprocal Rank Fusion Approach for doing a fusion of the baseline and the treatment] 

    Args:
        DATA_DIR ([type]): [description]
        baseline_file (str, optional): [description]. Defaults to "baseline.run".
        treatment_file (str, optional): [description]. Defaults to "laser.run".
        output_file (str, optional): [description]. Defaults to "baseline_laser_slen_fused.run".
    """

    r1 = TrecRun(os.path.join(DATA_DIR, baseline_file))
    r2 = TrecRun(os.path.join(DATA_DIR, treatment_file))

    # Easy way to create new baselines by fusing existing runs:
    fused_run = fusion.reciprocal_rank_fusion([r1,r2], k=3)
    #fused_run = fusion.combos([r1,r2])
    # Save run to disk with all its topics
    fused_run.print_subset(os.path.join(DATA_DIR, output_file), topics=fused_run.topics())

def aggregate_results(DATA_DIR="../data/for_sheikh/laser", run_file="../laser.run", BEGIN=6, END=7, VERBOSE=False, BASELINE=False, DISTANCE=True):
    """
    [The results are computed as follows:
        For each request example document, we calculate the retrieved task document score. Thus, a task document retrieves a vector of scores for a request. 
        Then we compute the mean of the scores as the score of the task document for that request. This function takes an array of scores for the task document 
        and computes the mean.
        NOTE: it seems for the better evaluation only the rank matters, but not the score.]

    Args:
        DATA_DIR (str, optional): [The data di]. Defaults to "../data/for_sheikh/laser".
        run_file (str, optional): [Output file where results will be written]. Defaults to "../laser.run".
        BEGIN (int, optional): [This is an offset parameter for selecting a specific task]. Defaults to 6.
        END (int, optional): [This is an offset parameter for selecting a specific task]. Defaults to 7. 
        [BEGIN:END] by default will select task 6. 
        VERBOSE (bool, optional): [description]. Defaults to False.
        BASELINE (bool, optional): [If we are aggregating for the baseline run]. Defaults to False.
        BASELINE (bool, optional): [description]. Defaults to False.
    """
    
    task_ids = os.listdir(DATA_DIR)
    
    for task_id in task_ids[BEGIN:END]: 
    
        if VERBOSE == True:
            print(task_id)
    
        files = os.listdir(os.path.join(DATA_DIR, task_id))    
        result_files = [file for file in files if "res" in file]
        #print(result_files)
        
        for result_file in result_files:  
            results = json.load(open(os.path.join(DATA_DIR, task_id, result_file)))
            #print(f"results size {len(results)}")
            results_aggregated = [] 

            for result in results: 
                score = np.mean(result[4:-1])
                if score == 0:
                    results_aggregated.append(result[0:4] + [0] + [result[-1]])            
                else:
                    #we are inverting the score because the score has been computed in terms of distance. 
                    if DISTANCE == True:
                        results_aggregated.append(result[0:4] + [1/score] + [result[-1]])            
                    else: 
                        results_aggregated.append(result[0:4] + [score] + [result[-1]])            

            results_aggregated = sorted(results_aggregated, key=lambda x: x[4], reverse=True)        

            if BASELINE:
                score = 1000000
                for i, result in enumerate(results):            
                    run_file.write(" ".join(result[0:3]) + " " + str(i+1) + " " + str(score) + " " + result[-1] + "\n")
                    score-=1                
            else:
                for i, result in enumerate(results_aggregated):            
                    if result[4]!=0:
                        run_file.write(" ".join(result[0:3]) + " " + str(i+1) + " " + str(result[4]) + " " + result[-1] + "\n")
                    else:
                        run_file.write(" ".join(result[0:3]) + " " + str(i+1) + " " + str(0) + " " + result[-1] + "\n")
    run_file.close()


def aggregate_results_model(DATA_DIR="../data/for_sheikh/laser", run_file="../laser.run", BEGIN=6, END=7, VERBOSE=False, BASELINE=False, DISTANCE=True):
    """
    [The results are computed as follows:
        For each request example document, we calculate the retrieved task document score. Thus, a task document retrieves a vector of scores for a request. 
        Then we compute the mean of the scores as the score of the task document for that request. This function takes an array of scores for the task document 
        and computes the mean.
        NOTE: it seems for the better evaluation only the rank matters, but not the score.]

    Args:
        DATA_DIR (str, optional): [The data di]. Defaults to "../data/for_sheikh/laser".
        run_file (str, optional): [Output file where results will be written]. Defaults to "../laser.run".
        BEGIN (int, optional): [This is an offset parameter for selecting a specific task]. Defaults to 6.
        END (int, optional): [This is an offset parameter for selecting a specific task]. Defaults to 7. 
        [BEGIN:END] by default will select task 6. 
        VERBOSE (bool, optional): [description]. Defaults to False.
        BASELINE (bool, optional): [If we are aggregating for the baseline run]. Defaults to False.
        BASELINE (bool, optional): [description]. Defaults to False.
    """
    
    task_ids = os.listdir(DATA_DIR)
    
    for task_id in task_ids[BEGIN:END]: 
        
        if VERBOSE == True:
            print(task_id)
    
        files = os.listdir(os.path.join(DATA_DIR, task_id))    
        result_files = [file for file in files if "res" in file]
        #print(result_files)

        request_emb_files = [file for file in files if "enriched" in file and "DR" in file]
        number_of_all_request_documents = 0

        for request_emb_file in request_emb_files:
            number_of_all_request_documents+=len(json.load(open(os.path.join(DATA_DIR, task_id, request_emb_file))))


        for result_file in result_files:  
            request_list = json.load(open(os.path.join(DATA_DIR, task_id, result_file.split("_")[0] + ".json" )))            
            number_of_request_documents = len(request_list)
            flag = [] 
            #import pdb; pdb.set_trace()
            #for k in range(number_of_request_documents):            
            flag = number_of_request_documents * [0.5/(number_of_request_documents)] + number_of_all_request_documents * [0.5/(number_of_all_request_documents + number_of_request_documents)]
            results = json.load(open(os.path.join(DATA_DIR, task_id, result_file)))
            #print(f"results size {len(results)}")
            results_aggregated = [] 

            for result in results: 
                #score = np.mean(result[4:-1])
                
                score = np.sum(np.asarray(flag) * np.asarray(result[4:-1]))
                if score == 0:
                    results_aggregated.append(result[0:4] + [0] + [result[-1]])            
                else:
                    #we are inverting the score because the score has been computed in terms of distance. 
                    if DISTANCE == True:
                        results_aggregated.append(result[0:4] + [1/score] + [result[-1]])            
                    else: 
                        results_aggregated.append(result[0:4] + [score] + [result[-1]])            

            results_aggregated = sorted(results_aggregated, key=lambda x: x[4], reverse=True)        

            if BASELINE:
                score = 1000000
                for i, result in enumerate(results):            
                    run_file.write(" ".join(result[0:3]) + " " + str(i+1) + " " + str(score) + " " + result[-1] + "\n")
                    score-=1                
            else:
                for i, result in enumerate(results_aggregated):            
                    if result[4]!=0:
                        run_file.write(" ".join(result[0:3]) + " " + str(i+1) + " " + str(result[4]) + " " + result[-1] + "\n")
                    else:
                        run_file.write(" ".join(result[0:3]) + " " + str(i+1) + " " + str(0) + " " + result[-1] + "\n")
    run_file.close()





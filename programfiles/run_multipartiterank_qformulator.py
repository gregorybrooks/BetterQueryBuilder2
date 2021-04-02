import pke
import argparse
from translation_package.GalagoQT import GalagoQT
import json
import re



"""
Runs PKE library with the given unsupervised model and returns the extracted keywords and their weights
"""
def pke_unsupervised(cur_text, top_k, kw_extractor, lang='en', document_frequency_file=None):
    arg_tokens = kw_extractor.split('-')
    extractor = getattr(pke.unsupervised, arg_tokens[-1])()
    extractor.load_document(input=cur_text, language=lang)
    extractor.candidate_selection()
    if document_frequency_file is not None:
        df_counts = pke.load_document_frequency_file(input_file=document_frequency_file)
        extractor.candidate_weighting(df=df_counts)
    else: # go back to the default values 
        extractor.candidate_weighting()
    keyphrases = extractor.get_n_best(n=top_k)
    final_kw = [(score, term)  for term, score in keyphrases]
    return final_kw

"""
Writes galago format json queries into the given output path
"""
def write_topics(topics_all, topics_path_out):
    my_galago_topics_list = []
    for qnum, qtxt in topics_all.items():
        my_cur_topic_dict = {"number":qnum, "text":qtxt}
        my_galago_topics_list.append(my_cur_topic_dict)
    my_galago_topics_json = {'queries':my_galago_topics_list}
    with open(topics_path_out, 'w', encoding='utf-8') as f:
        json.dump(my_galago_topics_json, f, ensure_ascii=False, indent=4)

        

def construct_galago_query(keywords_with_score, QT_obejct, out_lang='en', combine_opt='sdm'): # combine or sdm
    weights_str = '#combine'
    words_str = ''
    phrase_index = 0
    for score, phrase in keywords_with_score:
        if out_lang=='ar':
            wrapped_phrase = QT_obejct.tranlate_phrase_sdm_syn(phrase, tran_top_k=2, trans_type='tt_syn_op')
        else:
            wrapped_phrase = _wrap_opt_phrase(phrase, combine_opt)
        if len(wrapped_phrase)>2:
            words_str += ' ' + wrapped_phrase
            weights_str += f':{phrase_index}={score}'
            phrase_index+=1
    final_query = f"{weights_str}({words_str})"
    return final_query

def construct_galago_query_no_phrasing(keywords_with_score):
    weights_str = '#combine'
    words_str = ''
    phrase_index = 0
    for score, phrase in keywords_with_score:
        wrapped_phrase = phrase
        if len(wrapped_phrase)>2:
            words_str += ' ' + wrapped_phrase
            weights_str += f':{phrase_index}={score}'
            phrase_index+=1
    final_query = f"{weights_str}({words_str})"
    return final_query


def _wrap_opt_phrase(text, combine_opt='sdm'):
    mytext = re.sub(r"[.,$\(\):;!?\"‘’]|'s\b", "", text).strip()
    tokens = mytext.split()
    if len(tokens)>1:
        return f"#{combine_opt}({mytext})"
    else:
        return mytext


def main(): 
    parser = argparse.ArgumentParser(description='Extracting, Translating, and Formulating BETTER projects queries using MultiPartiteRanking model of PKE python library...')
    
    parser.add_argument('--input_file', type=str, default='analytic_tasks.json', help='the file path of analytic_tasks.json file ')
    parser.add_argument('--output_file', type=str, default='test.queries.json', help='the file path for galago queries that this program would write into')
    parser.add_argument('--out_lang', type=str, default='ar', help='what language should it translate the queries')
    parser.add_argument('--program_directory', type=str, default='.', help='parent directory of translation_package and translation_tables')
    parser.add_argument('--mode', type=str, default='AUTO', help='AUTO, AUTO-HITL, or HITL')
    parser.add_argument('--phase', type=str, default='Request', help='Request or Task')

#    parser.add_argument('--tt_path', type=str, default='', help='path to the isi translation table of arabic to english ')
#    parser.add_argument('--muse_en_path', type=str, default='', help='path to english vectors of muse embeddings')
#    parser.add_argument('--muse_ar_path', type=str, default='', help='poth to arabic vectors of muse embeddings')
    
    args = parser.parse_args()
    print(f"arguments are received {args}")
    
    tt_path = args.program_directory + "translation_tables/unidirectional-with-null-en-ar.simple-tok.txt"
    muse_en_path = args.program_directory + "translation_package/muse/wiki.multi.en.vec"
    muse_ar_path = args.program_directory + "translation_package/muse/wiki.multi.ar.vec"

    ############
    ### Translation Module Loading
    ############
    myQT = None
    if args.out_lang=='ar':
        myQT = GalagoQT(tt_dir=tt_path, emb_src_path=muse_en_path, emb_tgt_path=muse_ar_path)
    
    
    ############
    ### Extract Keywords & Formualte & Translate
    ############ 
    with open(args.input_file, 'r') as f:
        eng_dry_run = json.load(f)
    
    
    final_topics_all = {}
    cur_kw_extractor = 'pke-usup-MultipartiteRank'
    cur_formulate_op = 'sdm'
    kw_top_k = 100

    for task in eng_dry_run: #'task-num', 'task-docs', 'task-title', 'task-stmt', 'requests', 'task-narr'
        tasknum = task['task-num']
        
        # 'task-title', 'task-stmt', 'task-narr'
        task_misc = []
        if 'task-title' in task:
            if task['task-title'] is not None:
                task_title = task['task-title'].strip()
                if len(task_title)>3:
                    if args.out_lang=='ar':
                        cur_task_galago_query = myQT.tranlate_phrase_sdm_syn(task_title, tran_top_k=2, trans_type='tt_syn_op')
                    else:
                        cur_task_galago_query = _wrap_opt_phrase(task_title, combine_opt=cur_formulate_op) 
                    task_misc.append(cur_task_galago_query)
        
        if 'task-stmt' in task:
            if task['task-stmt'] is not None:
                task_stmt = task['task-stmt'].strip()
                if len(task_stmt)>3:
                    if args.out_lang=='ar':
                        cur_task_galago_query = myQT.tranlate_phrase_sdm_syn(task_stmt, tran_top_k=2, trans_type='tt_syn_op')
                    else:
                        cur_task_galago_query = _wrap_opt_phrase(task_stmt, combine_opt=cur_formulate_op) 
                    task_misc.append(cur_task_galago_query)
                
        if 'task-narr' in task:
            if task['task-narr'] is not None:
                task_narr = task['task-narr'].strip()
                if len(task_narr)>3:
                    if args.out_lang=='ar':
                        cur_task_galago_query = myQT.tranlate_phrase_sdm_syn(task_narr, tran_top_k=2, trans_type='tt_syn_op')
                    else:
                        cur_task_galago_query = _wrap_opt_phrase(task_narr, combine_opt=cur_formulate_op) 
                    task_misc.append(cur_task_galago_query)
        

        # extract task level keywords and the query 
        task_docs = task['task-docs']
        task_doc_ids = list(task_docs.keys())
        cur_task_content = [task_docs[task_doc_id]['doc-text'] for task_doc_id in task_doc_ids]
        cur_task_text = ' '.join(cur_task_content)
        extracted_kws = pke_unsupervised(cur_task_text, kw_top_k, cur_kw_extractor)
        cur_task_galago_query = construct_galago_query(extracted_kws, myQT, args.out_lang, combine_opt=cur_formulate_op)
        
        if len(task_misc)>0:
            task_misc_galago_query = f"#combine( {' '.join(task_misc)} )"
            cur_task_galago_query = f'#combine:0=0.8:1=0.2( {cur_task_galago_query} {task_misc_galago_query} )'

        for req_obj in task['requests']: #'req-docs', 'req-text', 'req-num'
            req_num = req_obj['req-num']
            req_docs = req_obj['req-docs']
            req_doc_ids = list(req_docs.keys())
            
            
            final_req_query_parts = [(0.33, cur_task_galago_query)]
            
            #extract request level keywords and the query 
            cur_req_content = [req_docs[req_doc_id]['doc-text'] for req_doc_id in req_doc_ids]
            cur_req_doc_text = ' '.join(cur_req_content)
            extracted_kws_req = pke_unsupervised(cur_req_doc_text, kw_top_k, cur_kw_extractor, lang='en')
            cur_req_galago_query = construct_galago_query(extracted_kws_req, myQT, args.out_lang, combine_opt=cur_formulate_op)
            final_req_query_parts.append((0.33, cur_req_galago_query))

            # construct highlight part query (if exists)
            cur_req_highlights = [req_docs[req_doc_id].get('highlight', '').strip() for req_doc_id in req_doc_ids]
            cur_req_hl_text = ' '.join(cur_req_highlights)
            if len(cur_req_hl_text.strip())>3:
                if args.out_lang=='ar':
                    cur_req_hl_galago_query = myQT.tranlate_phrase_sdm_syn(cur_req_hl_text, tran_top_k=2, trans_type='tt_syn_op')
                else:
                    cur_req_hl_galago_query = _wrap_opt_phrase(cur_req_hl_text, combine_opt=cur_formulate_op) 
                final_req_query_parts.append((0.33, cur_req_hl_galago_query))
                    
            
            # extract req-text (if exists)
            if 'req-text' in req_obj:
                if req_obj['req-text'] is not None:
                    cur_req_text = req_obj['req-text'].strip()
                    if len(cur_req_text)>3:
                        if args.out_lang=='ar':
                            cur_req_text_galago_query = myQT.tranlate_phrase_sdm_syn(cur_req_text, tran_top_k=2, trans_type='tt_syn_op')
                        else:
                            cur_req_text_galago_query = _wrap_opt_phrase(cur_req_text, combine_opt=cur_formulate_op) 
                        final_req_query_parts.append((0.33, cur_req_text_galago_query))
            
            
             # construct the final query that consists of each of task, query, and highlight 
            cur_req_final_galago_query = construct_galago_query_no_phrasing(final_req_query_parts)
            final_topics_all[req_num] = cur_req_final_galago_query

    ############
    ### write the formulated quereis into the output path
    ############ 
    write_topics(final_topics_all, args.output_file)
    

if __name__ == "__main__":
    main()

import numpy as np
import arabic_reshaper
import unicodedata as ud
import io
import spacy
import string



"""
This class loads an arabic Translation Table (similar to ISI provided) and also word embeddings and 
can return different varieties of translated galago queries
"""
class GalagoQT:
    def __init__(self, tt_dir, emb_src_path=None, emb_tgt_path=None):
        self.eng_nlp = spacy.load("en_core_web_sm")
        
        # loading the translation table 
        self.tt_dict = self._load_translation_dict(tt_dir)
        
        # loading the embedding vectors
        if emb_src_path is not None:
            self.src_emb, self.src_id2word, self.src_word2id = self._muse_load_vec(emb_src_path)
            self.tgt_emb, self.tgt_id2word, self.tgt_word2id = self._muse_load_vec(emb_tgt_path)
            self.word2id = {v: k for k, v in self.src_id2word.items()}
    
    
    """
    Returns a translation of a phrase as a galago query,
    for example for english query "North Korea"
    returns '#sdm(#synonym(شمال الشمال) #synonym(كوريا الشمالية))'
    
    Specify trans_type for either translation table, or MUSE embeddings:
    1. (default) trans_type='tt_syn_op' get tran_top_k of translations from tt
    2. trans_type='clw_syn_op' get tran_top_k of translations from embedding
    3. trans_type='tt_clw_syn_op' get tran_top_k of translations from each of tt and embedding
    
    if top_trans=1 -> uses the translation itself without #synonym operator
    if num of tokens of phrase =1 -> do not put in #sdm operator
    """
    def tranlate_phrase_sdm_syn(self, ph_txt, tran_top_k, trans_type='tt_syn_op'):
        kw_tokens = self.spacy_english_tokenizer_and_cleaner(ph_txt)
        wrapped_kw = ''
        if len(kw_tokens)>=1:
            kw_tokens_translations = []
            for kw_token in kw_tokens:
                if trans_type=='tt_syn_op':
                    q_trans_tokens = self.get_tt_topk(kw_token, topk=tran_top_k)
                elif trans_type=='clw_syn_op':
                    q_trans_tokens = self.get_muse_topk(kw_token, topk=tran_top_k)
                elif trans_type=='tt_clw_syn_op':
                    tt_q_trans_tokens = self.get_tt_topk(kw_token, topk=tran_top_k)
                    clw_q_trans_tokens = self.get_muse_topk(kw_token, topk=tran_top_k)
                    tt_q_trans_tokens.extend(clw_q_trans_tokens)
                    q_trans_tokens = tt_q_trans_tokens
                q_trans_tokens = [token for score, token in q_trans_tokens]
                if len(q_trans_tokens)>1:
                    wrapped_trans = f"#synonym({' '.join(q_trans_tokens)})"
                else:
                    wrapped_trans = ' '.join(q_trans_tokens)
                kw_tokens_translations.append(wrapped_trans)

            if len(kw_tokens_translations)>1:
                wrapped_kw = f"#sdm({' '.join(kw_tokens_translations)})"
            else:
                wrapped_kw = f"{' '.join(kw_tokens_translations)}"
        return wrapped_kw
    
    
    
    """
    How to use: 
    mytrains = get_tt_topk("world", topk=2)

    [(0.619245, 'العالم'),
     (0.0974328, 'العالمية')
     ]
    """
    def get_tt_topk(self, src_token, topk=5):
        tgt_tokens = self.tt_dict.get(src_token, None)
        if tgt_tokens is not None:
            tgt_tokens = sorted(tgt_tokens, key = lambda x: x[0], reverse=True)
        else:
            tgt_tokens = [(1.0, src_token)]
        return tgt_tokens[:topk]
    
    
    def get_muse_topk(self, word, topk=5):
        if word in self.word2id:
            word_emb = self.src_emb[self.word2id[word]]
            scores = (self.tgt_emb / np.linalg.norm(self.tgt_emb, 2, 1)[:, None]).dot(word_emb / np.linalg.norm(word_emb))
            k_best = scores.argsort()[-topk:][::-1]
            tgt_tokens_topk = []
            for i, idx in enumerate(k_best):
                idx_word = self.tgt_id2word[idx]
                reshaped_ar_w = arabic_reshaper.reshape(idx_word)
                reshaped_ar_w = reshaped_ar_w.replace('#', '')
                tgt_tokens_topk.append((scores[idx], reshaped_ar_w))
        else:
            tgt_tokens_topk = [(1.0, word)]
        return tgt_tokens_topk
    
    
    def _load_translation_dict(self, tt_file):
        lines = open(tt_file, 'r', encoding='utf-8').readlines()
        tt_dict = {}
        for line in lines:
            # '"\tإليه\t4.47296e-05\n' -> ['en_term', 'ar_term', '0.458949']
            #line = remove_puncuations(line)
            line_splitted = line.strip().split('\t')
            if len(line_splitted)==3:
                src_token = self.remove_puncuations(line_splitted[0])
                tgt_token = self.remove_puncuations(line_splitted[1].replace('\t', ''))
                if len(src_token)==0 or len(tgt_token)==0:
                    continue
                score = float(line_splitted[2])
                trans_terms = tt_dict.get(src_token, [])
                trans_terms.append((score, tgt_token))
                tt_dict[src_token] = trans_terms
        return tt_dict
    
    def remove_puncuations(self, text):
        #s = "أهلاً بالعالم في هذه التجربة ! علامات ،الترقيم ؟ ,? لا .اتذكرها"
        # sout = 'أهلاً بالعالم في هذه التجربة  علامات الترقيم   لا اتذكرها'
        return ''.join(c for c in text if not ud.category(c).startswith('P'))


    # MUSE library loading the embedding and other things 
    # https://github.com/facebookresearch/MUSE/blob/master/demo.ipynb
    def _muse_load_vec(self, emb_path): #, nmax=50000
        vectors = []
        word2id = {}
        with io.open(emb_path, 'r', encoding='utf-8', newline='\n', errors='ignore') as f:
            next(f)
            for i, line in enumerate(f):
                word, vect = line.rstrip().split(' ', 1)
                vect = np.fromstring(vect, sep=' ')
                if vect.size==300:
                    assert word not in word2id, 'word found twice'
                    vectors.append(vect)
                    word2id[word] = len(word2id)
        #             if len(word2id) == nmax:
        #                 break
        id2word = {v: k for k, v in word2id.items()}
        embeddings = np.vstack(vectors)
        return embeddings, id2word, word2id
    
    """
    1. Remove puncutations
    Use spaCy for:
    1. Tokenize into words
    2. remove stopwords 
    """
    def spacy_english_tokenizer_and_cleaner(self, text):
        doc = self.eng_nlp(text.replace('#', ' '))  # phrase to tokenize
        eng_stopwords = self.eng_nlp.Defaults.stop_words
        text_tokens_clean = ' '.join([w.text.lower() for w in doc if not w.text.lower() in eng_stopwords])
        final_tokens = text_tokens_clean.translate(str.maketrans('', '', string.punctuation))
        return final_tokens.split()
    
    

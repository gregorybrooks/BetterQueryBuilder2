from GalagoQT import GalagoQT
# initialize
isi_tt_path = '/home/glbrooks/BETTER/translation_tables/unidirectional-with-null-en-ar.simple-tok.txt'
muse_emb_src_path = 'muse/wiki.multi.en.vec'
muse_emb_tgt_path = 'muse/wiki.multi.ar.vec'
myQT = GalagoQT(tt_dir=isi_tt_path, emb_src_path=muse_emb_src_path, emb_tgt_path=muse_emb_tgt_path)

translated_text = myQT.tranlate_phrase_sdm_syn("North Korea", tran_top_k=2, trans_type='tt_syn_op')
print(translated_text)

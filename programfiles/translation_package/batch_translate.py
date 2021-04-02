import sys
from GalagoQT import GalagoQT
#dir="/BETTER/programfiles/translation_package/"
dir=sys.argv[1] + "translation_package/"
def trace(text):
    f = open(dir + "debug.txt", "a")
    f.write(text)
    f.write("\n")
    f.close()

#isi_tt_path = '/BETTER/translation_tables/unidirectional-with-null-en-ar.simple-tok.txt'
isi_tt_path = sys.argv[1] + "translation_tables/unidirectional-with-null-en-ar.simple-tok.txt"
muse_emb_src_path = dir + 'muse/wiki.multi.en.vec'
muse_emb_tgt_path = dir + 'muse/wiki.multi.ar.vec'
myQT = GalagoQT(tt_dir=isi_tt_path, emb_src_path=muse_emb_src_path, emb_tgt_path=muse_emb_tgt_path)

for line in sys.stdin:
    trace("Calling GalagoQT")
    trace(str(len(line)))
    trace(line)
    translated_text = myQT.tranlate_phrase_sdm_syn(line, tran_top_k=2, trans_type='tt_syn_op')
    trace("Back from GalagoQT")
    trace(translated_text)
    print(translated_text)
sys.exit(0)

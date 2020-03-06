from typing import List, Dict, Optional, Tuple, Iterable, Set
import typing
import argparse
import sys
from collections import Counter
# import tarfile

import conllu
from conllu import TokenList
from conllu.parser import serialize_field

from ufal.udpipe import Pipeline, ProcessingError, Model


# TODO:
# * Add option to preserve input UPOS and FEATS.
# * Can PCC files be identified based on the ID?
#   <- YES
# * In .cupt metadata, is `orig_file_sentence` always consistent with
# `source_sent_id`?
#   <- ADD CHECK
# * For PCC, should we preserve tokenization?  What about non-PCC sentences?
#   <- YES, KEEP TOKENIZATION
# * Where to put new files?  Gitlab parseme_pl repo?


#################################################
# TYPES
#################################################


# Global columns meta-data
GlobalColumns = str


#################################################
# CONSTANTS
#################################################


# Global columns meta-data
GLOBAL_COLUMNS_KEY = "global.columns"

# MWE column
MWE_COL = "parseme:mwe"

# XPOS, UPOS, ...
XPOS = "xpos"
UPOS = "upos"
FEATS = "feats"
LEMMA = "lemma"


#################################################
# UTILS
#################################################


def get_sent_id(sent: TokenList) -> str:
    """Determine the sentence ID."""
    return sent.metadata["orig_file_sentence"].split('#')[0]


def collect_dataset(paths: List[str]) \
        -> Tuple[GlobalColumns, Iterable[TokenList]]:
    """Collect the dataset from the given .cupt files."""

    def get_columns():
        assert len(paths) > 0
        with open(paths[0], "r", encoding="utf-8") as data_file:
            header_line = data_file.readline().strip()
            if header_line.startswith("# " + GLOBAL_COLUMNS_KEY + " ="):
                assert "=" not in GLOBAL_COLUMNS_KEY
                return header_line.split("=")[1].strip()
            else:
                return None

    def iterate():
        for path in paths:
            with open(path, "r", encoding="utf-8") as data_file:
                for sent in conllu.parse_incr(data_file):
                    if GLOBAL_COLUMNS_KEY in sent.metadata:
                        del sent.metadata[GLOBAL_COLUMNS_KEY]
                    yield sent

    return get_columns(), iterate()


def write_glob_cols(cols, file):
    file.write("# " + GLOBAL_COLUMNS_KEY + " = " + cols + "\n")


#################################################
# SPLIT
#################################################


# The list of text ID prefixes which allow to identify the source.
SOURCE_PREFS = {"130-2", "130-3", "130-5", "120-", "310-", "330-"}

# The set of source IDs consists of text ID prefixes and PCC (the latter
# cannot be easily identified based on the text ID).
PCC = "PCC"
SOURCE_IDS = SOURCE_PREFS.union({PCC})


# The set of possible origin IDs
PDB = "PDB"
NKJP = "NKJP"
ORIG_IDS = [PCC, NKJP, PDB]


def text_source(text_id: str) -> str:
    """Determine the source of the sentence based on its ID.

    The set of source IDs (codomain of this function) is SOURCE_IDs.
    """
    for pref in SOURCE_PREFS:
        if text_id.startswith(pref):
            return pref
    return PCC


def is_pcc(text_id: str) -> bool:
    """Does the text with the given ID belong to PCC?"""
    return text_source(text_id) == PCC


def split_by_source(dataset: List[TokenList]) -> Dict[str, List[TokenList]]:
    """Split the given dataset based on source IDs."""
    res = dict((src, []) for src in SOURCE_IDS)
    for sent in dataset:
        src = text_source(get_sent_id(sent))
        if src not in SOURCE_IDS:
            raise Exception(f"{src} not in {SOURCE_IDS}")
        res[src].append(sent)
    return res


def split_by_origin(dataset: Iterable[TokenList], pdb_ud_ids: Set[str]) \
        -> Dict[str, List[TokenList]]:
    """Split the given dataset based on source IDs."""
    res = dict((orig, []) for orig in ORIG_IDS)
    for sent in dataset:
        sid = get_sent_id(sent)
        if sid in pdb_ud_ids:
            res[PDB].append(sent)
        elif is_pcc(sid):
            res[PCC].append(sent)
        else:
            res[NKJP].append(sent)
    return res


#################################################
# UDPipe
#################################################


def parse_raw_with_udpipe(model, text: str) -> List[TokenList]:
    """Use UDPipe to parse the given raw text."""
    pipeline = Pipeline(model, "tokenizer", Pipeline.DEFAULT,
                        Pipeline.DEFAULT, "conllu")
    error = ProcessingError()
    processed = pipeline.process(text, error)
    assert not error.occurred()
    parsed = conllu.parse(processed)
    # In metadata, keep only info about text
    for sent in parsed:
        meta = {'text': sent.metadata['text']}
        sent.metadata = meta
    return parsed


def parse_with_udpipe(model, sent: TokenList, use_tagger=True) -> TokenList:
    """Use UDPipe to parse the given .conllu sentence."""
    tagger_opt = Pipeline.DEFAULT if use_tagger else Pipeline.NONE
    pipeline = Pipeline(model, "conllu", tagger_opt,
                        Pipeline.DEFAULT, "conllu")
    error = ProcessingError()

    # Remove the MWE column if any
    mwes = []
    for tok in sent:
        if MWE_COL in tok:
            mwes.append(tok[MWE_COL])
            del tok[MWE_COL]

    # Perform parsing, check errors
    processed = pipeline.process(sent.serialize(), error)
    if error.occurred():
        print("ERROR: ", error.message)
    assert not error.occurred()
    parsed = conllu.parse(processed)
    assert len(parsed) == 1
    parsed = parsed[0]

    # Copy original metadata
    parsed.metadata = sent.metadata

    # Restore the MWE column
    for tok, mwe in zip(parsed, mwes):
        tok[MWE_COL] = mwe

    return parsed


#################################################
# ALIGNMENT
#################################################


def data_by_id(dataset: Iterable[TokenList]) -> Dict[str, TokenList]:
    """Determine the map from sentence IDs to sentences."""
    res = dict()
    for sent in dataset:
        sid = get_sent_id(sent)
        assert sid not in res
        res[sid] = sent
    return res


def align(source: Iterable[TokenList], dest: Iterable[TokenList]) \
        -> List[Tuple[TokenList, Optional[TokenList]]]:
    """For each sentence in `dest`, find the corresponding sentence
    in `source`.
    """
    source_by_id = data_by_id(source)
    res = []
    for dest_sent in dest:
        sid = get_sent_id(dest_sent)
        source_sent = source_by_id.get(sid)
        if source_sent and \
                dest_sent.metadata['text'] != source_sent.metadata['text']:
            print("# text metadata differs:", file=sys.stderr)
            print("dst:", dest_sent.metadata['text'], file=sys.stderr)
            print("src:", source_sent.metadata['text'], file=sys.stderr)
        res.append((source_sent, dest_sent))
    return res


#################################################
# TAGSET
#################################################


# Language-specific POS tag
XPos = str

# Lemma
Lemma = str

# UPOS and Features
UPos = str
Feats = str


def tagset_mapping(dataset: List[TokenList]) \
        -> Tuple[Dict[XPos, typing.Counter[UPos]],
                 Dict[XPos, typing.Counter[Feats]]]:
    """Determine the set of UPOS tags and feature dictionaries
    for each XPOS in the given dataset.
    """
    upos_map, feat_map = dict(), dict()

    def update_map(m, k, v):
        if k not in m:
            m[k] = Counter([v])
        else:
            m[k].update([v])

    for sent in dataset:
        for tok in sent:
            # print(tok)
            xpos = tok[XPOS]
            upos = tok[UPOS]
            feats = serialize_field(tok[FEATS])
            update_map(upos_map, xpos, upos)
            update_map(feat_map, xpos, feats)

    return upos_map, feat_map


def most_common(m: Dict[str, typing.Counter[str]]) \
        -> Dict[str, str]:
    """Pick the majofiryt class for each key in the input dict."""
    r = dict()
    for k, v in m.items():
        r[k] = v.most_common(1)[0][0]
    return r


def save_mapping(m: Dict[str, str], path: str):
    """Save mapping in the given file."""
    with open(path, "w", encoding="utf-8") as f:
        for k, v in m.items():
            print(f"{k}\t{v}", file=f)


def load_mapping(path: str) -> Dict[str, str]:
    """Load mapping from the given file."""
    m = dict()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            k, v = line.strip().split("\t")
            m[k] = v
    return m


def load_qub_mapping(path: str) -> Dict[Lemma, Tuple[UPos, Feats]]:
    """Load the mapping specified for qub's."""
    m = dict()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            lemma, xpos, _qub, feats = line.strip().split("\t")
            m[lemma] = (xpos, feats)
    return m


def load_manual_mapping(path: str) -> Dict[XPos, Tuple[UPos, Feats]]:
    """Load the mapping specified for qub's."""
    m = dict()
    with open(path, "r", encoding="utf-8") as f:
        f.readline()    # ignore header
        for line in f:
            xpos, upos, feats, *rest = line.strip().split("\t")
            m[xpos] = (upos, feats)
    return m


#################################################
# ARGUMENTS
#################################################


def mk_arg_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(description='parseme-pl')
    subparsers = parser.add_subparsers(
        dest='command', help='available commands')

    parser_split = subparsers.add_parser('split', help='split input files')
    parser_split.add_argument("-i",
                              dest="inp_paths",
                              required=True,
                              nargs='+',
                              help="input .conllu/.cupt files",
                              metavar="FILE")
    parser_split.add_argument("--pdb",
                              dest="pdb_paths",
                              required=True,
                              nargs='+',
                              help="input .conllu PDB files",
                              metavar="FILE")
    parser_split.add_argument("-o",
                              dest="out_dir",
                              required=True,
                              help="output directory",
                              metavar="DIR")
    # parser_split.add_argument("-s",
    #                         dest="source_id",
    #                         required=False,
    #                         help="source ID to handle",
    #                         metavar="FILE")

    parser_parse = subparsers.add_parser(
        'parse', help='parse (with UDPipe) input files')
    parser_parse.add_argument("-i",
                              dest="paths",
                              required=True,
                              nargs='+',
                              help="input .conllu/.cupt files",
                              metavar="FILE")
    parser_parse.add_argument("-m",
                              dest="udpipe_model",
                              required=True,
                              help="input UDPipe model",
                              metavar="FILE")
    parser_parse.add_argument("--raw",
                              dest="parse_raw",
                              action="store_true",
                              help="parse raw text (includes tokenization)")
    parser_parse.add_argument("--disable-tagger",
                              dest="disable_tagger",
                              action="store_true",
                              help="disable UDPipe tagger (only parsing)")

    parser_align = subparsers.add_parser(
        'align', help='align')
    parser_align.add_argument("-s",
                              dest="source",
                              required=True,
                              nargs='+',
                              help="source .conllu/.cupt files",
                              metavar="FILE")
    parser_align.add_argument("-d",
                              dest="dest",
                              required=True,
                              nargs='+',
                              help="dest .conllu/.cupt files",
                              metavar="FILE")

    # parser_conllu = subparsers.add_parser(
    #     'conllu', help='re-parse (with UDPipe) conllu raw .tar.gz')
    # parser_conllu.add_argument("-i",
    #                            dest="tar_path",
    #                            required=True,
    #                            help="input .tar.gz",
    #                            metavar="FILE")
    # parser_conllu.add_argument("-m",
    #                            dest="udpipe_model",
    #                            required=True,
    #                            help="input UDPipe model",
    #                            metavar="FILE")

    parser_tagset = subparsers.add_parser(
        'tagset', help='determine XPOS -> UPOS/Feats tagset conversion')
    parser_tagset.add_argument("-i",
                               dest="paths",
                               required=True,
                               nargs='+',
                               help="input .conllu/.cupt files",
                               metavar="FILE")
    parser_tagset.add_argument("--feats",
                               dest="feat_path",
                               required=True,
                               help="feature conversion map",
                               metavar="FILE")
    parser_tagset.add_argument("--upos",
                               dest="upos_path",
                               required=True,
                               help="upos conversion map",
                               metavar="FILE")

    parser_convert = subparsers.add_parser(
        'convert', help='convert the given file w.r.t. the given maps')
    parser_convert.add_argument("-i",
                                dest="paths",
                                required=True,
                                nargs='+',
                                help="input .conllu/.cupt files",
                                metavar="FILE")
    parser_convert.add_argument("--feats",
                                dest="feat_path",
                                required=True,
                                help="feature conversion map",
                                metavar="FILE")
    parser_convert.add_argument("--upos",
                                dest="upos_path",
                                required=True,
                                help="upos conversion map",
                                metavar="FILE")
    parser_convert.add_argument("--qub",
                                dest="qub_path",
                                required=True,
                                help="qub conversion map",
                                metavar="FILE")
    parser_convert.add_argument("--manual",
                                dest="man_path",
                                required=True,
                                help="manual conversion map",
                                metavar="FILE")

    return parser


#################################################
# SPLIT
#################################################


# Source identifiers
PDB_uri = "http://hdl.handle.net/11234/1-3105"
PDB_path = "UD_Polish-PDB"
PCC_uri = "http://zil.ipipan.waw.pl/PolishCoreferenceCorpus?action=AttachFile&do=get&target=PCC-0.92-TEI.zip"
# PCC_path = "."
NKJP_uri = "http://clip.ipipan.waw.pl/NationalCorpusOfPolish?action=AttachFile&do=get&target=NKJP-PodkorpusMilionowy-1.2.tar.gz"
# NKJP_path = "."


def do_split(args):
    glob_cols, dataset = collect_dataset(args.inp_paths)
    assert glob_cols is not None

    # datadict = split_by_source(dataset)
    pdb_ids = data_by_id(collect_dataset(args.pdb_paths)[1]).keys()
    datadict = split_by_origin(dataset, pdb_ud_ids=pdb_ids)

    for (src, sents) in datadict.items():
        out_path = args.out_dir + "/" + src + ".cupt"
        with open(out_path, "w", encoding="utf-8") as data_file:
            write_glob_cols(glob_cols, data_file)
            for sent in sents:
                # Update the source id information
                sid = get_sent_id(sent)
                if src == PDB:
                    src_sid = ' '.join([PDB_uri, PDB_path, sid])
                elif src == PCC:
                    file_id, *sid = sid.split("_")
                    sid = '_'.join(sid)
                    assert sid.startswith("morph")
                    path = "long/" + file_id + "/ann_morphosyntax.xml"
                    src_sid = ' '.join([PCC_uri, path, sid])
                elif src == NKJP:
                    file_id, *sid = sid.split("_")
                    sid = '_'.join(sid)
                    assert sid.startswith("morph")
                    path = file_id + "/ann_morphosyntax.xml"
                    src_sid = ' '.join([NKJP_uri, path, sid])
                else:
                    raise Exception("source unknown")
                # Update both IDs
                sent.metadata['orig_file_sentence'] = sid
                sent.metadata['source_sent_id'] = src_sid
                del sent.metadata['sent_id']
                # Serialize and print the updated sentence
                data_file.write(sent.serialize())


#################################################
# PARSE (NKJP, PCC)
#################################################


def do_parse(args):
    cols, dataset = collect_dataset(args.paths)
    model = Model.load(args.udpipe_model)
    if cols:
        write_glob_cols(cols, file=sys.stdout)
    for sent in dataset:
        if args.parse_raw:
            text = sent.metadata["text"]
            parsed = parse_raw_with_udpipe(model, text)
        else:
            use_tagger = not args.disable_tagger
            parsed = [parse_with_udpipe(model, sent, use_tagger=use_tagger)]
        for sent in parsed:
            # We don't want to keep orig_file_sentence for NKJP or PCC
            del sent.metadata['orig_file_sentence']
            print(sent.serialize(), end='')


#################################################
# ALIGN (PDB)
#################################################


def do_align(arcs):
    src_cols, source_data = collect_dataset(args.source)
    dst_cols, dest_data = collect_dataset(args.dest)
    assert src_cols is None  # we print it on output
    for src, dst in align(source_data, dest_data):
        # print(dst.metadata['text'])
        # print("=>", src is not None)
        assert src is not None

        # At this point we construct the metadata based
        # on the metadata present in the true PDB (source)
        sid = src.metadata['sent_id']
        src_sid = ' '.join([PDB_uri, PDB_path, sid])
        orig_sid = get_sent_id(src)
        text = src.metadata['text']
        src.metadata = {}
        src.metadata['source_sent_id'] = src_sid
        src.metadata['orig_file_sentence'] = orig_sid
        src.metadata['text'] = text

        # Print
        print(src.serialize(), end='')


#################################################
# TAGSET
#################################################


def do_tagset(args):
    dataset = collect_dataset(args.paths)
    upos_map, feat_map = tagset_mapping(dataset)
    upos_map = most_common(upos_map)
    feat_map = most_common(feat_map)
    save_mapping(upos_map, args.upos_path)
    save_mapping(feat_map, args.feat_path)


def do_convert(args):
    # Load conversion maps
    upos_map = load_mapping(args.upos_path)
    feat_map = load_mapping(args.feat_path)
    main_map = {
        key: (upos_map[key], feat_map[key])
        for key in upos_map.keys()
    }
    qub_map = load_qub_mapping(args.qub_path)
    man_map = load_manual_mapping(args.man_path)

    # # Conversion w.r.t to the given conversion map
    # def convert(m, x, todo):
    #     if x in m:
    #         return m[x]
    #     else:
    #         return todo

    # def convert_sent(conv, dest_col, sent, todo):
    #     for tok in sent:
    #         # print("A", tok, file=sys.stderr)
    #         xpos = tok['xpostag']
    #         tok[dest_col] = convert(conv, xpos, todo)
    #         # print("B", tok, file=sys.stderr)

    def convert_tok(tok):
        xpos = tok[XPOS]
        if xpos == 'qub':
            default = "PART", "_"
            upos, feats = qub_map.get(tok[LEMMA], default)
        elif xpos in man_map:
            upos, feats = man_map[xpos]
        else:
            default = "TODO", "_"
            upos, feats = main_map.get(xpos, default)
        tok[UPOS] = upos
        tok[FEATS] = feats

    # Process dataset
    cols, dataset = collect_dataset(args.paths)
    if cols:
        write_glob_cols(cols, file=sys.stdout)
    for sent in dataset:
        for tok in sent:
            convert_tok(tok)
        # convert_sent(upos_map, 'upostag', sent, "TODO")
        # convert_sent(feat_map, 'feats', sent, "TODO=TODO")
        print(sent.serialize(), end='')


#################################################
# MAIN
#################################################


if __name__ == '__main__':
    parser = mk_arg_parser()
    args = parser.parse_args()
    if args.command == 'split':
        do_split(args)
    if args.command == 'parse':
        do_parse(args)
    if args.command == 'align':
        do_align(args)
    if args.command == 'tagset':
        do_tagset(args)
    if args.command == 'convert':
        do_convert(args)

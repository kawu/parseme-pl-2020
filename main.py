from typing import List, Dict, Optional, Tuple
import argparse
import sys
import tarfile

import conllu
from conllu import TokenList

from ufal.udpipe import Pipeline, ProcessingError, Model


#################################################
# UTILS
#################################################


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


# The list of text ID prefixes which allow to identify the source.
SOURCE_PREFS = {"130-2", "130-3", "130-5", "120-", "310-", "330-"}

# The set of source IDs consists of text ID prefixes and PCC (the latter
# cannot be easily identified based on the text ID).
PCC = "PCC"
SOURCE_IDS = SOURCE_PREFS.union({PCC})


def text_source(text_id: str) -> str:
    """Determine the source of the sentence based on its ID.

    The set of source IDs (codomain of this function) is SOURCE_IDs.
    """
    for pref in SOURCE_PREFS:
        if text_id.startswith(pref):
            return pref
    return PCC


def get_sent_id(sent: TokenList) -> str:
    """Determine the sentence ID."""
    return sent.metadata["orig_file_sentence"].split('#')[0]


def split_by_source(dataset: List[TokenList]) -> Dict[str, List[TokenList]]:
    """Split the given dataset based on source IDs."""
    res = dict((src, []) for src in SOURCE_IDS)
    for sent in dataset:
        src = text_source(get_sent_id(sent))
        if src not in SOURCE_IDS:
            raise Exception(f"{src} not in {SOURCE_IDS}")
        res[src].append(sent)
    return res


def collect_dataset(paths: List[str]) -> List[TokenList]:
    """Collect the dataset from the given .cupt files."""
    dataset = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as data_file:
            for sent in conllu.parse_incr(data_file):
                dataset.append(sent)
    return dataset


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
    return conllu.parse(processed)


def parse_with_udpipe(model, sent: TokenList, use_tagger=True) -> TokenList:
    """Use UDPipe to parse the given .conllu sentence."""
    tagger_opt = Pipeline.DEFAULT if use_tagger else Pipeline.NONE
    pipeline = Pipeline(model, "conllu", tagger_opt,
                        Pipeline.DEFAULT, "conllu")
    error = ProcessingError()
    processed = pipeline.process(sent.serialize(), error)
    assert not error.occurred()
    parsed = conllu.parse(processed)
    assert len(parsed) == 1
    return parsed[0]


#################################################
# ALIGNMENT
#################################################


def data_by_id(dataset: List[TokenList]) -> Dict[str, TokenList]:
    """Determine the map from sentence IDs to sentences."""
    res = dict()
    for sent in dataset:
        sid = get_sent_id(sent)
        assert sid not in res
        res[sid] = sent
    return res


def align(source: List[TokenList], dest: List[TokenList]) \
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
# ARGUMENTS
#################################################


def mk_arg_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(description='parseme-pl')
    subparsers = parser.add_subparsers(
        dest='command', help='available commands')

    parser_split = subparsers.add_parser('split', help='split input files')
    parser_split.add_argument("-i",
                              dest="paths",
                              required=True,
                              nargs='+',
                              help="input .conllu/.cupt files",
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

    return parser


#################################################
# SPLIT
#################################################


def do_split(args):
    dataset = collect_dataset(args.paths)
    datadict = split_by_source(dataset)
    for (src, sents) in datadict.items():
        out_path = args.out_dir + "/" + src + ".cupt"
        with open(out_path, "w", encoding="utf-8") as data_file:
            for sent in sents:
                # Serialize and print the updated sentence
                data_file.write(sent.serialize())


#################################################
# PARSE
#################################################


def do_parse(args):
    dataset = collect_dataset(args.paths)
    model = Model.load(args.udpipe_model)
    for sent in dataset:
        if args.parse_raw:
            text = sent.metadata["text"]
            parsed = parse_raw_with_udpipe(model, text)
        else:
            use_tagger = not args.disable_tagger
            parsed = [parse_with_udpipe(model, sent, use_tagger=use_tagger)]
        for sent in parsed:
            print(sent.serialize(), end='')


#################################################
# PROCESS conllu .tar.xz
#################################################


# def do_process_conllu(args):
#     print("# reading model:", args.udpipe_model)
#     model = Model.load(args.udpipe_model)
#     tar = tarfile.open(args.tar_path, "r:*", encoding="utf-8")
#     for member in tar.getmembers():
#         print("#", member.name)
#         # with out_file =
#         inp_file = tar.extractfile(member)
#         for sent in conllu.parse_incr(inp_file):
#             text = sent.metadata["text"]
#             parsed = parse_raw_with_udpipe(model, text)
#             for sent in parsed:
#                 print(sent.serialize(), end='')
#         # if f is not None:
#         #     dataset =


#################################################
# ALIGN
#################################################


def do_align(arcs):
    source_data = collect_dataset(args.source)
    dest_data = collect_dataset(args.dest)
    for src, dst in align(source_data, dest_data):
        # print(dst.metadata['text'])
        # print("=>", src is not None)
        assert src is not None
        print(src.serialize(), end='')


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
    # if args.command == 'conllu':
    #     do_process_conllu(args)

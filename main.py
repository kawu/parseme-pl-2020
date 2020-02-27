from typing import List, Dict
import argparse
import conllu
from conllu import TokenList

from ufal.udpipe import Pipeline, ProcessingError, Model


#################################################
# UTILS
#################################################


# TODO:
# * Can PCC files be identified based on the ID?
# * In .cupt metadata, is `orig_file_sentence` always consistent with
# `source_sent_id`?
# * For PCC, should we preserve tokenization?  What about non-PCC sentences?
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


def split_by_ids(dataset: List[TokenList]) -> Dict[str, List[TokenList]]:
    """Split the given dataset based on IDs."""
    res = dict((src, []) for src in SOURCE_IDS)
    for sent in dataset:
        src = text_source(sent.metadata["orig_file_sentence"])
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


def parse_with_udpipe(model, sent: TokenList) -> TokenList:
    """Use UDPipe to parse the given .conllu sentence."""
    pipeline = Pipeline(model, "conllu", Pipeline.DEFAULT,
                        Pipeline.DEFAULT, "conllu")
    error = ProcessingError()
    processed = pipeline.process(sent.serialize(), error)
    assert not error.occurred()
    parsed = conllu.parse(processed)
    assert len(parsed) == 1
    return parsed[0]


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

    return parser


#################################################
# SPLIT
#################################################


def do_split(args):
    dataset = collect_dataset(args.paths)
    datadict = split_by_ids(dataset)
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
            parsed = [parse_with_udpipe(model, sent)]
        for sent in parsed:
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

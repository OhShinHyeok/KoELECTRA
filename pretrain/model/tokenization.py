# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors, The HuggingFace Inc. team and Jangwon Park
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tokenization classes."""

import collections
import logging
import os
import unicodedata
from typing import List, Optional

from transformers.tokenization_utils import PreTrainedTokenizer

logger = logging.getLogger(__name__)

VOCAB_FILES_NAMES = {"vocab_file": "vocab.txt"}

PRETRAINED_VOCAB_FILES_MAP = {}

PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES = {}

PRETRAINED_INIT_CONFIGURATION = {}


def load_vocab(vocab_file):
    """Loads a vocabulary file into a dictionary."""
    vocab = collections.OrderedDict()
    with open(vocab_file, "r", encoding="utf-8") as reader:
        tokens = reader.readlines()
    for index, token in enumerate(tokens):
        token = token.rstrip("\n")
        vocab[token] = index
    return vocab


def whitespace_tokenize(text):
    """Runs basic whitespace cleaning and splitting on a piece of text."""
    text = text.strip()
    if not text:
        return []
    tokens = text.split()
    return tokens


class KoCharElectraTokenizer(PreTrainedTokenizer):
    r"""
    Korean Character Electra tokenizer. Character-level Tokenizer
    This tokenizer inherits from :class:`~transformers.PreTrainedTokenizer` which contains most of the methods. Users
    should refer to the superclass for more information regarding methods.
    Args:
        vocab_file (:obj:`string`):
            File containing the vocabulary.
        do_lower_case (:obj:`bool`, `optional`, defaults to :obj:`True`):
            Whether to lowercase the input when tokenizing.
        do_basic_tokenize (:obj:`bool`, `optional`, defaults to :obj:`True`):
            Whether to do basic tokenization before WordPiece.
        never_split (:obj:`bool`, `optional`, defaults to :obj:`True`):
            List of tokens which will never be split during tokenization. Only has an effect when
            :obj:`do_basic_tokenize=True`
        unk_token (:obj:`string`, `optional`, defaults to "[UNK]"):
            The unknown token. A token that is not in the vocabulary cannot be converted to an ID and is set to be this
            token instead.
        sep_token (:obj:`string`, `optional`, defaults to "[SEP]"):
            The separator token, which is used when building a sequence from multiple sequences, e.g. two sequences
            for sequence classification or for a text and a question for question answering.
            It is also used as the last token of a sequence built with special tokens.
        pad_token (:obj:`string`, `optional`, defaults to "[PAD]"):
            The token used for padding, for example when batching sequences of different lengths.
        cls_token (:obj:`string`, `optional`, defaults to "[CLS]"):
            The classifier token which is used when doing sequence classification (classification of the whole
            sequence instead of per-token classification). It is the first token of the sequence when built with
            special tokens.
        mask_token (:obj:`string`, `optional`, defaults to "[MASK]"):
            The token used for masking values. This is the token used when training this model with masked language
            modeling. This is the token which the model will try to predict.
        tokenize_chinese_chars (:obj:`bool`, `optional`, defaults to :obj:`True`):
            Whether to tokenize Chinese characters.
            This should likely be deactivated for Japanese:
            see: https://github.com/huggingface/transformers/issues/328
    """
    vocab_files_names = VOCAB_FILES_NAMES
    pretrained_vocab_files_map = PRETRAINED_VOCAB_FILES_MAP
    pretrained_init_configuration = PRETRAINED_INIT_CONFIGURATION
    max_model_input_sizes = PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES

    def __init__(
        self,
        vocab_file,
        do_lower_case=False,
        do_basic_tokenize=True,
        never_split=None,
        unk_token="[UNK]",
        sep_token="[SEP]",
        pad_token="[PAD]",
        cls_token="[CLS]",
        mask_token="[MASK]",
        tokenize_chinese_chars=True,
        **kwargs
    ):
        super().__init__(
            unk_token=unk_token,
            sep_token=sep_token,
            pad_token=pad_token,
            cls_token=cls_token,
            mask_token=mask_token,
            **kwargs,
        )

        if not os.path.isfile(vocab_file):
            raise ValueError(
                "Can't find a vocabulary file at path '{}'. To load the vocabulary from a Google pretrained "
                "model use `tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)`".format(vocab_file)
            )
        self.vocab = load_vocab(vocab_file)
        self.ids_to_tokens = collections.OrderedDict([(ids, tok) for tok, ids in self.vocab.items()])

    @property
    def vocab_size(self):
        return len(self.vocab)

    def get_vocab(self):
        return dict(self.vocab, **self.added_tokens_encoder)

    def _tokenize(self, text):
        return list(" ".join(text.split()))  # Erase duplicate space

    def _convert_token_to_id(self, token):
        """ Converts a token (str) in an id using the vocab. """
        return self.vocab.get(token, self.vocab.get(self.unk_token))

    def _convert_id_to_token(self, index):
        """Converts an index (integer) in a token (str) using the vocab."""
        return self.ids_to_tokens.get(index, self.unk_token)

    def convert_tokens_to_string(self, tokens):
        """ Converts a sequence of tokens (string) in a single string. """
        return "".join(tokens).strip()

    def build_inputs_with_special_tokens(
        self, token_ids_0: List[int], token_ids_1: Optional[List[int]] = None
    ) -> List[int]:
        """
        Build model inputs from a sequence or a pair of sequence for sequence classification tasks
        by concatenating and adding special tokens.
        A BERT sequence has the following format:
        - single sequence: ``[CLS] X [SEP]``
        - pair of sequences: ``[CLS] A [SEP] B [SEP]``
        Args:
            token_ids_0 (:obj:`List[int]`):
                List of IDs to which the special tokens will be added
            token_ids_1 (:obj:`List[int]`, `optional`, defaults to :obj:`None`):
                Optional second list of IDs for sequence pairs.
        Returns:
            :obj:`List[int]`: list of `input IDs <../glossary.html#input-ids>`__ with the appropriate special tokens.
        """
        if token_ids_1 is None:
            return [self.cls_token_id] + token_ids_0 + [self.sep_token_id]
        cls = [self.cls_token_id]
        sep = [self.sep_token_id]
        return cls + token_ids_0 + sep + token_ids_1 + sep

    def get_special_tokens_mask(
        self, token_ids_0: List[int], token_ids_1: Optional[List[int]] = None, already_has_special_tokens: bool = False
    ) -> List[int]:
        """
        Retrieves sequence ids from a token list that has no special tokens added. This method is called when adding
        special tokens using the tokenizer ``prepare_for_model`` or ``encode_plus`` methods.
        Args:
            token_ids_0 (:obj:`List[int]`):
                List of ids.
            token_ids_1 (:obj:`List[int]`, `optional`, defaults to :obj:`None`):
                Optional second list of IDs for sequence pairs.
            already_has_special_tokens (:obj:`bool`, `optional`, defaults to :obj:`False`):
                Set to True if the token list is already formatted with special tokens for the model
        Returns:
            :obj:`List[int]`: A list of integers in the range [0, 1]: 0 for a special token, 1 for a sequence token.
        """

        if already_has_special_tokens:
            if token_ids_1 is not None:
                raise ValueError(
                    "You should not supply a second sequence if the provided sequence of "
                    "ids is already formated with special tokens for the model."
                )
            return list(map(lambda x: 1 if x in [self.sep_token_id, self.cls_token_id] else 0, token_ids_0))

        if token_ids_1 is not None:
            return [1] + ([0] * len(token_ids_0)) + [1] + ([0] * len(token_ids_1)) + [1]
        return [1] + ([0] * len(token_ids_0)) + [1]

    def create_token_type_ids_from_sequences(
        self, token_ids_0: List[int], token_ids_1: Optional[List[int]] = None
    ) -> List[int]:
        """
        Creates a mask from the two sequences passed to be used in a sequence-pair classification task.
        A BERT sequence pair mask has the following format:
        ::
            0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1
            | first sequence    | second sequence |
        if token_ids_1 is None, only returns the first portion of the mask (0's).
        Args:
            token_ids_0 (:obj:`List[int]`):
                List of ids.
            token_ids_1 (:obj:`List[int]`, `optional`, defaults to :obj:`None`):
                Optional second list of IDs for sequence pairs.
        Returns:
            :obj:`List[int]`: List of `token type IDs <../glossary.html#token-type-ids>`_ according to the given
            sequence(s).
        """
        sep = [self.sep_token_id]
        cls = [self.cls_token_id]
        if token_ids_1 is None:
            return len(cls + token_ids_0 + sep) * [0]
        return len(cls + token_ids_0 + sep) * [0] + len(token_ids_1 + sep) * [1]

    def save_vocabulary(self, vocab_path):
        """
        Save the sentencepiece vocabulary (copy original file) and special tokens file to a directory.
        Args:
            vocab_path (:obj:`str`):
                The directory in which to save the vocabulary.
        Returns:
            :obj:`Tuple(str)`: Paths to the files saved.
        """
        index = 0
        if os.path.isdir(vocab_path):
            vocab_file = os.path.join(vocab_path, VOCAB_FILES_NAMES["vocab_file"])
        else:
            vocab_file = vocab_path
        with open(vocab_file, "w", encoding="utf-8") as writer:
            for token, token_index in sorted(self.vocab.items(), key=lambda kv: kv[1]):
                if index != token_index:
                    logger.warning(
                        "Saving vocabulary to {}: vocabulary indices are not consecutive."
                        " Please check that the vocabulary is not corrupted!".format(vocab_file)
                    )
                    index = token_index
                writer.write(token + "\n")
                index += 1
        return (vocab_file,)

# # coding=utf-8
# # Copyright 2020 The Google Research Authors.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
#
# """Tokenization classes, the same as used for BERT."""
#
# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function
#
# import collections
# import unicodedata
# import six
# import tensorflow.compat.v1 as tf
#
#
#
# def convert_to_unicode(text):
#   """Converts `text` to Unicode (if it's not already), assuming utf-8 input."""
#   if six.PY3:
#     if isinstance(text, str):
#       return text
#     elif isinstance(text, bytes):
#       return text.decode("utf-8", "ignore")
#     else:
#       raise ValueError("Unsupported string type: %s" % (type(text)))
#   elif six.PY2:
#     if isinstance(text, str):
#       return text.decode("utf-8", "ignore")
#     elif isinstance(text, unicode):
#       return text
#     else:
#       raise ValueError("Unsupported string type: %s" % (type(text)))
#   else:
#     raise ValueError("Not running on Python2 or Python 3?")
#
#
# def printable_text(text):
#   """Returns text encoded in a way suitable for print or `tf.logging`."""
#
#   # These functions want `str` for both Python2 and Python3, but in one case
#   # it's a Unicode string and in the other it's a byte string.
#   if six.PY3:
#     if isinstance(text, str):
#       return text
#     elif isinstance(text, bytes):
#       return text.decode("utf-8", "ignore")
#     else:
#       raise ValueError("Unsupported string type: %s" % (type(text)))
#   elif six.PY2:
#     if isinstance(text, str):
#       return text
#     elif isinstance(text, unicode):
#       return text.encode("utf-8")
#     else:
#       raise ValueError("Unsupported string type: %s" % (type(text)))
#   else:
#     raise ValueError("Not running on Python2 or Python 3?")
#
#
# def load_vocab(vocab_file):
#   """Loads a vocabulary file into a dictionary."""
#   vocab = collections.OrderedDict()
#   index = 0
#   with tf.io.gfile.GFile(vocab_file, "r") as reader:
#     while True:
#       token = convert_to_unicode(reader.readline())
#       if not token:
#         break
#       token = token.strip()
#       vocab[token] = index
#       index += 1
#   return vocab
#
#
# def convert_by_vocab(vocab, items):
#   """Converts a sequence of [tokens|ids] using the vocab."""
#   output = []
#   for item in items:
#     output.append(vocab[item])
#   return output
#
#
# def convert_tokens_to_ids(vocab, tokens):
#   return convert_by_vocab(vocab, tokens)
#
#
# def convert_ids_to_tokens(inv_vocab, ids):
#   return convert_by_vocab(inv_vocab, ids)
#
#
# def whitespace_tokenize(text):
#   """Runs basic whitespace cleaning and splitting on a piece of text."""
#   text = text.strip()
#   if not text:
#     return []
#   tokens = text.split()
#   return tokens
#
#
# class FullTokenizer(object):
#   """Runs end-to-end tokenziation."""
#
#   def __init__(self, vocab_file, do_lower_case=True):
#     self.vocab = load_vocab(vocab_file)
#     self.inv_vocab = {v: k for k, v in self.vocab.items()}
#     self.basic_tokenizer = BasicTokenizer(do_lower_case=do_lower_case)
#     self.wordpiece_tokenizer = WordpieceTokenizer(vocab=self.vocab)
#
#   def tokenize(self, text):
#     split_tokens = []
#     for token in self.basic_tokenizer.tokenize(text):
#       for sub_token in self.wordpiece_tokenizer.tokenize(token):
#         split_tokens.append(sub_token)
#
#     return split_tokens
#
#   def convert_tokens_to_ids(self, tokens):
#     return convert_by_vocab(self.vocab, tokens)
#
#   def convert_ids_to_tokens(self, ids):
#     return convert_by_vocab(self.inv_vocab, ids)
#
#
# class BasicTokenizer(object):
#   """Runs basic tokenization (punctuation splitting, lower casing, etc.)."""
#
#   def __init__(self, do_lower_case=True):
#     """Constructs a BasicTokenizer.
#
#     Args:
#       do_lower_case: Whether to lower case the input.
#     """
#     self.do_lower_case = do_lower_case
#
#   def tokenize(self, text):
#     """Tokenizes a piece of text."""
#     text = convert_to_unicode(text)
#     text = self._clean_text(text)
#
#     # This was added on November 1st, 2018 for the multilingual and Chinese
#     # models. This is also applied to the English models now, but it doesn't
#     # matter since the English models were not trained on any Chinese data
#     # and generally don't have any Chinese data in them (there are Chinese
#     # characters in the vocabulary because Wikipedia does have some Chinese
#     # words in the English Wikipedia.).
#     text = self._tokenize_chinese_chars(text)
#
#     orig_tokens = whitespace_tokenize(text)
#     split_tokens = []
#     for token in orig_tokens:
#       if self.do_lower_case:
#         token = token.lower()
#         token = self._run_strip_accents(token)
#       split_tokens.extend(self._run_split_on_punc(token))
#
#     output_tokens = whitespace_tokenize(" ".join(split_tokens))
#     return output_tokens
#
#   def _run_strip_accents(self, text):
#     """Strips accents from a piece of text."""
#     text = unicodedata.normalize("NFD", text)
#     output = []
#     for char in text:
#       cat = unicodedata.category(char)
#       if cat == "Mn":
#         continue
#       output.append(char)
#     return "".join(output)
#
#   def _run_split_on_punc(self, text):
#     """Splits punctuation on a piece of text."""
#     chars = list(text)
#     i = 0
#     start_new_word = True
#     output = []
#     while i < len(chars):
#       char = chars[i]
#       if _is_punctuation(char):
#         output.append([char])
#         start_new_word = True
#       else:
#         if start_new_word:
#           output.append([])
#         start_new_word = False
#         output[-1].append(char)
#       i += 1
#
#     return ["".join(x) for x in output]
#
#   def _tokenize_chinese_chars(self, text):
#     """Adds whitespace around any CJK character."""
#     output = []
#     for char in text:
#       cp = ord(char)
#       if self._is_chinese_char(cp):
#         output.append(" ")
#         output.append(char)
#         output.append(" ")
#       else:
#         output.append(char)
#     return "".join(output)
#
#   def _is_chinese_char(self, cp):
#     """Checks whether CP is the codepoint of a CJK character."""
#     # This defines a "chinese character" as anything in the CJK Unicode block:
#     #   https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)
#     #
#     # Note that the CJK Unicode block is NOT all Japanese and Korean characters,
#     # despite its name. The modern Korean Hangul alphabet is a different block,
#     # as is Japanese Hiragana and Katakana. Those alphabets are used to write
#     # space-separated words, so they are not treated specially and handled
#     # like the all of the other languages.
#     if ((cp >= 0x4E00 and cp <= 0x9FFF) or  #
#         (cp >= 0x3400 and cp <= 0x4DBF) or  #
#         (cp >= 0x20000 and cp <= 0x2A6DF) or  #
#         (cp >= 0x2A700 and cp <= 0x2B73F) or  #
#         (cp >= 0x2B740 and cp <= 0x2B81F) or  #
#         (cp >= 0x2B820 and cp <= 0x2CEAF) or
#         (cp >= 0xF900 and cp <= 0xFAFF) or  #
#         (cp >= 0x2F800 and cp <= 0x2FA1F)):  #
#       return True
#
#     return False
#
#   def _clean_text(self, text):
#     """Performs invalid character removal and whitespace cleanup on text."""
#     output = []
#     for char in text:
#       cp = ord(char)
#       if cp == 0 or cp == 0xfffd or _is_control(char):
#         continue
#       if _is_whitespace(char):
#         output.append(" ")
#       else:
#         output.append(char)
#     return "".join(output)
#
#
# class WordpieceTokenizer(object):
#   """Runs WordPiece tokenziation."""
#
#   def __init__(self, vocab, unk_token="[UNK]", max_input_chars_per_word=200):
#     self.vocab = vocab
#     self.unk_token = unk_token
#     self.max_input_chars_per_word = max_input_chars_per_word
#
#   def tokenize(self, text):
#     """Tokenizes a piece of text into its word pieces.
#
#     This uses a greedy longest-match-first algorithm to perform tokenization
#     using the given vocabulary.
#
#     For example:
#       input = "unaffable"
#       output = ["un", "##aff", "##able"]
#
#     Args:
#       text: A single token or whitespace separated tokens. This should have
#         already been passed through `BasicTokenizer.
#
#     Returns:
#       A list of wordpiece tokens.
#     """
#
#     text = convert_to_unicode(text)
#
#     output_tokens = []
#     for token in whitespace_tokenize(text):
#       chars = list(token)
#       if len(chars) > self.max_input_chars_per_word:
#         output_tokens.append(self.unk_token)
#         continue
#
#       is_bad = False
#       start = 0
#       sub_tokens = []
#       while start < len(chars):
#         end = len(chars)
#         cur_substr = None
#         while start < end:
#           substr = "".join(chars[start:end])
#           if start > 0:
#             substr = "##" + substr
#           if substr in self.vocab:
#             cur_substr = substr
#             break
#           end -= 1
#         if cur_substr is None:
#           is_bad = True
#           break
#         sub_tokens.append(cur_substr)
#         start = end
#
#       if is_bad:
#         output_tokens.append(self.unk_token)
#       else:
#         output_tokens.extend(sub_tokens)
#     return output_tokens
#
#
# def _is_whitespace(char):
#   """Checks whether `chars` is a whitespace character."""
#   # \t, \n, and \r are technically contorl characters but we treat them
#   # as whitespace since they are generally considered as such.
#   if char == " " or char == "\t" or char == "\n" or char == "\r":
#     return True
#   cat = unicodedata.category(char)
#   if cat == "Zs":
#     return True
#   return False
#
#
# def _is_control(char):
#   """Checks whether `chars` is a control character."""
#   # These are technically control characters but we count them as whitespace
#   # characters.
#   if char == "\t" or char == "\n" or char == "\r":
#     return False
#   cat = unicodedata.category(char)
#   if cat.startswith("C"):
#     return True
#   return False
#
#
# def _is_punctuation(char):
#   """Checks whether `chars` is a punctuation character."""
#   cp = ord(char)
#   # We treat all non-letter/number ASCII as punctuation.
#   # Characters such as "^", "$", and "`" are not in the Unicode
#   # Punctuation class but we treat them as punctuation anyways, for
#   # consistency.
#   if ((cp >= 33 and cp <= 47) or (cp >= 58 and cp <= 64) or
#       (cp >= 91 and cp <= 96) or (cp >= 123 and cp <= 126)):
#     return True
#   cat = unicodedata.category(char)
#   if cat.startswith("P"):
#     return True
#   return False

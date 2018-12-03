from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import typing
from typing import Any, List

from rasa_nlu.components import Component
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.tokenizers import Tokenizer, Token
from rasa_nlu.training_data import Message
from rasa_nlu.training_data import TrainingData

if typing.TYPE_CHECKING:
    from spacy.tokens.doc import Doc

# modify by fangning 20181028
import os
import glob

class SpacyTokenizer(Tokenizer, Component):
    name = "tokenizer_spacy"

    provides = ["tokens"]

    requires = ["spacy_doc"]

    # modify by fangning 20181028
    def __init__(self,
                 component_config=None,  # type: Dict[Text, Any]
                 tokenizer=None
                 ):
        # type: (...) -> None
        
        super(SpacyTokenizer, self).__init__(component_config)

        self.tokenizer = tokenizer


    @classmethod
    def create(cls, cfg):
        # type: (RasaNLUModelConfig) -> SpacyTokenizer

        import jieba as tokenizer

        component_conf = cfg.for_component(cls.name, cls.defaults)
        tokenizer = cls.init_jieba(tokenizer, component_conf)
        
        return SpacyTokenizer(component_conf, tokenizer)

    @classmethod
    def load(cls,
             model_dir=None,  # type: Optional[Text]
             model_metadata=None,  # type: Optional[Metadata]
             cached_component=None,  # type: Optional[Component]
             **kwargs  # type: **Any
             ):
        # type: (...) -> JiebaTokenizer
        
        import jieba as tokenizer

        component_meta = model_metadata.for_component(cls.name)
        tokenizer = cls.init_jieba(tokenizer, component_meta)
        
        return SpacyTokenizer(component_meta, tokenizer)

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, RasaNLUModelConfig, **Any) -> None

        for example in training_data.training_examples:
            example.set("tokens", self.tokenize(example.get("spacy_doc")))

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None

        message.set("tokens", self.tokenize(message.get("spacy_doc")))
        print(str(message.get("spacy_doc"))+" | "+str(" ".join([ t.text for t in message.get("tokens")])))

    def tokenize(self, doc):
        # type: (Doc) -> List[Token]
        return [Token(t.text, t.idx) for t in doc ]

    # modify by fangning 20181028
    @classmethod
    def init_jieba(cls, tokenizer, dict_config):
        
        if dict_config.get("default_dict"):
            if os.path.isfile(dict_config.get("default_dict")):
                path_default_dict = glob.glob("{}".format(dict_config.get("default_dict")))
                tokenizer = cls.set_default_dict(tokenizer, path_default_dict[0])
            else:
                print("Because the path of Jieba Default Dictionary has to be a file, not a directory, \
                       so Jieba Default Dictionary hasn't been switched.")
        else:
            print("No Jieba Default Dictionary found")

        if dict_config.get("user_dicts"):
            if os.path.isdir(dict_config.get("user_dicts")):
                parse_pattern = "{}/*"
            else:
                parse_pattern = "{}"

            path_user_dicts = glob.glob(parse_pattern.format(dict_config.get("user_dicts")))    
            tokenizer = cls.set_user_dicts(tokenizer, path_user_dicts)
        else:
            print("No Jieba User Dictionary found")

        return tokenizer


    @staticmethod
    def set_default_dict(tokenizer, path_default_dict):
        print("Setting Jieba Default Dictionary at " + str(path_default_dict))
        tokenizer.set_dictionary(path_default_dict)
        
        return tokenizer


    @staticmethod
    def set_user_dicts(tokenizer, path_user_dicts):
        if len(path_user_dicts) > 0:
            for path_user_dict in path_user_dicts:
                print("Loading Jieba User Dictionary at " + str(path_user_dict))
                tokenizer.load_userdict(path_user_dict)
        else:
            print("No Jieba User Dictionary found")

        return tokenizer


    def persist(self, model_dir):
        # type: (Text) -> Dict[Text, Any]

        return {
            "user_dicts": self.component_config.get("user_dicts"),
            "default_dict": self.component_config.get("default_dict")
        }

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import os
import tempfile
import zipfile
from functools import wraps

import pymysql.cursors
from datetime import datetime
import json

import typing
from builtins import str
from flask import Flask, request, abort, Response, jsonify
from flask_cors import CORS, cross_origin
from gevent.pywsgi import WSGIServer
from typing import Union, Text, Optional

from rasa_core import utils, events, run
from rasa_core.agent import Agent
from rasa_core.channels.direct import CollectingOutputChannel
from rasa_core.tracker_store import TrackerStore
from rasa_core.trackers import DialogueStateTracker
from rasa_core.version import __version__

if typing.TYPE_CHECKING:
    from rasa_core.interpreter import NaturalLanguageInterpreter as NLI

logger = logging.getLogger(__name__)


def create_argument_parser():
    """Parse all the command line arguments for the server script."""

    parser = argparse.ArgumentParser(
            description='starts server to serve an agent')
    parser.add_argument(
            '-d', '--core',
            required=True,
            type=str,
            help="core model to run with the server")
    parser.add_argument(
            '-u', '--nlu',
            type=str,
            help="nlu model to run with the server")
    parser.add_argument(
            '-p', '--port',
            type=int,
            default=50005,
            help="port to run the server at")
    parser.add_argument(
            '--cors',
            nargs='*',
            type=str,
            help="enable CORS for the passed origin. "
                 "Use * to whitelist all origins")
    parser.add_argument(
            '--auth_token',
            type=str,
            help="Enable token based authentication. Requests need to provide "
                 "the token to be accepted.")
    parser.add_argument(
            '-o', '--log_file',
            type=str,
            default="rasa_core.log",
            help="store log file in specified file")
    parser.add_argument(
            '--endpoints',
            default=None,
            help="Configuration file for the connectors as a yml file")

    utils.add_logging_option_arguments(parser)
    return parser


def ensure_loaded_agent(agent):
    """Wraps a request handler ensuring there is a loaded and usable model."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            __agent = agent()
            if not __agent:
                return Response(
                        "No agent loaded. To continue processing, a model "
                        "of a trained agent needs to be loaded.",
                        status=503)

            return f(*args, **kwargs)

        return decorated

    return decorator


def bool_arg(name, default=True):
    # type: ( Text, bool) -> bool
    """Return a passed boolean argument of the request or a default.

    Checks the `name` parameter of the request if it contains a valid
    boolean value. If not, `default` is returned."""

    return request.args.get(name, str(default)).lower() == 'true'


def request_parameters():
    if request.method == 'GET':
        return request.args.to_dict()
    else:

        try:
            return request.get_json(force=True)
        except ValueError as e:
            logger.error("Failed to decode json during respond request. "
                         "Error: {}.".format(e))
            raise


def requires_auth(token=None):
    # type: (Optional[Text]) -> function
    """Wraps a request handler with token authentication."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            provided = request.args.get('token')
            if token is None or provided == token:
                return f(*args, **kwargs)
            abort(401)

        return decorated

    return decorator


def _create_agent(
        model_directory,  # type: Text
        interpreter,  # type: Union[Text,NLI,None]
        action_factory=None,  # type: Optional[Text]
        tracker_store=None,  # type: Optional[TrackerStore]
        generator=None
):
    # type: (...) -> Optional[Agent]
    try:

        return Agent.load(model_directory, interpreter,
                          tracker_store=tracker_store,
                          action_factory=action_factory,
                          generator=generator)
    except Exception as e:
        logger.warn("Failed to load any agent model. Running "
                    "Rasa Core server with out loaded model now. {}"
                    "".format(e))
        return None


def create_app(model_directory,  # type: Text
               interpreter=None,  # type: Union[Text, NLI, None]
               loglevel="INFO",  # type: Optional[Text]
               logfile="rasa_core.log",  # type: Optional[Text]
               cors_origins=None,  # type: Optional[List[Text]]
               action_factory=None,  # type: Optional[Text]
               auth_token=None,  # type: Optional[Text]
               tracker_store=None,  # type: Optional[TrackerStore]
               endpoints=None
               ):
    """Class representing a Rasa Core HTTP server."""

    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    # Setting up logfile
    utils.configure_file_logging(loglevel, logfile)

    if not cors_origins:
        cors_origins = []
    model_directory = model_directory

    nlg_endpoint = utils.read_endpoint_config(endpoints, "nlg")

    nlu_endpoint = utils.read_endpoint_config(endpoints, "nlu")

    tracker_store = tracker_store

    action_factory = action_factory

    _interpreter = run.interpreter_from_args(interpreter, nlu_endpoint)

    # this needs to be an array, so we can modify it in the nested functions...
    _agent = [_create_agent(model_directory, _interpreter,
                            action_factory, tracker_store, nlg_endpoint)]

    def agent():
        if _agent and _agent[0]:
            return _agent[0]
        else:
            return None


    """
    @app.route("/conversations/<sender_id>/respond",
               methods=['GET', 'POST', 'OPTIONS'])
    @cross_origin(origins=cors_origins)
    @requires_auth(auth_token)
    @ensure_loaded_agent(agent)
    def respond(sender_id):
        request_params = request_parameters()

        if 'query' in request_params:
            message = request_params.pop('query')
        elif 'q' in request_params:
            message = request_params.pop('q')
        else:
            return Response(jsonify(error="Invalid respond parameter "
                                          "specified."),
                            status=400,
                            mimetype="application/json")

        try:
            # Set the output channel
            out = CollectingOutputChannel()
            # Fetches the appropriate bot response in a json format
            responses = agent().handle_message(message,
                                               output_channel=out,
                                               sender_id=sender_id)
            return jsonify(responses)

        except Exception as e:
            logger.exception("Caught an exception during respond.")
            return Response(jsonify(error="Server failure. Error: {}"
                                          "".format(e)),
                            status=500,
                            content_type="application/json")
    """

    @app.route("/dlg-app/service/chat/v1/im",
               methods=['GET', 'POST', 'OPTIONS'])
    @cross_origin(origins=cors_origins)
    @requires_auth(auth_token)
    @ensure_loaded_agent(agent)


    def respond():
        global cursor
        global connect
        global list_data

        try:
            request_params = request_parameters()
            if 'partyNo' in request_params:
                partyNo = request_params.pop('partyNo')
                if len(partyNo.strip())==0:
                    logger.exception("partyNo is empty")
                    return jsonify({"resCode":400101,"resMsg":"partyNo is empty","data":""})
                    # return Response(jsonify(error="partyNo is empty"),status=400,mimetype="application/json")
            else:
                logger.exception("partyNo does not exist")
                return jsonify({"resCode":400102,"resMsg":"partyNo [1] does not exist","data":""})
                # return Response(jsonify(error="partyNo [3] does not exist"),status=400,mimetype="application/json")
            
            if 'question' in request_params:
                question = request_params.pop('question')
                if len(question.strip())==0:
                    logger.exception("question is empty")
                    return jsonify({"resCode":400101,"resMsg":"question is empty","data":""})
                    # return Response(jsonify(error="question is empty"),status=400,mimetype="application/json")            
                    
            if 'channel' in request_params:
                channel = request_params.pop('channel')
                if len(channel.strip())==0:
                    logger.exception("channel is empty")
                    return jsonify({"resCode":400101,"resMsg":"channel is empty","data":""})
                    # return Response(jsonify(error="channel is empty" ),status=400,mimetype="application/json") 
            else:
                logger.exception("channel does not exist")
                return jsonify({"resCode":400103,"resMsg":"channel [3] does not exist","data":""})
                # return Response(jsonify(error="channel does not exist" ),status=400,mimetype="application/json")

            appVersion = request_params.pop('appVersion')
            msgId = request_params.pop('msgId')

            # Set the output channel
            out = CollectingOutputChannel()
            # Fetches the appropriate bot response in a json format
            responses = agent().handle_message(question,
                                               output_channel=out,
                                               sender_id=partyNo)

            # print(responses)
            # 0：转人工；1：非人工
            # text= str(dict(list(responses)[0])["text"]).replace('\\','')
            text= str(dict(list(responses)[0])["text"])
            # print(text)

            sql = "INSERT INTO dialogue (msgId, partyNo, question,responses,time_stamp) VALUES ( %s, %s, %s, %s,%s)"
            list_data.append((msgId,partyNo,question,text,str(datetime.now())))
            # print("sql: "+sql)

            # print("len of list_data: "+str(len(list_data)))
            if len(list_data)>=3:
                try:
                    connect.ping()
                except:
                    connect = pymysql.Connect(host='localhost',port=3306,user='test',passwd='12345678',db='test',charset='utf8')
                    cursor = connect.cursor()        
                try:
                    cursor.executemany(sql,list_data)
                    connect.commit()
                    print('成功插入', cursor.rowcount, '条数据')
                    list_data=[]              
                except Exception as e:
                    # print(e.message)
                    connect.rollback()  # 事务回滚
              

            content=''
            link=[]

            # print(content)
            # print(str(link))
            if text.find('answerType')>=0: # xiaoan response
                data_json = {"type":1,"msgType":"XIAOAN", "content":str(text)}
            elif text.find('content')>=0 and text.find('link')>=0: # text and link response
                tmp= eval(text)
                content= tmp["content"]
                tmp2=tmp["link"]
                link= eval(tmp2)
                data_json = {"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":content,"link":link})}
            else: # only text response
                data_json = {"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":text,"link":link})}
            
            
            print(data_json)
            # data_json = {"type":1,"msgType":"LU:CsMsg",
            #     "content":str({"title":"","content":str(dict(list(responses)[0])["text"]),"link":[       
            #         {
            #             "content":"鑫理财的收益？",    # 链接显示的文案
            #             "reply":"鑫理财的收益",       # 用户点击后回复该内容
            #             "echoReply":"Y"                  # Y:用户可以看到自己发送了消息(普通文本消息)；N:发送用户不可见消息(LU:Keyword)。 默认“Y”
            #         },
            #         {
            #             "content":"陆金所理财首页",
            #             "url":"https://pe.lufunds.com/pe/productDetail?productId=154575448"       
            #             #点击后的行为：若存在，交由schema机制处理；若不存在，则把content中的文字当做消息内容发送
            #         },
            #         {
            #             "content":"近一年期的基金600134收益曲线",
            #             "reply":"近一年期的基金600134收益曲线",       # url存在时，忽略reply和echoReply
            #             "url":"lufax://stockhome"
            #         }
            #     ]})}
            
            # data_json = {"type":1,"content":str({title":"","content":str(dict(list(responses)[0])["text"]),"link":[]})}

            # data_json = {"type":0,"content":str({"title":"","content":""})}

            # data_json = {"type":1,"msgType":"RC:ImgTextMsg","content":str({"title":"","content":{"title":"标题","content":"消息描述","imageUri":"http://p1.cdn.com/fds78ruhi.jpg","url":"http://www.rongcloud.cn","extra":""}})}

            # data_json = {"type":1,"msgType":"LU:LucyRecommend","content":str({
            #     "LucyID":"123",                  # 消息ID，埋点用
            #     "title":"给您推荐以下产品",         #获取最后一条消息内容使用，会话不展示
            #     "cardList":[                    # 推荐产品列表
            #        {
            #            "title":"智能宝-聚金",    # 标题
            #            "leftValue":"4.8%",     # 左边第一行
            #            "leftKey":"七日年化",     # 左边第二行
            #            "rightValue":"灵活投资",  # 右边第一行
            #            "rightKey":"投资期限",    # 右边第二行
            #            "note":"期限更短 收益更高", # 底部推荐语
            #            "schema":"lufax://XXXX" # 点击后跳转schema
            #        }
            #     ]
            # })}
            # data_json={}


            return jsonify({"resCode":0,"resMsg":"success","data":data_json})
            # return Response(jsonify(str({"resCode":0,"resMsg":"success","data":data_json})),status=0,content_type="application/json")

            # return jsonify(responses)

        except Exception as e:
            logger.exception("Caught an exception during respond.")
            # return Response(jsonify(error="Server failure. Error: {}" .format(e)),status=500,content_type="application/json")
            return Response(jsonify(error="Server failure. Error: {}"
                                          "".format(e)),
                            status=500,
                            content_type="application/json")


    return app


if __name__ == '__main__':
    # Running as standalone python application
    arg_parser = create_argument_parser()
    cmdline_args = arg_parser.parse_args()

    # Setting up the color scheme of logger
    utils.configure_colored_logging(cmdline_args.loglevel)

    # Setting up the rasa_core application framework
    app = create_app(cmdline_args.core,
                     cmdline_args.nlu,
                     cmdline_args.loglevel,
                     cmdline_args.log_file,
                     cmdline_args.cors,
                     auth_token=cmdline_args.auth_token,
                     endpoints=cmdline_args.endpoints)

    logger.info("Started http server on port %s" % cmdline_args.port)

    # Running the server at 'this' address with the
    # rasa_core application framework
    http_server = WSGIServer(('0.0.0.0', cmdline_args.port), app)
    logger.info("Up and running")

    list_data = list()
    connect = pymysql.Connect(host='localhost',port=3306,user='test',passwd='12345678',db='test',charset='utf8')
    cursor = connect.cursor()

    try:
        http_server.serve_forever()
    except Exception as exc:
        logger.exception(exc)
        
    cursor.close()
    connect.close()
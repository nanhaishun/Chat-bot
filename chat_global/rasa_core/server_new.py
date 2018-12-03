from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import argparse
import logging
import os
import tempfile
import zipfile
from functools import wraps

import pymysql
from DBUtils.PooledDB import PooledDB
from rasa_core.configs.read_config import read_mysql_config

from datetime import datetime
import json
import threading

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

    @app.route("/",
               methods=['GET', 'OPTIONS'])
    @cross_origin(origins=cors_origins)
    def hello():
        """Check if the server is running and responds with the version."""
        return "hello from Rasa Core: " + __version__

    @app.route("/status/health.check",
               methods=['GET', 'OPTIONS'])
    @cross_origin(origins=cors_origins)
    def version():
        """respond with the version number of the installed rasa core."""

        # return jsonify({'version': __version__})
        return "OK:dlg-app:reg_20181121_01"


    @app.route("/dlg-app/service/chat/v1/im",
               methods=['GET', 'POST', 'OPTIONS'])
    @cross_origin(origins=cors_origins)
    @requires_auth(auth_token)
    @ensure_loaded_agent(agent)


    def respond():
        global list_data

        try:
            request_params = request_parameters()
            if 'partyNo' in request_params:
                partyNo = request_params.pop('partyNo')
                if len(partyNo.strip())==0:
                    logger.exception("partyNo is empty")
                    return jsonify({"resCode":400101,"resMsg":"partyNo is empty","data":""})

            else:
                logger.exception("partyNo does not exist")
                return jsonify({"resCode":400102,"resMsg":"partyNo [1] does not exist","data":""})
            
            if 'question' in request_params:
                question = request_params.pop('question')
                if len(question.strip())==0:
                    logger.exception("question is empty")
                    return jsonify({"resCode":0,"resMsg":"question is empty","data":{"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":"question is empty"})}})
                    
            if 'channel' in request_params:
                channel = request_params.pop('channel')
                if len(channel.strip())==0:
                    logger.exception("channel is empty")
                    return jsonify({"resCode":400101,"resMsg":"channel is empty","data":""})
            else:
                logger.exception("channel does not exist")
                return jsonify({"resCode":400103,"resMsg":"channel [3] does not exist","data":""})

            appVersion = request_params.pop('appVersion')

            if 'msgId' in request_params:
                msgId = request_params.pop('msgId')
                if len(msgId.strip())==0:
                    logger.exception("msgId is empty")
                    return jsonify({"resCode":400101,"resMsg":"msgId is empty","data":""})  
            else:
                logger.exception("msgId does not exist")
                return jsonify({"resCode":400103,"resMsg":"msgId does not exist","data":""})   



            # Set the output channel
            out = CollectingOutputChannel()
            # Fetches the appropriate bot response in a json format
            
            try:
                responses = agent().handle_message(question,output_channel=out,sender_id=partyNo)

                # print("response: "+str(responses))

                text = str(responses[0]["text"])

                if text.find("<utter_restart>")>=0:
                    data_json={"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":"restart"})}
                else:
                    content=''
                    link=[]

                    text_new = eval(text)
                    if type(text_new) is list:
                        # print(text_new)
                        data_json = {"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":text_new[0]})}
                    elif type(text_new) is dict:
                        # print(text_new)
                        tuple_tmp = list(text_new.items())[0]
                        if tuple_tmp[0]=='REC':
                            data_json = {"type":1,"msgType":"LU:LucyRecommend","content":tuple_tmp[1]}
                        elif tuple_tmp[0]=='XIAOAN':
                            data_json = {"type":1,"msgType":"XIAOAN", "content":tuple_tmp[1]}
                        elif tuple_tmp[0]=='CONTENT_LINK':
                            tmp= eval(tuple_tmp[1])
                            data_json = {"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":tmp["content"],"link":tmp["link"]})}
                        elif tuple_tmp[0]=='TO_PERSON':
                            data_json = {"type":0,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":tuple_tmp[1]})}
                        else:
                            print("output error format")
                    else:
                        print("output error format")

            except Exception as e:
                logger.exception("Caught an exception of eval(text) is error.")
                data_json={"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":"test1"})}

                
            # try:
            #     print(data_json)
            # except Exception as e:
            #     logger.exception("Caught an exception of data_json is None.")
            #     data_json={"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":"test2"})}


            # sql = "INSERT INTO dialogue (msgId, partyNo, question,responses,time_stamp) VALUES ( %s, %s, %s, %s,%s)"
            sql = "INSERT INTO dialogue (msgId, partyNo, question,responses) VALUES ( %s, %s, %s, %s)"
            # list_data.append((msgId,partyNo,question,text,str(datetime.now())))


            list_data.append((msgId,partyNo,question,str(data_json)))

            # print("sql: "+sql)
            
            if len(list_data)>=10:
                try:
                    connect = pool.connection()  #以后每次需要数据库连接就是用connection（）函数获取连接就好了
                    cursor=connect.cursor()
                    cursor.executemany(sql,list_data)                     
                    connect.commit()
                    print('成功插入', cursor.rowcount, '条数据')
                    list_data=[]  
                except Exception as e:
                    # print(e.message)
                    logger.exception("Caught an exception during insert mysql.")
                    connect.rollback()  # 事务回滚                
                cursor.close()
                connect.close()



            return jsonify({"resCode":0,"resMsg":"success","data":data_json})

        except Exception as e:
            logger.exception("Caught an exception during respond.")
            return jsonify({"resCode":9999,"resMsg":"failure","data":{"type":1,"msgType":"LU:CsMsg", "content":str({ "title":"", "content":"test3"})}})            

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

    # modify wanghuan 20181123

    MYSQL_CONF = read_mysql_config()

    # connect = pymysql.Connect(host='localhost',port=3306,user='test',passwd='12345678',db='test',charset='utf8')
    # cursor = connect.cursor()

    pool = PooledDB(pymysql,10,host=MYSQL_CONF['host'],port=MYSQL_CONF['port'],user=MYSQL_CONF['user'],passwd=MYSQL_CONF['password'],db=MYSQL_CONF['database'],charset='utf8') #10为连接池里的最少连接数


    try:
        http_server.serve_forever()
    except Exception as exc:
        logger.exception(exc)
        
    # cursor.close()
    # connect.close()
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import io
import logging
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor as ProcessPool
from typing import Text, Dict, Any, Optional, List

import six
from builtins import object
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.logger import jsonFileLogObserver, Logger

from rasa_nlu import utils, config
from rasa_nlu.components import ComponentBuilder
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.evaluate import get_evaluation_metrics, clean_intent_labels
from rasa_nlu.model import InvalidProjectError
from rasa_nlu.project import Project, load_from_server
from rasa_nlu.train import do_train_in_worker, TrainingException
from rasa_nlu.training_data import Message
from rasa_nlu.training_data.loading import load_data

logger = logging.getLogger(__name__)

# in some execution environments `reactor.callFromThread`
# can not be called as it will result in a deadlock as
# the `callFromThread` queues the function to be called
# by the reactor which only happens after the call to `yield`.
# Unfortunately, the test is blocked there because `app.flush()`
# needs to be called to allow the fake server to
# respond and change the status of the Deferred on which
# the client is yielding. Solution: during tests we will set
# this Flag to `False` to directly run the calls instead
# of wrapping them in `callFromThread`.
DEFERRED_RUN_IN_REACTOR_THREAD = True


class MaxTrainingError(Exception):
    """Raised when a training is requested and the server has
        reached the max count of training processes.

    Attributes:
        message -- explanation of why the request is invalid
    """

    def __init__(self):
        self.message = 'The server can\'t train more models right now!'

    def __str__(self):
        return self.message


def deferred_from_future(future):
    """Converts a concurrent.futures.Future object to a
       twisted.internet.defer.Deferred object.

    See:
    https://twistedmatrix.com/pipermail/twisted-python/2011-January/023296.html
    """

    d = Deferred()

    def callback(future):
        e = future.exception()
        if e:
            if DEFERRED_RUN_IN_REACTOR_THREAD:
                reactor.callFromThread(d.errback, e)
            else:
                d.errback(e)
        else:
            if DEFERRED_RUN_IN_REACTOR_THREAD:
                reactor.callFromThread(d.callback, future.result())
            else:
                d.callback(future.result())

    future.add_done_callback(callback)
    return d


class DataRouter(object):
    def __init__(self,
                 project_dir=None,
                 max_training_processes=1,
                 response_log=None,
                 emulation_mode=None,
                 remote_storage=None,
                 component_builder=None,
                 model_server=None,
                 wait_time_between_pulls=None):
        self._training_processes = max(max_training_processes, 1)
        self._current_training_processes = 0
        self.responses = self._create_query_logger(response_log)
        self.project_dir = config.make_path_absolute(project_dir)
        self.emulator = self._create_emulator(emulation_mode)
        self.remote_storage = remote_storage
        self.model_server = model_server
        self.wait_time_between_pulls = wait_time_between_pulls

        if component_builder:
            self.component_builder = component_builder
        else:
            self.component_builder = ComponentBuilder(use_cache=True)

        self.project_store = self._create_project_store(project_dir)

        if six.PY3:
            # tensorflow sessions are not fork-safe,
            # and training processes have to be spawned instead of forked.
            # See https://github.com/tensorflow/tensorflow/issues/5448#issuecomment-258934405
            multiprocessing.set_start_method('spawn', force=True)

        self.pool = ProcessPool(self._training_processes)

    def __del__(self):
        """Terminates workers pool processes"""
        self.pool.shutdown()

    @staticmethod
    def _create_query_logger(response_log):
        """Create a logger that will persist incoming query results."""

        # Ensures different log files for different
        # processes in multi worker mode
        if response_log:
            # We need to generate a unique file name,
            # even in multiprocess environments
            timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file_name = "rasa_nlu_log-{}-{}.log".format(timestamp,
                                                            os.getpid())
            response_logfile = os.path.join(response_log, log_file_name)
            # Instantiate a standard python logger,
            # which we are going to use to log requests
            utils.create_dir_for_file(response_logfile)
            out_file = io.open(response_logfile, 'a', encoding='utf8')
            query_logger = Logger(
                    observer=jsonFileLogObserver(out_file, recordSeparator=''),
                    namespace='query-logger')
            # Prevents queries getting logged with parent logger
            # --> might log them to stdout
            logger.info("Logging requests to '{}'.".format(response_logfile))
            return query_logger
        else:
            # If the user didn't provide a logging directory, we wont log!
            logger.info("Logging of requests is disabled. "
                        "(No 'request_log' directory configured)")
            return None

    def _collect_projects(self, project_dir):
        if project_dir and os.path.isdir(project_dir):
            projects = os.listdir(project_dir)
        else:
            projects = []

        projects.extend(self._list_projects_in_cloud())
        return projects

    def _create_project_store(self,
                              project_dir):
        default_project = RasaNLUModelConfig.DEFAULT_PROJECT_NAME

        projects = self._collect_projects(project_dir)

        project_store = {}

        if self.model_server is not None:
            project_store[default_project] = load_from_server(
                    self.component_builder,
                    default_project,
                    self.project_dir,
                    self.remote_storage,
                    self.model_server,
                    self.wait_time_between_pulls
            )
        else:
            for project in projects:
                project_store[project] = Project(self.component_builder,
                                                 project,
                                                 self.project_dir,
                                                 self.remote_storage)

            if not project_store:
                project_store[default_project] = Project(
                        project=default_project,
                        project_dir=self.project_dir,
                        remote_storage=self.remote_storage
                )

        return project_store

    def _pre_load(self, projects):
        logger.debug("loading %s", projects)
        for project in self.project_store:
            if project in projects:
                self.project_store[project].load_model()

    def _list_projects_in_cloud(self):
        try:
            from rasa_nlu.persistor import get_persistor
            p = get_persistor(self.remote_storage)
            if p is not None:
                return p.list_projects()
            else:
                return []
        except Exception:
            logger.exception("Failed to list projects. Make sure you have "
                             "correctly configured your cloud storage "
                             "settings.")
            return []

    @staticmethod
    def _create_emulator(mode):
        """Create emulator for specified mode.

        If no emulator is specified, we will use the Rasa NLU format."""

        if mode is None:
            from rasa_nlu.emulators import NoEmulator
            return NoEmulator()
        elif mode.lower() == 'wit':
            from rasa_nlu.emulators.wit import WitEmulator
            return WitEmulator()
        elif mode.lower() == 'luis':
            from rasa_nlu.emulators.luis import LUISEmulator
            return LUISEmulator()
        elif mode.lower() == 'dialogflow':
            from rasa_nlu.emulators.dialogflow import DialogflowEmulator
            return DialogflowEmulator()
        else:
            raise ValueError("unknown mode : {0}".format(mode))

    @staticmethod
    def _tf_in_pipeline(model_config):
        # type: (RasaNLUModelConfig) -> bool
        from rasa_nlu.classifiers.embedding_intent_classifier import \
            EmbeddingIntentClassifier
        return EmbeddingIntentClassifier.name in model_config.component_names

    def extract(self, data):
        return self.emulator.normalise_request_json(data)

    def parse(self, data):
        project = data.get("project", RasaNLUModelConfig.DEFAULT_PROJECT_NAME)
        model = data.get("model")
        if project not in self.project_store:
            projects = self._list_projects(self.project_dir)

            cloud_provided_projects = self._list_projects_in_cloud()
            projects.extend(cloud_provided_projects)

            if project not in projects:
                raise InvalidProjectError(
                        "No project found with name '{}'.".format(project))
            else:
                try:
                    self.project_store[project] = Project(
                            self.component_builder, project,
                            self.project_dir, self.remote_storage)
                except Exception as e:
                    raise InvalidProjectError(
                            "Unable to load project '{}'. "
                            "Error: {}".format(project, e))

        time = data.get('time')
        response = self.project_store[project].parse(data['text'], time,
                                                     model)

        if self.responses:
            self.responses.info('', user_input=response, project=project,
                                model=response.get('model'))

        return self.format_response(response)

    @staticmethod
    def _list_projects(path):
        """List the projects in the path, ignoring hidden directories."""
        return [os.path.basename(fn)
                for fn in utils.list_subdirectories(path)]

    def parse_training_examples(self, examples, project, model):
        # type: (Optional[List[Message]], Text, Text) -> List[Dict[Text, Text]]
        """Parses a list of training examples to the project interpreter"""

        predictions = []
        for ex in examples:
            logger.debug("Going to parse: {}".format(ex.as_dict()))
            response = self.project_store[project].parse(ex.text,
                                                         None,
                                                         model)
            logger.debug("Received response: {}".format(response))
            predictions.append(response)

        return predictions

    def format_response(self, data):
        return self.emulator.normalise_response_json(data)

    def get_status(self):
        # This will only count the trainings started from this
        # process, if run in multi worker mode, there might
        # be other trainings run in different processes we don't know about.

        return {
            "max_training_processes": self._training_processes,
            "current_training_processes": self._current_training_processes,
            "available_projects": {
                name: project.as_dict()
                for name, project in self.project_store.items()
            }
        }

    def start_train_process(self,
                            data_file,  # type: Text
                            project,  # type: Text
                            train_config,  # type: RasaNLUModelConfig
                            model_name=None  # type: Optional[Text]
                            ):
        # type: (...) -> Deferred
        """Start a model training."""

        if not project:
            raise InvalidProjectError("Missing project name to train")

        if self._training_processes <= self._current_training_processes:
            raise MaxTrainingError

        if project in self.project_store:
            self.project_store[project].status = 1
        elif project not in self.project_store:
            self.project_store[project] = Project(
                    self.component_builder, project,
                    self.project_dir, self.remote_storage)
            self.project_store[project].status = 1

        def training_callback(model_path):
            model_dir = os.path.basename(os.path.normpath(model_path))
            self.project_store[project].update(model_dir)
            self._current_training_processes -= 1
            self.project_store[project].current_training_processes -= 1
            if (self.project_store[project].status == 1 and
                    self.project_store[project].current_training_processes ==
                    0):
                self.project_store[project].status = 0
            return model_dir

        def training_errback(failure):
            logger.warning(failure)
            target_project = self.project_store.get(
                    failure.value.failed_target_project)
            self._current_training_processes -= 1
            self.project_store[project].current_training_processes -= 1
            if (target_project and
                    self.project_store[project].current_training_processes ==
                    0):
                target_project.status = 0
            return failure

        logger.debug("New training queued")

        self._current_training_processes += 1
        self.project_store[project].current_training_processes += 1

        # tensorflow training is not executed in a separate thread on python 2,
        # as this may cause training to freeze
        if six.PY2 and self._tf_in_pipeline(train_config):
            try:
                logger.warning("Training a pipeline with a tensorflow "
                               "component. This blocks the server during "
                               "training.")
                model_path = do_train_in_worker(
                        train_config,
                        data_file,
                        path=self.project_dir,
                        project=project,
                        fixed_model_name=model_name,
                        storage=self.remote_storage)
                model_dir = os.path.basename(os.path.normpath(model_path))
                training_callback(model_dir)
                return model_dir
            except TrainingException as e:
                logger.warning(e)
                target_project = self.project_store.get(
                        e.failed_target_project)
                if target_project:
                    target_project.status = 0
                raise e
        else:
            result = self.pool.submit(do_train_in_worker,
                                      train_config,
                                      data_file,
                                      path=self.project_dir,
                                      project=project,
                                      fixed_model_name=model_name,
                                      storage=self.remote_storage)
            result = deferred_from_future(result)
            result.addCallback(training_callback)
            result.addErrback(training_errback)

            return result

    def evaluate(self, data, project=None, model=None):
        # type: (Text, Optional[Text], Optional[Text]) -> Dict[Text, Any]
        """Perform a model evaluation."""

        project = project or RasaNLUModelConfig.DEFAULT_PROJECT_NAME
        model = model or None
        file_name = utils.create_temporary_file(data, "_training_data")
        test_data = load_data(file_name)

        if project not in self.project_store:
            raise InvalidProjectError("Project {} could not "
                                      "be found".format(project))

        preds_json = self.parse_training_examples(test_data.intent_examples,
                                                  project,
                                                  model)

        predictions = [
            {"text": e.text,
             "intent": e.data.get("intent"),
             "predicted": p.get("intent", {}).get("name"),
             "confidence": p.get("intent", {}).get("confidence")}
            for e, p in zip(test_data.intent_examples, preds_json)
        ]

        y_true = [e.data.get("intent") for e in test_data.intent_examples]
        y_true = clean_intent_labels(y_true)

        y_pred = [p.get("intent", {}).get("name") for p in preds_json]
        y_pred = clean_intent_labels(y_pred)

        report, precision, f1, accuracy = get_evaluation_metrics(y_true,
                                                                 y_pred)

        return {
            "intent_evaluation": {
                "report": report,
                "predictions": predictions,
                "precision": precision,
                "f1_score": f1,
                "accuracy": accuracy}
        }

    def unload_model(self, project, model):
        # type: (Text, Text) -> Dict[Text]
        """Unload a model from server memory."""

        if project is None:
            raise InvalidProjectError("No project specified")
        elif project not in self.project_store:
            raise InvalidProjectError("Project {} could not "
                                      "be found".format(project))

        try:
            unloaded_model = self.project_store[project].unload(model)
            return unloaded_model
        except KeyError:
            raise InvalidProjectError("Failed to unload model {} "
                                      "for project {}.".format(model, project))

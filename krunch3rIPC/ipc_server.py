# ipc.py
# create a single subscriber ipc (unix socket/windows named pipe)

from multiprocessing.connection import Listener
from pathlib import Path
from tempfile import gettempdir
import os
import json

import logging, sys


def _generate_local_logger(env_level=None):
    env_level = os.environ.get("PYTHONDEBUGLEVEL", 0)
    try:
        env_level = int(env_level)
    except:
        env_level = 0

    g_logger = logging.getLogger(__name__)
    _stream_handler = logging.StreamHandler(sys.stderr)
    _formatter = logging.Formatter(
        "\033[1m%(levelname)s\033[0m:%(name)s:%(lineno)d:%(message)s"
    )
    _stream_handler.setFormatter(_formatter)
    g_logger.addHandler(_stream_handler)
    g_logger.setLevel(env_level)

    return g_logger


class IPC_Server(Listener):
    def __init__(
        self,
        parent_pipe_conn,
        exename="filterms",
        ppid=None,
        logger=None,
    ):
        """
        pre: called in process
        in: process pipe back to parent, process name, [ pid of master process ]
        out: n/a
        post: connection_info.json written to temp directory named after process information
        """
        if logger == None:
            self._logger = _generate_local_logger()

        self._parent_pipe_conn = parent_pipe_conn
        if ppid == None:
            self._k_pid = int(os.getpid())
        else:
            self._k_pid = int(ppid)
        self._k_exename = exename
        kTempDirPath = Path(gettempdir())
        self._kConnectionDirRoot = kTempDirPath / str("_" + self._k_exename)
        self._kConnectionDirPath = self._kConnectionDirRoot / str(self._k_pid)
        self._kConnectionInfoFilePath = (
            self._kConnectionDirPath / "connection_info.json"
        )

        self._kConnectionDirPath.mkdir(parents=True, exist_ok=True)
        self._kFamily = "AF_PIPE" if os.name == "nt" else "AF_UNIX"

        self._logger.debug(self._kConnectionInfoFilePath)

        super().__init__(family=self._kFamily)
        self._logger.debug(self.address)

        connectionInfoDict = {"server file": str(self.address)}
        with open(self._kConnectionInfoFilePath, "w") as connectionInfoFileObj:
            connectionInfoFileObj.write(json.dumps(connectionInfoDict))
        self._logger.debug(f"INITIALIZED AND WRITTEN: {self._kConnectionInfoFilePath}")

    def __call__(self):
        """
        pre: called in (sub)process
        in: none
        out: none
        post: none
        check for messages on parent_pipe_conn and broadcast
        """
        conn = None
        while True:
            # wait for one connection (limit one)
            ipc_conn = self.accept()
            self._logger.debug("\nipc.py: accepted connection, waiting on parent pipe")
            while True:
                # wait for next mesg to relay
                msg_to_broadcast = self._parent_pipe_conn.recv()
                dict_msg_to_broadcast = dict()
                if not isinstance(msg_to_broadcast, dict):
                    dict_msg_to_broadcast["signal"] = msg_to_broadcast
                elif "signal" not in dict_msg_to_broadcast:
                    dict_msg_to_broadcast["signal"] = msg_to_broadcast
                dict_msg_to_broadcast["pid"] = self._k_pid
                dict_msg_to_broadcast["exename"] = self._k_exename
                try:
                    # add exename and pid keys to msg
                    ipc_conn.send(json.dumps(dict_msg_to_broadcast))
                except BrokenPipeError:
                    # the pipe to the last client is no longer usable,
                    # client has left. exit loop to accept
                    # the next (new) client connection
                    # the message is lost
                    self._logger.debug(f"\nlost message {msg_to_broadcast}")
                    try:
                        (self._kConnectionInfoFilePath.parent / "lockfile").unlink()
                    except:
                        pass
                    break

    def __del__(self):
        """
        pre: none
        in: n/a
        out: n/a
        post: socket or pipe file deleted along with owning directory, application data
         directory deleted if no other pipes; lockfile removed if present
        """
        self._logger.debug("__del__ IPCServer object")
        self._kConnectionInfoFilePath.unlink()
        self.close()
        try:
            (self._kConnectionInfoFilePath.parent / "lockfile").unlink()
        except:
            pass
        self._kConnectionDirPath.rmdir()
        # try:
        #     self._kConnectionDirRoot.rmdir()
        # except:
        #     pass  # only when all servers have stopped will cleanup complete to root

        self._logger.debug("cleaned up")

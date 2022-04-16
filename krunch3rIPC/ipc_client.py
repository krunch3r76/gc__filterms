# ipc_client.py
# authored by krunch3r76 (https://github.com/krunch3r76)
# license GPL

from pathlib import Path
from tempfile import gettempdir
from time import sleep
import json
from multiprocessing.connection import Client

import multiprocessing.connection
import multiprocessing
import asyncio

import logging
import sys


_logger = None


def _generate_local_logger(env_level=None):
    import logging, sys, os

    if env_level == None:
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


async def _search_for_connection_info_files(kConnectionDataDirPath):
    """identify and return at least one (<pid_dirname>, <connection_info.json>)"""

    """
    PRE: data dir exists
    IN: data dir with subdirectories as pids
    OUT: list of directory as pid name paired with path to json properties file
    POST: NONE
    """

    # TODO check for lock file and ignore on its presence
    connection_info_filepath = None
    pairs = []
    iterdir = kConnectionDataDirPath.iterdir()
    while True:
        try:
            nextDir = next(iterdir)
        except (StopIteration, FileNotFoundError):
            # print(".", end="", flush=True)  # indicates no connections seen in dir
            # sleep(0.5)  # check again
            break
        else:
            # found a process directory, confirm connection info file
            connection_info_filepath_candidate = nextDir / "connection_info.json"
            if connection_info_filepath_candidate.exists():
                if not (nextDir / "lockfile").exists():
                    _logger.debug(
                        f"no lockfile, adding connection {connection_info_filepath_candidate}"
                    )
                    # connection_info_filepath = connection_info_filepath_candidate
                    pairs.append(
                        (
                            nextDir.name,
                            connection_info_filepath_candidate,
                        )
                    )
                else:
                    pass
                    # _logger.debug(f"lockfile seen in {nextDir}, cannot proceed")
            else:
                pass
                # _logger.debug(f"empty pid directory seen {nextDir}")
    return pairs


class _MyClientConnectionInfo:
    def __init__(self, pid, pathobj_to_info):
        self._race = False
        self.pid = int(pid)
        self.pathobj_to_info = pathobj_to_info
        self.pathobj_to_pipe = self._parse_connection_info_for_server_file()

    def lock(self):
        path_to_parent_dir = self.pathobj_to_info.parent
        path_to_lock_file = path_to_parent_dir / "lockfile"
        try:
            with open(path_to_lock_file, mode="x") as lockfile:
                pass
        except FileExistsError:
            _logger.critical(
                f"lock attempt failed, already locked: {path_to_parent_dir}"
            )

    def whether_pipe_exists(self):
        implication = True
        if self.pathobj_to_pipe == None:
            implication = False
        elif not self.pathobj_to_pipe.exists():
            implication = False
        return implication

    def __repr__(self):
        repr2 = "" if self.pathobj_to_pipe == None else str(self.pathobj_to_pipe)
        return str(self.pathobj_to_info) + repr2

    def __hash__(self):
        return hash(self.__repr__())

    def _parse_connection_info_for_server_file(self):
        """
        PRE: NONE
        IN: path to json file that contains the attribute for the path to the server file
        OUT: parsed path to server file or None if connection info file does not exist
        POST: NONE
        """
        connection_filepath = None
        try:
            with open(self.pathobj_to_info, "r") as connection_info_fo:
                props = json.load(connection_info_fo)
                connection_filepath = Path(props["server file"])
        except:
            connection_filepath = None
        finally:
            return connection_filepath


class _MyClientConnection:
    """wrapper around multiprocessing.connection.Client connection"""

    def __init__(self, myClientConnectionInfo):

        """
        PRE: myClientConnectionInfo associated pipe is an existing file
        """
        # private
        self._myClientConnectionInfo = myClientConnectionInfo
        self._myClientConnectionInfo.lock()

        _logger.debug(f"connecting to {self._pathobj_to_pipe}")
        try:
            self._conn = Client(str(self._pathobj_to_pipe))
        except:
            _logger.critical("unhandled exception")
        _logger.debug(f"connected to {self._pathobj_to_pipe}")
        # public
        self.marked_bad = False

    @property
    def _pathobj_to_info(self):
        return self._myClientConnectionInfo.pathobj_to_info

    @property
    def _pathobj_to_pipe(self):
        return self._myClientConnectionInfo.pathobj_to_pipe

    def __repr__(self):
        return str(self._myClientConnectionInfo.pid)
        # return str(self._pathobj_to_info) + str(self._pathobj_to_pipe)

    def __hash__(self):
        return hash(self._myClientConnectionInfo.__repr__())

    def poll(self, timeout=0):
        return self._conn.poll(timeout)

    def send(self, obj_to_pickle):
        return self._conn.send(obj_to_pickle)

    def recv(self):
        return self._conn.recv()

    def fileno(self):
        return self._conn.fileno()


class IPC_Client:
    def __init__(self, exename, pipe_to_parent, logger=None):
        kTempDirPath = Path(gettempdir())
        path_to_datadir = kTempDirPath / str("_" + exename)
        # private
        self._path_to_datadir = path_to_datadir
        self._pipe_to_parent = pipe_to_parent
        self._server_connections = set()
        if logger == None:
            self._logger = _generate_local_logger()
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger = logger

        global _logger
        _logger = self._logger  # global

    async def _update_connections(self):
        """scan datadir and add any new ones to internal set"""
        # print("#", end="", flush=True, file=sys.stderr)
        connection_info_files = await _search_for_connection_info_files(
            self._path_to_datadir
        )
        # print("/#", end="", flush=True, file=sys.stderr)
        # self._logger.info(f"connection_info_files: {connection_info_files}")

        bad_connections = set(filter(lambda c: c.marked_bad, self._server_connections))
        self._server_connections = self._server_connections - bad_connections
        for bad_connection in bad_connections:
            lockfile = (bad_connection._pathobj_to_info).parent / "lockfile"
            try:
                lockfile.unlink()
            except FileNotFoundError:
                pass

        if len(connection_info_files) > 0:
            _logger.debug("considering potentially new connections")
            myClientConnectionInfos = {
                _MyClientConnectionInfo(*info_file)
                for info_file in connection_info_files
            }

            # identify connections without existing target pipe
            disconnected = set(
                filter(lambda m: not m.whether_pipe_exists(), myClientConnectionInfos)
            )
            # remove disconnected from new set
            myClientConnectionInfos = myClientConnectionInfos - disconnected
            # remove disconnected from last set (self._server_connections) redundant?
            self._server_connections = self._server_connections - disconnected
            # remove marked bad from last set
            self._server_connections = self._server_connections - bad_connections
            # union viable with self._server_connections to add any missing
            for m in myClientConnectionInfos:
                if hash(m) not in [hash(c) for c in self._server_connections]:
                    self._server_connections.add(
                        _MyClientConnection(myClientConnectionInfo=m)
                    )
                    _logger.debug(f"added connection {m}")
            # self._logger.info(f"myClientConnectionInfos: {myClientConnectionInfos}")

            # filter connection_info_files which do not have a corresponding entry in self set

    async def _poll_connections(self):
        """wait on all connections and relay signals over process pipe"""
        try:
            # print("!", end="", flush=True, file=sys.stderr)
            ready_ = multiprocessing.connection.wait(
                self._server_connections, timeout=0
            )
        except ValueError:
            self._logger.debug("ValueError")
            return  # refreshing needed
        ready = ready_
        # ready = list(filter(lambda r: not r.marked_bad, ready_))
        # print(f"?{len(ready)}", end="", flush=True, file=sys.stderr)
        if len(ready) > 0:
            for p in ready:
                try:
                    _logger.debug("about to receive")
                    received = p.recv()
                    print(received, flush=True)
                except EOFError:
                    self._logger.debug(f"EOFError: {p}")
                    p.marked_bad = True
                except ConnectionResetError:
                    self._logger.debug("ConnectionResetError")
                    p.marked_bad = True

    async def __async_call__(self):
        while True:
            pass
            # print(".", flush=True, end="")
            # order is important here, poll before updating/marking bad
            await self._poll_connections()
            await self._update_connections()
            await asyncio.sleep(0.1)

    def __call__(self):

        """maintain and handle connections"""

        """
        PRE: called in a process
        IN: NONE
        OUT: NONE
        POST: NONE
        """
        asyncio.run(self.__async_call__())

    def __del__(self):
        for server_connection in self._server_connections:
            lockfile = (server_connection._pathobj_to_info).parent / "lockfile"
            try:
                lockfile.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    parent_pipe, child_pipe = multiprocessing.Pipe(duplex=False)

    ipc_client = IPC_Client("filterms", parent_pipe)
    process = multiprocessing.Process(target=ipc_client, daemon=True)
    process.start()

    input("process invoking ipc_client has started, enter to proceed\n")

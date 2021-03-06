# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Functionality related to running the game in server-mode."""
from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING

from efro.terminal import Clr
from ba._enums import TimeType
from ba._freeforallsession import FreeForAllSession
from ba._dualteamsession import DualTeamSession
from bacommon.servermanager import (ServerCommand, StartServerModeCommand,
                                    ShutdownCommand, ShutdownReason)
import _ba

if TYPE_CHECKING:
    from typing import Optional, Dict, Any, Type
    import ba
    from bacommon.servermanager import ServerConfig


def _cmd(command_data: bytes) -> None:
    """Handle commands coming in from our server manager parent process."""
    import pickle
    command = pickle.loads(command_data)
    assert isinstance(command, ServerCommand)

    if isinstance(command, StartServerModeCommand):
        assert _ba.app.server is None
        _ba.app.server = ServerController(command.config)
        return

    if isinstance(command, ShutdownCommand):
        assert _ba.app.server is not None
        _ba.app.server.shutdown(reason=command.reason,
                                immediate=command.immediate)
        return

    print(f'{Clr.SRED}ERROR: server process'
          f' got unknown command: {type(command)}{Clr.RST}')


class ServerController:
    """Overall controller for the app in server mode.

    Category: App Classes
    """

    def __init__(self, config: ServerConfig) -> None:

        self._config = config
        self._playlist_name = '__default__'
        self._ran_access_check = False
        self._prep_timer: Optional[ba.Timer] = None
        self._next_stuck_login_warn_time = time.time() + 10.0
        self._first_run = True
        self._shutdown_reason: Optional[ShutdownReason] = None
        self._executing_shutdown = False

        # Make note if they want us to import a playlist;
        # we'll need to do that first if so.
        self._playlist_fetch_running = self._config.playlist_code is not None
        self._playlist_fetch_sent_request = False
        self._playlist_fetch_got_response = False
        self._playlist_fetch_code = -1

        # Now sit around doing any pre-launch prep such as waiting for
        # account sign-in or fetching playlists; this will kick off the
        # session once done.
        with _ba.Context('ui'):
            self._prep_timer = _ba.Timer(0.25,
                                         self._prepare_to_serve,
                                         timetype=TimeType.REAL,
                                         repeat=True)

    def shutdown(self, reason: ShutdownReason, immediate: bool) -> None:
        """Set the app to quit either now or at the next clean opportunity."""
        self._shutdown_reason = reason
        if immediate:
            print(f'{Clr.SBLU}Immediate shutdown initiated.{Clr.RST}')
            self._execute_shutdown()
        else:
            print(f'{Clr.SBLU}Shutdown initiated;'
                  f' server process will exit at the next clean opportunity.'
                  f'{Clr.RST}')

    def handle_transition(self) -> bool:
        """Handle transitioning to a new ba.Session or quitting the app.

        Will be called once at the end of an activity that is marked as
        a good 'end-point' (such as a final score screen).
        Should return True if action will be handled by us; False if the
        session should just continue on it's merry way.
        """
        if self._shutdown_reason is not None:
            self._execute_shutdown()
            return True
        return False

    def _execute_shutdown(self) -> None:
        from ba._lang import Lstr
        if self._executing_shutdown:
            return
        self._executing_shutdown = True
        timestrval = time.strftime('%c')
        if self._shutdown_reason is ShutdownReason.RESTARTING:
            # FIXME: Should add a server-screen-message call.
            # (so we could send this an an Lstr)
            _ba.chat_message(
                Lstr(resource='internal.serverRestartingText').evaluate())
            print(f'{Clr.SBLU}Exiting for server-restart'
                  f' at {timestrval}{Clr.RST}')
        else:
            # FIXME: Should add a server-screen-message call.
            # (so we could send this an an Lstr)
            print(f'{Clr.SBLU}Exiting for server-shutdown'
                  f' at {timestrval}{Clr.RST}')
            _ba.chat_message(
                Lstr(resource='internal.serverShuttingDownText').evaluate())
        with _ba.Context('ui'):
            _ba.timer(2.0, _ba.quit, timetype=TimeType.REAL)

    def _run_access_check(self) -> None:
        """Check with the master server to see if we're likely joinable."""
        from ba._netutils import serverget
        serverget(
            'bsAccessCheck',
            {
                'port': _ba.get_game_port(),
                'b': _ba.app.build_number
            },
            callback=self._access_check_response,
        )

    def _access_check_response(self, data: Optional[Dict[str, Any]]) -> None:
        gameport = _ba.get_game_port()
        if data is None:
            print('error on UDP port access check (internet down?)')
        else:
            if data['accessible']:
                print(f'{Clr.SBLU}UDP port {gameport} access check successful.'
                      f' Your server appears to be joinable from the'
                      f' internet.{Clr.RST}')
            else:
                print(f'{Clr.SRED}UDP port {gameport} access check failed.'
                      f' Your server does not appear to be joinable'
                      f' from the internet.{Clr.RST}')

    def _prepare_to_serve(self) -> None:
        signed_in = _ba.get_account_state() == 'signed_in'
        if not signed_in:

            # Signing in to the local server account should not take long;
            # complain if it does...
            curtime = time.time()
            if curtime > self._next_stuck_login_warn_time:
                print('Still waiting for account sign-in...')
                self._next_stuck_login_warn_time = curtime + 10.0
            return

        can_launch = False

        # If we're fetching a playlist, we need to do that first.
        if not self._playlist_fetch_running:
            can_launch = True
        else:
            if not self._playlist_fetch_sent_request:
                print(f'{Clr.SBLU}Requesting shared-playlist'
                      f' {self._config.playlist_code}...{Clr.RST}')
                _ba.add_transaction(
                    {
                        'type': 'IMPORT_PLAYLIST',
                        'code': str(self._config.playlist_code),
                        'overwrite': True
                    },
                    callback=self._on_playlist_fetch_response)
                _ba.run_transactions()
                self._playlist_fetch_sent_request = True

            if self._playlist_fetch_got_response:
                self._playlist_fetch_running = False
                can_launch = True

        if can_launch:
            self._prep_timer = None
            _ba.pushcall(self._launch_server_session)

    def _on_playlist_fetch_response(
        self,
        result: Optional[Dict[str, Any]],
    ) -> None:
        if result is None:
            print('Error fetching playlist; aborting.')
            sys.exit(-1)

        # Once we get here, simply modify our config to use this playlist.
        typename = (
            'teams' if result['playlistType'] == 'Team Tournament' else
            'ffa' if result['playlistType'] == 'Free-for-All' else '??')
        plistname = result['playlistName']
        print(f'{Clr.SBLU}Got playlist: "{plistname}" ({typename}).{Clr.RST}')
        self._playlist_fetch_got_response = True
        self._config.session_type = typename
        self._playlist_name = (result['playlistName'])

    def _get_session_type(self) -> Type[ba.Session]:
        # Convert string session type to the class.
        # Hmm should we just keep this as a string?
        if self._config.session_type == 'ffa':
            return FreeForAllSession
        if self._config.session_type == 'teams':
            return DualTeamSession
        raise RuntimeError(
            f'Invalid session_type: "{self._config.session_type}"')

    def _launch_server_session(self) -> None:
        """Kick off a host-session based on the current server config."""
        app = _ba.app
        appcfg = app.config
        sessiontype = self._get_session_type()

        if _ba.get_account_state() != 'signed_in':
            print('WARNING: launch_server_session() expects to run '
                  'with a signed in server account')

        if self._first_run:
            curtimestr = time.strftime('%c')
            print(f'{Clr.SBLU}BallisticaCore {app.version}'
                  f' ({app.build_number})'
                  f' entering server-mode {curtimestr}{Clr.RST}')

        if sessiontype is FreeForAllSession:
            appcfg['Free-for-All Playlist Selection'] = self._playlist_name
            appcfg['Free-for-All Playlist Randomize'] = (
                self._config.playlist_shuffle)
        elif sessiontype is DualTeamSession:
            appcfg['Team Tournament Playlist Selection'] = self._playlist_name
            appcfg['Team Tournament Playlist Randomize'] = (
                self._config.playlist_shuffle)
        else:
            raise RuntimeError(f'Unknown session type {sessiontype}')

        app.teams_series_length = self._config.teams_series_length
        app.ffa_series_length = self._config.ffa_series_length

        # Call set-enabled last (will push state to the cloud).
        _ba.set_public_party_max_size(self._config.max_party_size)
        _ba.set_public_party_name(self._config.party_name)
        _ba.set_public_party_stats_url(self._config.stats_url)
        _ba.set_public_party_enabled(self._config.party_is_public)

        # And here we go.
        _ba.new_host_session(sessiontype)

        if not self._ran_access_check:
            self._run_access_check()
            self._ran_access_check = True

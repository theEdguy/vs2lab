import random
import logging

import stablelog

# coordinator messages
from const3PC import VOTE_REQUEST, PREPARE_COMMIT, GLOBAL_COMMIT, GLOBAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT
# misc constants
from const3PC import TIMEOUT


class Coordinator:
    """
    Implements a three phase commit coordinator.
    """

    def __init__(self, chan):
        self.channel = chan
        self.coordinator = self.channel.join('coordinator')
        self.participants = []
        self.stable_log = stablelog.create_log("coordinator-" + self.coordinator)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Coordinator")
        self.state = None

    def _enter_state(self, state):
        self.stable_log.info(state)
        self.logger.info(f"Coordinator {self.coordinator} entered state {state}.")
        self.state = state

    def init(self):
        self.channel.bind(self.coordinator)
        self._enter_state('INIT')
        self.participants = self.channel.subgroup('participant')

    def run(self):
        if random.random() > 3/3:  # simulate a crash
            return "Coordinator crashed in state INIT."
        # Phase 1a: send vote request
        self._enter_state('WAIT')
        self.channel.send_to(self.participants, VOTE_REQUEST)
        if random.random() > 0/3:  # simulate a crash
            return "Coordinator crashed in state WAIT."

        # Phase 1b/2a: collect votes
        yet_to_receive = list(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)

            if not msg or msg[1] == VOTE_ABORT:
                reason = "timeout" if not msg else f"VOTE_ABORT from {msg[0]}"
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return f"Coordinator {self.coordinator} terminated in ABORT. Reason: {reason}."

            else:
                assert msg[1] == VOTE_COMMIT
                yet_to_receive.remove(msg[0])

        # Phase 2a/3a: send PRECOMMIT
        self._enter_state('PRECOMMIT')
        self.channel.send_to(self.participants, PREPARE_COMMIT)
        if random.random() > 0/3:  # simulate a crash
            return "Coordinator crashed in state PRECOMMIT."

        # Phase 3a: wait for READY_COMMIT responses
        yet_to_receive = list(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)
            if not msg:  # timeout -> treat as abort
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return f"Coordinator {self.coordinator} terminated in ABORT due to timeout in PRECOMMIT."
            else:
                # For simplicity, assume READY_COMMIT = VOTE_COMMIT
                yet_to_receive.remove(msg[0])

        # Phase 3a: all READY_COMMIT received -> GLOBAL_COMMIT
        self._enter_state('COMMIT')
        self.channel.send_to(self.participants, GLOBAL_COMMIT)
        return f"Coordinator {self.coordinator} terminated in COMMIT."
import random
import logging

# coordinator messages
from const3PC import VOTE_REQUEST, PREPARE_COMMIT, GLOBAL_COMMIT, GLOBAL_ABORT
# participant decisions
from const3PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, READY_COMMIT, NEED_DECISION
# misc constants
from const3PC import TIMEOUT

import stablelog


class Participant:
    """
    Implements a three phase commit participant with termination protocol
    after coordinator crash.
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log("participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state = 'NEW'

    @staticmethod
    def _do_work():
        # random decision: LOCAL_ABORT ~1/3, LOCAL_SUCCESS ~2/3
        return LOCAL_ABORT if random.random() > 3/3 else LOCAL_SUCCESS

    def _enter_state(self, state):
        self.stable_log.info(state)
        self.logger.info(f"Participant {self.participant} entered state {state}.")
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')

    def run(self):
        # wait for vote request from coordinator
        final_decision = None
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:
            # Coordinator crashed before vote request -> abort
            self._enter_state('ABORT')
            return f"Participant {self.participant} terminated in ABORT due to LOCAL_ABORT."

        assert msg[1] == VOTE_REQUEST
        decision = self._do_work()

        if decision == LOCAL_ABORT:
            self._enter_state('ABORT')
            self.channel.send_to(self.coordinator, VOTE_ABORT)
            return f"Participant {self.participant} terminated in ABORT due to LOCAL_ABORT."

        # Local SUCCESS -> READY
        self._enter_state('READY')
        self.channel.send_to(self.coordinator, VOTE_COMMIT)

        # wait for PREPARE_COMMIT or GLOBAL_ABORT
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        if not msg:
            # Coordinator crashed: begin termination protocol
            # Step 1: Determine new coordinator (lowest ID)
            new_coordinator = min(map(int, self.all_participants))
            # Step 2: New coordinator announces its state to all
            if self.participant == new_coordinator:
                # Map Participant-State auf Koordinator-State für Termination
                if self.state in ['INIT', 'READY']:
                    pk_state = 'WAIT'        # Fall 1: Teilnehmer noch nicht PRECOMMIT oder COMMIT
                elif self.state == 'PRECOMMIT':
                    pk_state = 'PRECOMMIT'   # Fall 2: Teilnehmer war bereit zum Commit
                elif self.state == 'COMMIT':
                    pk_state = 'COMMIT'      # Fall 3: bereits COMMIT
                else:
                    pk_state = 'ABORT'        # Fallback: alles andere (inklusive ABORT) → ABORT

                # Ankündigung des States an alle Teilnehmer
                self.channel.send_to(self.all_participants, pk_state)
                print(f"P_k (new coordinator) is {self.participant} with mapped state {pk_state}")

                # Final decision basierend auf pk_state
                if pk_state == 'WAIT':
                    final_state = 'ABORT'
                    final_decision = GLOBAL_ABORT
                elif pk_state == 'PRECOMMIT':
                    final_state = 'COMMIT'
                    final_decision = GLOBAL_COMMIT
                else:  # COMMIT oder ABORT
                    final_state = pk_state
                    final_decision = GLOBAL_COMMIT if pk_state == 'COMMIT' else GLOBAL_ABORT

                # Entscheidung an alle senden
                self.channel.send_to(self.all_participants, final_decision)
                self._enter_state(final_state)

            else:
                    # I am not the new coordinator: wait for state announcement
                    msg = self.channel.receive_from(self.all_participants, TIMEOUT)
                    if msg:
                        pk_state = msg[1]
                        # Adjust own state if behind
                        state_order = ['INIT', 'READY', 'PRECOMMIT', 'COMMIT', 'ABORT']
                        if state_order.index(self.state) < state_order.index(pk_state):
                            self._enter_state(pk_state)

                    # wait for final decision from new coordinator
                    msg = self.channel.receive_from(self.all_participants, TIMEOUT)
                    if msg and msg[1] in [GLOBAL_COMMIT, GLOBAL_ABORT]:
                        final_decision = msg[1]
                        self._enter_state('COMMIT' if final_decision == GLOBAL_COMMIT else 'ABORT')

                    return f"Participant {self.participant} terminated in state {self.state} due to {final_decision}."
        # normal path
        decision = msg[1]
        final_decision = decision
        if decision == GLOBAL_ABORT:
            self._enter_state('ABORT')
        elif decision == PREPARE_COMMIT:
            self._enter_state('PRECOMMIT')
            self.channel.send_to(self.coordinator, READY_COMMIT)
            msg = self.channel.receive_from(self.coordinator, TIMEOUT)
            if msg and msg[1] == GLOBAL_COMMIT:
                self._enter_state('COMMIT')
            else:
                self._enter_state('ABORT')
                decision = 'PREPARE_COMMIT timeout'
        elif decision == GLOBAL_COMMIT:
            self._enter_state('COMMIT')
        else:
            self._enter_state('ABORT')
            decision = 'unknown decision'

        # respond to NEED_DECISION messages
        for p in self.all_participants:
            if p != self.participant:
                msg = self.channel.receive_from({p}, TIMEOUT)
                if msg and msg[1] == NEED_DECISION:
                    self.channel.send_to({msg[0]}, decision)

        return f"Participant {self.participant} terminated in state {self.state} due to {decision}."
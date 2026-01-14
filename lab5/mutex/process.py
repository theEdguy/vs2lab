import logging
import random
import time

from constMutex import ENTER, RELEASE, ALLOW, ACTIVE, PASSIVE

HEARTBEAT = 'HEARTBEAT'


class Process:
    """
    Distributed mutual exclusion with crash detection via heartbeats.
    """

    HEARTBEAT_INTERVAL = 1.0      # seconds
    CRASH_TIMEOUT = 5.0           # seconds

    def __init__(self, chan):
        self.channel = chan
        self.process_id = self.channel.join('proc')

        self.all_processes = []
        self.other_processes = []

        self.queue = []
        self.clock = 0

        self.peer_name = 'unassigned'
        self.peer_type = 'unassigned'

        # crash detection
        self.last_seen = {}
        self.last_heartbeat_sent = 0.0

        self.logger = logging.getLogger(
            "vs2lab.lab5.mutex.process.Process")

    def __mapid(self, pid=None):
        if pid is None:
            pid = self.process_id
        return f"Proc-{pid}"

    # ---------------- MUTEX ---------------- #

    def __cleanup_queue(self):
        self.queue.sort()
        while self.queue and self.queue[0][2] == ALLOW:
            self.queue.pop(0)

    def __request_to_enter(self):
        self.clock += 1
        msg = (self.clock, self.process_id, ENTER)
        self.queue.append(msg)
        self.__cleanup_queue()
        self.channel.send_to(self.other_processes, msg)

    def __allow_to_enter(self, requester):
        self.clock += 1
        msg = (self.clock, self.process_id, ALLOW)
        self.channel.send_to([requester], msg)

    def __release(self):
        assert self.queue and self.queue[0][1] == self.process_id
        self.queue = [m for m in self.queue[1:] if m[2] == ENTER]

        self.clock += 1
        msg = (self.clock, self.process_id, RELEASE)
        self.channel.send_to(self.other_processes, msg)

    def __allowed_to_enter(self):
        if not self.queue:
            return False

        first = self.queue[0][1] == self.process_id
        responders = {m[1] for m in self.queue[1:]}
        return first and len(responders) == len(self.other_processes)

    # ---------------- FAILURE DETECTION ---------------- #

    def __send_heartbeat(self):
        now = time.time()
        if now - self.last_heartbeat_sent >= self.HEARTBEAT_INTERVAL:
            self.clock += 1
            hb = (self.clock, self.process_id, HEARTBEAT)
            self.channel.send_to(self.other_processes, hb)
            self.last_heartbeat_sent = now

    def __detect_crashes(self):
        now = time.time()
        crashed = []

        for pid in list(self.other_processes):
            last = self.last_seen.get(pid, 0)
            if now - last > self.CRASH_TIMEOUT:
                crashed.append(pid)

        for pid in crashed:
            self.logger.warning(
                f"{self.__mapid()} detects crashed process {self.__mapid(pid)}"
            )
            self.other_processes.remove(pid)
            self.all_processes.remove(pid)
            self.last_seen.pop(pid, None)
            new_queue = []
            for m in self.queue:
                if m[1] != pid:       # Nur Nachrichten von lebenden Prozessen behalten
                    new_queue.append(m)
                else:
                    print(f"Removing message from crashed process {self.__mapid(pid)}: {m}")
                    # oder alternativ: self.logger.info(f"Removing message from crashed process {self.__mapid(pid)}: {m}")
            self.queue = new_queue

        if crashed:
            self.__cleanup_queue()

    # ---------------- COMMUNICATION ---------------- #

    def __receive(self):
        if not self.other_processes:
            time.sleep(0.1)
            return False

        received = self.channel.receive_from(self.other_processes, 1)
        if not received:
            return False

        msg = received[1]
        sender = msg[1]

        self.clock = max(self.clock, msg[0]) + 1
        self.last_seen[sender] = time.time()

        if msg[2] == ENTER:
            self.queue.append(msg)
            self.__allow_to_enter(sender)

        elif msg[2] == ALLOW:
            self.queue.append(msg)

        elif msg[2] == RELEASE:
            if self.queue and self.queue[0][1] == sender:
                self.queue.pop(0)

        elif msg[2] == HEARTBEAT:
            pass

        self.__cleanup_queue()
        return True

    # ---------------- INIT / RUN ---------------- #

    def init(self, peer_name, peer_type):
        self.channel.bind(self.process_id)

        self.all_processes = list(self.channel.subgroup('proc'))
        self.other_processes = [
            p for p in self.all_processes if p != self.process_id
        ]

        now = time.time()
        for p in self.other_processes:
            self.last_seen[p] = now

        self.peer_name = peer_name
        self.peer_type = peer_type

        self.logger.info(
            f"{peer_name} joined channel as {self.__mapid()}")

    def run(self):
        while True:
            self.__send_heartbeat()
            self.__detect_crashes()

            if (self.peer_type == ACTIVE and
                    len(self.all_processes) > 1 and
                    random.choice([True, False])):

                self.__request_to_enter()

                while not self.__allowed_to_enter():
                    self.__receive()
                    self.__detect_crashes()
                    self.__send_heartbeat()

                print(f" CS <- {self.__mapid()}")
                time.sleep(random.randint(0, 2000) / 1000)
                print(f" CS -> {self.__mapid()}")
                self.__release()

            else:
                self.__receive()
                time.sleep(0.05)
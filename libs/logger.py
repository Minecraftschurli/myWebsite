import re

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


class Logger(object):
    def __init__(self, _in):
        self.terminal = _in
        self.log = open("log.txt", "a")

    def write(self, message):
        self.terminal.write(message)
        if '/admin/console' not in message:
            self.log.write(ansi_escape.sub('', message))

    def flush(self):
        self.terminal.flush()
        self.log.flush()
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass

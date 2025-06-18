import io
import logging
import re

from agent_gateway.tools.utils import parse_log_message


class StreamlitLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_buffer = io.StringIO()
        self.ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    def emit(self, record):
        msg = self.format(record)
        clean_msg = self.ansi_escape.sub("", msg)
        self.log_buffer.write(clean_msg + "\n")

    def get_logs(self):
        return self.log_buffer.getvalue()

    def process_logs(self):
        raw_logs = self.get_logs()
        lines = raw_logs.strip().split("\n")
        log_output = [parse_log_message(line.strip()) for line in lines if line.strip()]
        cleaned_output = [line for line in log_output if line is not None]
        all_logs = "\n".join(cleaned_output)
        return all_logs

    def clear_logs(self):
        self.log_buffer = io.StringIO()


def setup_logging():
    root_logger = logging.getLogger()
    handler = StreamlitLogHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return handler

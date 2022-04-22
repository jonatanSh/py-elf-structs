from io import StringIO
import logging
import traceback


def log_traceback():
    traceback_file = StringIO()
    traceback.print_exc(file=traceback_file)
    traceback_file.seek(0)
    logging.info(str(traceback_file.read()))

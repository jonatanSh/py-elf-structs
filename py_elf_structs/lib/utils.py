from io import StringIO, BytesIO
import logging
import traceback
import sys
IS_PYTHON_3 = int(sys.version[0]) > 2


def log_traceback():
    if IS_PYTHON_3:
        traceback_file = StringIO()
    else:
        traceback_file = BytesIO()
    traceback.print_exc(file=traceback_file)
    traceback_file.seek(0)
    logging.info(str(traceback_file.read()))

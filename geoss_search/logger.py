import sys
import traceback
from itertools import chain
import logging

APP_NAME = 'geoss_search'

def exception_as_rfc5424_structured_data(ex: Exception) -> dict:
    """Transform a Python exception into RFC5424 compliant structured data

    Args:
        ex (Exception): A Python exception

    Returns:
        dict: Structured data dictionary
    """
    tb = traceback.format_exception(*sys.exc_info())
    
    return {
        'structured_data': {
            'mdc': {
                'exception-message': str(ex),
                'exception': '|'.join(chain.from_iterable((s.splitlines() for s in tb[1:]))),
            }
        }
    }

class Rfc5424ContextFilter(logging.Filter):
    """A filter injecting diagnostic context suitable for RFC5424 messages"""
    
    def filter(self, record):
        record.msgid = APP_NAME
        if not hasattr(record, 'structured_data'):
            record.structured_data = {'mdc': {}}
        mdc = record.structured_data.get('mdc') 
        if mdc is None:
            mdc = record.structured_data['mdc'] = {}
        mdc.update({
            'logger': record.name,
            'thread': record.threadName
        })
        return True

mainLogger = logging.getLogger(APP_NAME)
mainLogger.addFilter(Rfc5424ContextFilter())

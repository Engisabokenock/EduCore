import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'level': record.levelname,
            'time': self.formatTime(record, '%Y-%m-%dT%H:%M:%S.%fZ'),
            'name': record.name,
            'message': record.getMessage(),
        }
        extra = getattr(record, 'request_log', None)
        if extra:
            log_data.update(extra)
        return json.dumps(log_data)

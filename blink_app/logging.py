
import logging

log = logging.getLogger(__name__)

logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-10.10s] [%(levelname)s]  %(message)s"
)

log.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('runtime.log')
console_handler = logging.StreamHandler()

file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logFormatter)

console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logFormatter)

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)

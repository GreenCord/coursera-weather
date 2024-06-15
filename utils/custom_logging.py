import boto3
import logging
import matplotlib
from simple_chalk import chalk

class Logger(logging.getLoggerClass()):
    
    def __init__(self, caller=__name__):
        self.logLevel = logging.DEBUG
        logging.basicConfig(format=chalk.whiteBright(" %(levelname)-8s") + chalk.white(" [ ") + chalk.whiteBright("%(name)-11s") + chalk.white(" ] ") + "%(message)s", level=self.logLevel, force=True)
        matplotlib.set_loglevel(level = "info")
        boto3.set_stream_logger('boto3', logging.INFO)
        boto3.set_stream_logger('botocore', logging.INFO)
        boto3.set_stream_logger('botocore.tokens', logging.CRITICAL)
        boto3.set_stream_logger('urllib3.connectionpool', logging.INFO)

        
        self.l = logging.getLogger(caller)
        self.caller = chalk.whiteBright(f"{caller}")
        self.sep = " :: "
        self.l.info(chalk.blue(f"Logger initialized for {caller}."))
    
    def critical(self, msg, symbolType="INFO"):
        self.l.critical(chalk.red(msg))

    def debug(self, msg, symbolType="DEBUG"):
        self.l.debug(chalk.green(msg))

    def error(self, msg, symbolType="INFO"):
        self.l.error(chalk.red(msg))
    
    def info(self, msg):
        self.l.info(chalk.white(msg))

    def log(self, msg):
        self.l.info(chalk.white("LOG") + chalk.whiteBright(msg))

    def warn(self, msg, symbolType="WARNING"):
        self.l.warning(chalk.yellow(msg))
        

import structlog
log = structlog.get_logger()
log.info("event-a")
log.info("event-b", _replace_msg="B")
log.debug("ignored-debug", _replace_msg="dbg")

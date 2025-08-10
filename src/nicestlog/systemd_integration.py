"""
Advanced systemd integration for nicestlog.

Makes systemd logging actually usable and powerful.
"""
import os
import sys
import socket
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

try:
    from systemd import journal
    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False
    journal = None


class SystemdJournalHandler:
    """
    Advanced systemd journal handler with proper field mapping and priorities.
    """
    
    # Map Python log levels to systemd priorities
    PRIORITY_MAP = {
        'critical': journal.LOG_CRIT if SYSTEMD_AVAILABLE else 2,
        'error': journal.LOG_ERR if SYSTEMD_AVAILABLE else 3,
        'warning': journal.LOG_WARNING if SYSTEMD_AVAILABLE else 4,
        'info': journal.LOG_INFO if SYSTEMD_AVAILABLE else 6,
        'debug': journal.LOG_DEBUG if SYSTEMD_AVAILABLE else 7,
        'trace': journal.LOG_DEBUG if SYSTEMD_AVAILABLE else 7,
    }
    
    def __init__(self, identifier: str = None, facility: str = None):
        """
        Initialize systemd journal handler.
        
        Args:
            identifier: SYSLOG_IDENTIFIER for journal entries
            facility: SYSLOG_FACILITY (e.g., 'daemon', 'user', 'local0')
        """
        self.identifier = identifier or "nicestlog"
        self.facility = facility
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        
        if not SYSTEMD_AVAILABLE:
            print("Warning: systemd-python not available. Install with: pip install systemd-python", 
                  file=sys.stderr)
    
    def __call__(self, _, __, event_dict):
        """Process log event and send to systemd journal."""
        if not SYSTEMD_AVAILABLE:
            return event_dict
        
        # Extract standard fields
        message = event_dict.get('event', '')
        level = event_dict.get('level', 'info')
        logger_name = event_dict.get('logger', 'root')
        timestamp = event_dict.get('timestamp')
        
        # Build journal fields (systemd uses uppercase field names)
        journal_fields = {
            'MESSAGE': str(message),
            'PRIORITY': self.PRIORITY_MAP.get(level, journal.LOG_INFO),
            'SYSLOG_IDENTIFIER': self.identifier,
            'LOGGER_NAME': logger_name,
            'PYTHON_MODULE': logger_name,
            'SYSLOG_PID': str(self.pid),
            '_HOSTNAME': self.hostname,
            '_PID': str(self.pid),
        }
        
        # Add facility if specified
        if self.facility:
            journal_fields['SYSLOG_FACILITY'] = self.facility
        
        # Add custom fields from event_dict
        for key, value in event_dict.items():
            if key in ['event', 'level', 'logger', 'timestamp']:
                continue
            
            # Convert to systemd field format (uppercase, prefix with app name)
            field_name = f"NICESTLOG_{key.upper()}"
            
            # Systemd fields must be strings
            if isinstance(value, (dict, list)):
                journal_fields[field_name] = json.dumps(value, default=str)
            else:
                journal_fields[field_name] = str(value)
        
        # Send to journal
        try:
            journal.send(**journal_fields)
        except Exception as e:
            print(f"Failed to send to systemd journal: {e}", file=sys.stderr)
        
        return event_dict
    
    def emit(self, record):
        """
        Emit a log record to systemd journal.
        
        This method provides compatibility with standard Python logging handlers.
        """
        if not SYSTEMD_AVAILABLE and journal is None:
            return
        
        # Extract information from log record
        message = record.getMessage()
        level = record.levelname.lower()
        logger_name = record.name
        
        # Build journal fields
        priority = self.PRIORITY_MAP.get(level, 6)  # Default to LOG_INFO equivalent
        journal_fields = {
            'MESSAGE': str(message),
            'PRIORITY': str(priority),
            'SYSLOG_IDENTIFIER': self.identifier,
            'LOGGER_NAME': logger_name,
            'PYTHON_MODULE': logger_name,
            'SYSLOG_PID': str(self.pid),
            '_HOSTNAME': self.hostname,
            '_PID': str(self.pid),
            'CODE_FILE': getattr(record, 'pathname', ''),
            'CODE_LINE': str(getattr(record, 'lineno', '')),
            'CODE_FUNC': getattr(record, 'funcName', ''),
        }
        
        # Add facility if specified
        if self.facility:
            journal_fields['SYSLOG_FACILITY'] = self.facility
        
        # Add exception info if present
        if hasattr(record, 'exc_info') and record.exc_info:
            journal_fields['EXCEPTION_INFO'] = str(record.exc_info)
        
        if hasattr(record, 'exc_text') and record.exc_text:
            journal_fields['EXCEPTION_TEXT'] = record.exc_text
        
        # Send to journal
        try:
            journal.send(**journal_fields)
        except Exception as e:
            print(f"Failed to send to systemd journal: {e}", file=sys.stderr)


def detect_systemd_environment() -> Dict[str, Any]:
    """
    Detect if we're running under systemd and gather environment info.
    """
    info = {
        'running_under_systemd': False,
        'journal_available': SYSTEMD_AVAILABLE,
        'service_name': None,
        'unit_name': None,
        'invocation_id': None,
        'journal_stream': None,
        'systemd_exec_pid': None,
    }
    
    # Check if we're running under systemd
    if os.environ.get('SYSTEMD_EXEC_PID'):
        info['running_under_systemd'] = True
        info['systemd_exec_pid'] = os.environ.get('SYSTEMD_EXEC_PID')
    
    # Get systemd-specific environment variables
    info['invocation_id'] = os.environ.get('INVOCATION_ID')
    info['journal_stream'] = os.environ.get('JOURNAL_STREAM')
    
    # Try to get unit name from systemd
    if SYSTEMD_AVAILABLE:
        try:
            # This is a bit hacky but works
            with open('/proc/self/cgroup', 'r') as f:
                for line in f:
                    if 'systemd:' in line and '.service' in line:
                        parts = line.strip().split('/')
                        for part in parts:
                            if part.endswith('.service'):
                                info['unit_name'] = part
                                info['service_name'] = part.replace('.service', '')
                                break
        except Exception:
            pass
    
    return info


def setup_systemd_logging(identifier: str = None, facility: str = None, 
                         structured_fields: bool = True) -> bool:
    """
    Setup systemd journal logging integration.
    
    Args:
        identifier: SYSLOG_IDENTIFIER for journal entries
        facility: SYSLOG_FACILITY 
        structured_fields: Whether to include structured data as journal fields
    
    Returns:
        True if systemd logging was successfully configured
    """
    if not SYSTEMD_AVAILABLE:
        print("systemd-python not available. Install with: pip install systemd-python", 
              file=sys.stderr)
        return False
    
    env_info = detect_systemd_environment()
    
    # Use detected service name if no identifier provided
    if not identifier and env_info['service_name']:
        identifier = env_info['service_name']
    
    handler = SystemdJournalHandler(identifier=identifier, facility=facility)
    
    # Add to structlog processors
    current_config = structlog.get_config()
    processors = list(current_config.get('processors', []))
    
    # Insert before any renderers
    processors.insert(-1, handler)
    
    structlog.configure(
        processors=processors,
        logger_factory=current_config.get('logger_factory', structlog.stdlib.LoggerFactory()),
        wrapper_class=current_config.get('wrapper_class', structlog.stdlib.BoundLogger),
        cache_logger_on_first_use=True,
    )
    
    return True


def create_systemd_service_file(service_name: str, exec_command: str, 
                               user: str = None, working_directory: str = None,
                               environment: Dict[str, str] = None,
                               restart_policy: str = "always") -> str:
    """
    Generate a systemd service file with proper logging configuration.
    
    Args:
        service_name: Name of the service
        exec_command: Command to execute
        user: User to run as (default: current user)
        working_directory: Working directory
        environment: Environment variables
        restart_policy: Restart policy (always, on-failure, etc.)
    
    Returns:
        Service file content as string
    """
    user = user or os.getenv('USER', 'nobody')
    working_directory = working_directory or os.getcwd()
    environment = environment or {}
    
    service_content = f"""[Unit]
Description={service_name} - Managed by nicestlog
After=network.target
Wants=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_directory}
ExecStart={exec_command}
Restart={restart_policy}
RestartSec=5

# Logging configuration
StandardOutput=journal
StandardError=journal
SyslogIdentifier={service_name}

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={working_directory}

# Environment variables
"""
    
    for key, value in environment.items():
        service_content += f"Environment={key}={value}\n"
    
    service_content += """
[Install]
WantedBy=multi-user.target
"""
    
    return service_content


def query_journal_logs(service_name: str = None, since: str = "1 hour ago", 
                      level: str = None, lines: int = 100) -> List[Dict[str, Any]]:
    """
    Query systemd journal for logs.
    
    Args:
        service_name: Filter by service name
        since: Time filter (e.g., "1 hour ago", "today")
        level: Log level filter
        lines: Maximum number of lines
    
    Returns:
        List of log entries as dictionaries
    """
    if not SYSTEMD_AVAILABLE:
        print("systemd-python not available for journal queries", file=sys.stderr)
        return []
    
    try:
        j = journal.Reader()
        
        # Add filters
        if service_name:
            j.add_match(SYSLOG_IDENTIFIER=service_name)
        
        if level:
            priority = SystemdJournalHandler.PRIORITY_MAP.get(level.lower())
            if priority:
                j.add_match(PRIORITY=priority)
        
        # Set time filter
        if since:
            j.seek_realtime(datetime.now().timestamp() - parse_time_delta(since))
        
        # Get entries
        entries = []
        for entry in j:
            if len(entries) >= lines:
                break
            
            # Convert journal entry to dict
            log_entry = {
                'timestamp': entry['__REALTIME_TIMESTAMP'].timestamp(),
                'message': entry.get('MESSAGE', ''),
                'priority': entry.get('PRIORITY', 6),
                'identifier': entry.get('SYSLOG_IDENTIFIER', ''),
                'pid': entry.get('_PID', ''),
                'hostname': entry.get('_HOSTNAME', ''),
            }
            
            # Add custom fields
            for key, value in entry.items():
                if key.startswith('NICESTLOG_'):
                    field_name = key.replace('NICESTLOG_', '').lower()
                    log_entry[field_name] = value
            
            entries.append(log_entry)
        
        return list(reversed(entries))  # Most recent first
    
    except Exception as e:
        print(f"Error querying journal: {e}", file=sys.stderr)
        return []


def parse_time_delta(time_str: str) -> float:
    """Parse time strings like '1 hour ago' into seconds."""
    # Simple parser for common time formats
    time_str = time_str.lower().strip()
    
    if 'hour' in time_str:
        hours = int(time_str.split()[0])
        return hours * 3600
    elif 'minute' in time_str:
        minutes = int(time_str.split()[0])
        return minutes * 60
    elif 'day' in time_str:
        days = int(time_str.split()[0])
        return days * 24 * 3600
    elif time_str == 'today':
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        return (now - today_start).total_seconds()
    else:
        return 3600  # Default: 1 hour


def demo_systemd_integration():
    """Demonstrate systemd integration features."""
    print("🔧 Systemd Integration Demo")
    print("=" * 50)
    
    # Check environment
    env_info = detect_systemd_environment()
    print(f"Running under systemd: {env_info['running_under_systemd']}")
    print(f"Journal available: {env_info['journal_available']}")
    print(f"Service name: {env_info['service_name']}")
    print(f"Unit name: {env_info['unit_name']}")
    print(f"Invocation ID: {env_info['invocation_id']}")
    
    if SYSTEMD_AVAILABLE:
        # Setup systemd logging
        setup_systemd_logging(identifier="nicestlog-demo")
        
        # Create logger and test
        log = structlog.get_logger("systemd_demo")
        
        print("\n📝 Sending test logs to systemd journal...")
        log.info("systemd_integration_test", 
                component="demo", 
                test_data={"key": "value"},
                user_id=12345)
        
        log.warning("test_warning", 
                   message="This is a test warning for systemd")
        
        log.error("test_error", 
                 error_code=500, 
                 details="Test error for systemd journal")
        
        print("✅ Logs sent to systemd journal!")
        print("💡 View with: journalctl -f SYSLOG_IDENTIFIER=nicestlog-demo")
        
        # Query recent logs
        print("\n📖 Recent logs from journal:")
        recent_logs = query_journal_logs(service_name="nicestlog-demo", lines=5)
        for entry in recent_logs:
            timestamp = datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M:%S')
            print(f"  {timestamp} [{entry['identifier']}] {entry['message']}")
    
    else:
        print("\n⚠️  systemd-python not available")
        print("💡 Install with: pip install systemd-python")
    
    # Generate service file example
    print(f"\n📄 Example systemd service file:")
    service_file = create_systemd_service_file(
        service_name="my-python-app",
        exec_command="/usr/bin/python3 /opt/myapp/main.py",
        user="myapp",
        working_directory="/opt/myapp",
        environment={"PYTHONPATH": "/opt/myapp", "LOG_LEVEL": "info"}
    )
    
    print(service_file)
    print("💡 Save as /etc/systemd/system/my-python-app.service")


if __name__ == "__main__":
    demo_systemd_integration()
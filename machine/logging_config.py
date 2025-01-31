import logging
from contextlib import contextmanager
from typing import Optional


class GlobalIndent:
    """Global indentation and tree state"""
    _level = 0
    _tree_chars_single = {
        'pipe': '│',
        'branch': '├──',
        'leaf': '└──',
        'space': ' ' * 3
    }
    _tree_chars_double = {
        'pipe': '║',
        'branch': '║──',
        'leaf': '╚══',
        'space': ' ' * 3
    }
    _active_branches = set()
    _double_lines = set()

    @classmethod
    def increase(cls, double_line: bool = False):
        cls._level += 1
        cls._active_branches.add(cls._level - 1)
        if double_line:
            cls._double_lines.add(cls._level - 1)

    @classmethod
    def decrease(cls):
        if cls._level > 0:
            # No longer active - will show end corner
            cls._active_branches.discard(cls._level - 1)
            cls._double_lines.discard(cls._level - 1)
            cls._level -= 1

    @classmethod
    def get_indent(cls) -> str:
        if cls._level == 0:
            return ""

        parts = []
        # For all levels except current, show pipe only if level is still active
        for i in range(cls._level - 1):
            if i in cls._active_branches:
                chars = cls._tree_chars_double if i in cls._double_lines else cls._tree_chars_single
                parts.append(f"{chars['pipe']}   ")
            else:
                parts.append("    ")

        # For current level, use leaf if not active (end of block)
        chars = cls._tree_chars_double if (cls._level - 1) in cls._double_lines else cls._tree_chars_single
        is_end = (cls._level - 1) not in cls._active_branches
        parts.append(chars['leaf'] if is_end else chars['branch'])
        return "".join(parts)

class IndentLogger:
    """Logger wrapper that handles indentation using global state"""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, msg: str, *args, **kwargs):
        self._logger.debug(f"{self.indent}{msg}", *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._logger.info(f"{self.indent}{msg}", *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._logger.warning(f"{self.indent}{msg}", *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._logger.error(f"{self.indent}{msg}", *args, **kwargs)

    @property
    def indent(self) -> str:
        return GlobalIndent.get_indent()

    @contextmanager
    def indent_block(self, initial_message: Optional[str] = None, double_line: bool = False):
        """Context manager for handling indentation blocks"""
        if initial_message:
            self.debug(initial_message)
        GlobalIndent.increase(double_line)
        try:
            yield
        finally:
            GlobalIndent.decrease()


def configure_logging(level: Optional[str] = None):
    """Configure logging with the specified level"""

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)8s %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)

    # Set level based on input or default to INFO
    log_level = getattr(logging, (level or 'INFO').upper())
    root_logger.setLevel(log_level)

    # Configure loggers for different components
    loggers = {
        'rules_engine': logging.getLogger('rules_engine'),
        'service': logging.getLogger('service'),
        'rule_context': logging.getLogger('rule_context'),
        'logger': logging.getLogger('rule_context'),
    }

    # Configure each logger
    for name, logger in loggers.items():
        logger.setLevel(log_level)
        logger.propagate = False  # Prevent duplicate logging
        logger.addHandler(console_handler)

    return loggers

import re
from .utils import cli_util


def process_entry(log_line):
    """
    Given a log line from the logs, extracts the name of the file and line numbers that were covered
    :param string log_line: line of log
    :return list({'name': string, 'line': integer}):
    """
    processed_logs = []
    pair = log_line.split(',')
    if len(pair) != 2:
        cli_util.error('Invalid formatting for result: {}'.format(pair))
        return []

    name = pair[0]
    lines = pair[1].split(' ')
    for line in lines:
        if line != '':
            processed_logs.append({'name': name, 'line': int(line)})

    return processed_logs


def process_logs(logs):
    """
    Given logs contents, returns a
    :param string logs: the log contents to process
    :return list({'name': string, 'line': integer}):
    """
    pattern = r'\[INSTR\] (.*)'
    matches = re.finditer(pattern, logs)
    processed_logs = []
    for match in matches:
        if len(match.groups()) != 1:
            cli_util.error('Invalid matching for result: {}'.format(match.groups()))
            continue

        match_group = match.groups()[0]
        line_dicts = process_entry(match_group)
        if line_dicts:
            processed_logs += line_dicts

    return processed_logs

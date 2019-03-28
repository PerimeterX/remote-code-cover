import re

from .constants import SYSLOG_INSTRUMENTATION_NAME


def get_var_line(line_number, tested_line_numbers, sub_tested_line_numbers,
                 instr_lines, sub_start_line_number, l_ws_cou):
    sub_tested_line_numbers.append(line_number)
    tested_line_numbers.append(line_number)
    instr_lines.insert(sub_start_line_number, '  declare local var.log_{} BOOL;'.format(line_number))
    return '{}set var.log_{} = true;'.format(' ' * l_ws_cou, line_number)


def get_syslog_line(name, sub_tested_line_numbers, l_ws_cou):
    log_additions = ''.join([' + if(var.log_{}, "{} ", "")'.format(l_n, l_n) for l_n in sub_tested_line_numbers])
    log_template = '{}log "syslog " req.service_id " {} :: [INSTR] {},"{};'
    return log_template.format(' ' * l_ws_cou, SYSLOG_INSTRUMENTATION_NAME, name, log_additions)


def is_line_sub_header(line):
    return line[:4] == 'sub '


def count_leading_whitespaces(line):
    return len(line) - len(line.lstrip())


def do_test_line(line):
    return line != '' and line[0] != '#'


def strip_line(line):
    # find trailing comment and remove it
    matches = re.findall(r'{\s*(#.*)', line)
    if len(matches) > 0:
        line = line.replace(matches[0], '')
    stripped_line = line.strip()
    return stripped_line


def has_open_params(is_tested, line):
    return is_tested and line[-1] == '{'


def has_close_params(is_tested, line):
    return is_tested and line[0] == '}'


def is_return_line(line):
    return line[:6] == 'return' or line[:6] == 'error ' or line[:7] == 'restart'


def end_of_subroutine(in_subroutine, parens_stack):
    return in_subroutine and len(parens_stack) == 0


def add_instrumentation(name, content):
    """
    Adds instrumentation to the code.

    Main properties:
    1. Coverage is only done inside subroutines
    2. Blank lines are omitted
    3. Comments are omitted

    :param string name: the name of the file
    :param string content: the code to instrument
    :return string, integer, list: instrumented code, original file line count
    and a list of line numbers that are tested for coverage
    """
    lines = content.split('\n')
    original_line_count = 1
    instrumented_lines = []
    subroutine_parenthesis_stack = []
    sub_tested_line_numbers = []
    tested_line_numbers = []
    cur_subroutine_decl_line_number = 0
    in_subroutine = False
    in_synthetic = False

    for raw_line in lines:
        stripped_line = strip_line(raw_line)
        is_tested = do_test_line(stripped_line)
        l_ws_cou = count_leading_whitespaces(raw_line)

        def add_log_line(subroutine_decl_line_number=cur_subroutine_decl_line_number, my_l_ws_cou=l_ws_cou):
            instrumented_lines.append(get_var_line(original_line_count, tested_line_numbers, sub_tested_line_numbers,
                                                   instrumented_lines, subroutine_decl_line_number, my_l_ws_cou))

        if is_line_sub_header(stripped_line):
            # if we reached a sub header, we add the log for it *after*
            # the line since we can't log outside subroutines
            in_subroutine = True
            instrumented_lines.append(raw_line)
            cur_subroutine_decl_line_number = len(instrumented_lines)
            subroutine_parenthesis_stack.append(original_line_count)
        elif not in_subroutine:
            instrumented_lines.append(raw_line)
        elif in_subroutine:
            if stripped_line[:11] == 'synthetic {':
                add_log_line(subroutine_decl_line_number=cur_subroutine_decl_line_number,
                             my_l_ws_cou=2)
                in_synthetic = True
                if stripped_line[-2:] == '};':
                    in_synthetic = False
            elif in_synthetic:
                if stripped_line[-2:] == '};':
                    in_synthetic = False
            elif has_close_params(is_tested, stripped_line):  # is_close_parens
                subroutine_parenthesis_stack.pop()
                if end_of_subroutine(in_subroutine, subroutine_parenthesis_stack):
                    instrumented_lines.append(get_syslog_line(name, sub_tested_line_numbers, 2))
                    sub_tested_line_numbers = []
                    in_subroutine = False
                elif has_open_params(is_tested, stripped_line):
                    add_log_line()
                    subroutine_parenthesis_stack.append(original_line_count)
            elif has_open_params(is_tested, stripped_line):  # is_open_parens
                add_log_line()
                subroutine_parenthesis_stack.append(original_line_count)
            elif is_return_line(stripped_line):
                add_log_line()
                instrumented_lines.append(get_syslog_line(name, sub_tested_line_numbers, l_ws_cou))
            elif is_tested:
                add_log_line()

            instrumented_lines.append(raw_line)

        original_line_count += 1

    instrumented_content = '\n'.join(instrumented_lines)
    return instrumented_content, original_line_count, tested_line_numbers


def instrument(vcls):
    """
    Given a list of custom_vcls, add instrumentation to them and return the instrumentation mapping
    :param vcls: array of dictionaries {"name", "content"}
    :return list, dictionary: A tuple of the instrumented custom_vcls and their mapping
    """
    instr_mapping = {}
    instr_vcls = []
    for i, vcl in enumerate(vcls):
        name = vcl['name']
        content = vcl['content']
        instr_content, orig_line_count, tested_line_numbers = add_instrumentation(str(i), content)
        instr_vcl = dict(vcl)
        instr_vcl['content'] = instr_content
        instr_vcls.append(instr_vcl)
        instr_mapping[name] = {
            'original_content': content,
            'orig_line_count': orig_line_count,
            'tested_line_count': len(tested_line_numbers),
            'tested_line_numbers': tested_line_numbers,
            'name_mapping': i
        }

    return instr_vcls, instr_mapping

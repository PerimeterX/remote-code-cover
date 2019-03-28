from os import path
import json
from collections import defaultdict
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from .utils import fs_util, string_util

CUR_DIR = path.dirname(__file__)


def calc_percentage(nominator, denominator, ndigits=2):
    if denominator == 0:
        return 0
    return round(float(nominator) * 100 / denominator, ndigits)


def calculate_coverage(instrumentation_mappings, processed_logs):
    """
    Given the parameters, returns a coverage object that contains the needed data for the report
    :param dict instrumentation_mappings: a dictionary of
    key: name, value: properties that includes instrumentation mappings
    :param list processed_logs: a list of processed logs that contain the coverage information
    :return dict: coverage object
    """

    # Removing duplicate lines
    logs_by_name_line = defaultdict(dict)
    for log_line in processed_logs:
        logs_by_name_line[log_line['name']][log_line['line']] = log_line

    coverage_object = {}
    files = {}
    global_tested_line_count = 0
    global_covered_line_count = 0
    for name, vcl_mapping in instrumentation_mappings.items():
        tested_line_count = vcl_mapping['tested_line_count']
        original_content = vcl_mapping['original_content']
        logs = logs_by_name_line[str(vcl_mapping['name_mapping'])]
        covered_line_numbers = list(logs.keys())
        covered_line_count = len(logs)
        tested_line_numbers = vcl_mapping['tested_line_numbers']
        uncovered_line_numbers = [line for line in tested_line_numbers if line not in covered_line_numbers]
        files[name] = {
            'name': name,
            'coverage_line_percentage': calc_percentage(covered_line_count, tested_line_count),
            'covered_line_count': covered_line_count,
            'tested_line_count': tested_line_count,
            'total_line_count': len(original_content.split('\n')),
            'original_content': original_content,
            'tested_line_numbers': tested_line_numbers,
            'uncovered_line_numbers': uncovered_line_numbers,
            'covered_line_numbers': covered_line_numbers
        }
        global_tested_line_count += tested_line_count
        global_covered_line_count += covered_line_count

    coverage_object['files'] = files
    coverage_object['global'] = {
        'coverage_line_percentage': calc_percentage(global_covered_line_count, global_tested_line_count),
        'covered_line_count': global_covered_line_count,
        'tested_line_count': global_tested_line_count,
    }

    return coverage_object


def coverage_percentage_to_level(percentage):
    if percentage < 50:
        return 'low'
    if percentage < 80:
        return 'medium'
    return 'high'


def generate_html_report(coverage_object):
    """
    Given a coverage object returns an html report
    :param dict coverage_object:
    :return list(string), string: html files, css file
    """
    lexer = get_lexer_by_name('ruby', stripall=True)
    formatter = HtmlFormatter(linenos=True, cssclass='source')

    assets_dir = path.join(CUR_DIR, 'assets')
    css = fs_util.read_file(path.join(assets_dir, 'highlight.css'))
    summary_template = fs_util.read_file(path.join(assets_dir, 'summary.jinja2'))
    source_code_template = fs_util.read_file(path.join(assets_dir, 'code_cover.jinja2'))
    html_files = {}
    file_names = coverage_object['files'].keys()
    for file_name, file_coverage in coverage_object['files'].items():
        source = highlight(file_coverage['original_content'], lexer, formatter)
        source_lines = source.split('\n')
        # find the start of the code
        indices = [i for (i, line) in enumerate(source_lines) if '<td class="code"><div class="source"><pre>' in line]
        if len(indices) != 1:
            raise Exception('No suitable pre code entries found')
        uncovered_line_numbers_offset = [indices[0] + i - 1 for i in file_coverage['uncovered_line_numbers']]
        for i in uncovered_line_numbers_offset:
            source_lines[i] = '<span class="uncovered">{}</span>'.format(source_lines[i])
        covered_line_numbers_offset = [indices[0] + i - 1 for i in file_coverage['covered_line_numbers']]
        for i in covered_line_numbers_offset:
            source_lines[i] = '<span class="covered">{}</span>'.format(source_lines[i])
        source = '\n'.join(source_lines)
        file_coverage['coverage_level'] = coverage_percentage_to_level(file_coverage['coverage_line_percentage'])
        result = string_util.render_template_with_variables(source_code_template, {
            'title': '{}.vcl'.format(file_name),
            'file_names': file_names,
            'file': file_coverage,
            'source': source,
            'coverage_level': file_coverage['coverage_level'],
        })
        html_files[file_name] = result

    html_files['index'] = string_util.render_template_with_variables(summary_template, {
        'global': coverage_object['global'],
        'files': coverage_object['files'].values(),
        'file_names': file_names,
        'coverage_level': coverage_percentage_to_level(coverage_object['global']['coverage_line_percentage'])
    })

    return html_files, css


def write_html_report(html_files, css, coverage_object):
    """
    Writes the html report to disk
    :param list(string) html_files:
    :param string css:
    :param dict coverage_object:
    :return None:
    """
    base_path = path.join('coverage')
    fs_util.mkdirp(base_path)
    for file_name, content in html_files.items():
        fs_util.write_file(path.join(base_path, file_name + '.html'), content)
    fs_util.write_file(path.join(base_path, 'highlight.css'), css)
    fs_util.write_file(path.join(base_path, 'coverage.json'), json.dumps(coverage_object, indent=2))

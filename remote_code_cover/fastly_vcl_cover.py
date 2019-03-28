from os import path
import os
from .utils.fastly_api_util import FastlyApiClient
from .utils import fs_util, cli_util
from . import instrumentator, logs_collector, logs_processor, reporter
from .constants import SYSLOG_INSTRUMENTATION_NAME


def upload_instrumented_version(fastly_client, proxy_remote_addr):
    """
    Retrieves active version, instruments it and uploads it as a draft version
    :param fastly_api_cover.utils.fastly_api_util.FastlyApiClient fastly_client:
    :param string proxy_remote_addr: the remote addr to send syslogs to
    :return integer, integer, dict:
    """
    cli_util.output('Retrieving active version custom vcls')
    active_version = fastly_client.get_active_version()
    custom_vcls = fastly_client.get_all_custom_vcls(active_version)

    cli_util.output('Applying instrumentation on code..')
    instr_vcls, instrumentation_mapping = instrumentator.instrument(custom_vcls)

    draft_version = fastly_client.clone_version(active_version)
    cli_util.output('Uploading custom vcls to draft version {}'.format(draft_version))
    for instr_vcl in instr_vcls:
        is_main = 'true' if instr_vcl['main'] else 'false'
        vcl_to_upload = {'name': instr_vcl['name'], 'content': instr_vcl['content'], 'main': is_main}
        fastly_client.delete_custom_vcl(draft_version, vcl_to_upload['name'])
        fastly_client.create_custom_vcl(draft_version, vcl_to_upload)

    fastly_client.delete_syslog(draft_version, SYSLOG_INSTRUMENTATION_NAME)
    address, port = proxy_remote_addr.split(':')
    fastly_client.create_syslog(draft_version, {
        'name': SYSLOG_INSTRUMENTATION_NAME,
        'address': address,
        'hostname': address,
        'port': port,
    })

    return active_version, draft_version, instrumentation_mapping


def run_coverage(fastly_token, fastly_service_id, standalone_proxy, proxy_remote_addr, ngrok_auth_token,
                 non_interactive, listen_seconds=None):
    """
    1. Instrument vcl code
    2. Deploy it (including Px-Instrumentation syslog)
    3. Run a local ngrok (if standalone_proxy is False) or use standalone
    4. Run a local syslog server as an upstream of ngrok endpoint (listening for logs output)
    (Run end-to-end tests externally on the deployed website - the process will capture the logs output)
    5. When tests finished, parse the logs into instrumentation result in instrumentation report
    6. Display the report
    :return None:
    """

    try:
        cli_util.set_interactive(not non_interactive)

        fastly_client = FastlyApiClient(fastly_token, fastly_service_id)

        active_version, draft_version, instrumentation_mapping = upload_instrumented_version(fastly_client,
                                                                                             proxy_remote_addr)

        logs_path = path.join('/tmp', 'syslog')

        try:
            cli_util.important('Activating version {}..'.format(draft_version))
            fastly_client.activate_version(draft_version)

            fs_util.remove_file(path.join(logs_path, 'messages'))

            logs_collector.start_listening(logs_path, standalone_proxy, proxy_remote_addr, listen_seconds,
                                           ngrok_auth_token)

            instr_logs = logs_collector.collect_logs(logs_path)
            processed_logs = logs_processor.process_logs(instr_logs)

            coverage_object = reporter.calculate_coverage(instrumentation_mapping, processed_logs)
            html_files, css = reporter.generate_html_report(coverage_object)

            reporter.write_html_report(html_files, css, coverage_object)

            coverage_path = path.join(os.getcwd(), 'coverage')
            cli_util.important('Coverage report saved to {}'.format(cli_util.blue_bold(coverage_path)))
            cli_util.output('Opening coverage html report..')
            fs_util.open_file(path.join(coverage_path, 'index.html'))

        finally:
            fs_util.remove_file(path.join(logs_path, 'messages'))
            fastly_client.activate_version(active_version)
            cli_util.important('Reactivated original version {}'.format(active_version))

    except Exception as err:
        cli_util.exception_format(err)

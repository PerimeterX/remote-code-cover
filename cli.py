import click
from remote_code_cover import fastly_vcl_cover


@click.command(name='fastly', help='Run test coverage on a Fastly service')
@click.option('--fastly-token', '-t', required=True, help='Fastly api token')
@click.option('--fastly-service-id', '-s', required=True, help='Fastly service id')
@click.option('--standalone-proxy', required=False, is_flag=True, help=('whether to use a standalone proxy to '
                                                                        'expose the local syslog server for '
                                                                        'incoming requests'))
@click.option('--proxy-remote-addr', required=True, help='ngrok remote address to expose syslog server')
@click.option('--ngrok-auth-token', required=False, help='ngrok authtoken to expose syslog server')
@click.option('--non-interactive', '-ni', required=False, is_flag=True,
              help='Runs the installation ignoring user input')
@click.option('--listen-seconds', type=int, required=False, help='Listening time in seconds until stopping')
def cover_fastly(fastly_token, fastly_service_id, standalone_proxy, proxy_remote_addr, ngrok_auth_token,
                 non_interactive, listen_seconds):
    click.echo('Running coverage for fastly')
    fastly_vcl_cover.run_coverage(fastly_token,
                                  fastly_service_id,
                                  standalone_proxy,
                                  proxy_remote_addr,
                                  ngrok_auth_token,
                                  non_interactive,
                                  listen_seconds)


@click.group(help='Runs coverage analysis')
def cover():
    pass


@click.group(help='A CLI tool for code instrumentation and test coverage reporting')
def main():
    pass


main.add_command(cover_fastly)

if __name__ == '__main__':
    main()

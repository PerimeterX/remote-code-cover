# Remote Code Cover

rcc is a CLI tool for code instrumentation and test coverage reporting, with support for:

- Fastly VCL

## Installation

1. Change to your preferred python setup (preferred from a virtual environment)
2. Run `pip install git+https://github.com/PerimeterX/remote-code-cover`

> If a permissions error occurs, add --user flag to the command: `pip install --user ...`

## Usage

Run `rcc --help` for usage instructions.

### Fastly VCL

Prerequisites:

1. Docker daemon running on your machine
2. A Fastly service with custom VCL and credentials for that service

Using reserved TCP address with Ngrok:

```bash
rcc fastly --fastly-token <fastly_api_key> \
--fastly-service-id <fastly_service_id> \
--proxy-remote-addr <tcp_domain>:<port> \
--ngrok-auth-token <ngrok_premium_token>
```

Or, using a standalone proxy is running in the background and forwarding TCP to port 514:

```bash
rcc fastly --fastly-token <fastly_api_key> \
--fastly-service-id <fastly_service_id> \
--proxy-remote-addr <tcp_domain>:<port> \
--standalone-proxy
```

The above commands will create a new version for the service with the instrumented code,
and then wait for tests to be run against the configured website:

```
! You can now run the tests. Press any key when the tests finished..
```

After clicking, a coverage report will be created at `./coverage` and opened in the browser, which looks like:

![Example Fastly VCL Report](https://github.com/PerimeterX/remote-code-cover/blob/master/assets/example-vcl-report.png)

You can run `rcc fastly --help` for exact usage info.

That's it!

## Contributing

The following steps are welcome when contributing to our project:

### Fork/Clone
First and foremost, [Create a fork](https://guides.github.com/activities/forking/) of the repository, and clone it locally.
Create a branch on your fork, preferably using a self descriptive branch name.

### Code/Run
Help improve our project by implementing missing features, adding capabilities or fixing bugs.

To run the code, simply follow the steps in the [installation Section](#installation).

### Pull Request
After you have completed the process, create a pull request to the Upstream repository.
Please provide a complete and thorough description explaining the changes.
Remember this code has to be read by our maintainers, so keep it simple, smart and accurate.
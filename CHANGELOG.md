## CHANGELOG

### v1.0.0 (2019-03-29)
#### Added
* End-to-end test coverage for Fastly VCL services:
  * Command-line app
  * Uses Fastly API to apply instrumentation to the VCL of a given Fastly service.
  * Instrumentation traces are sent via syslog back to the machine running the CLI app.
  * The logs are processed and an HTML test coverage report is executed.
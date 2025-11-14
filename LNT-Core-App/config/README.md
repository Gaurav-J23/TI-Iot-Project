# Test Configuration Files

Place your `test.yaml` files in this directory or reference them by path when starting tests.

## Example Usage

The `example_test.yaml` file shows the expected structure for test configuration files.

## Test YAML Structure

- **Job**: Contains test name and description
- **Firmwrare/Firmware**: Maps device hosts to DUT images
- **serial_steams/serial_streams**: Configures serial stream monitoring
- **serial_logs**: Specifies log file paths for serial ports
- **test_duration**: Test duration in format "Xd Xh Xm"


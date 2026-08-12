package elm327

import (
	"bufio"
	"fmt"
	"strings"
	"time"

	"go.bug.st/serial"
)

// Client wraps a serial connection to an ELM327 adapter.
type Client struct {
	port   serial.Port
	reader *bufio.Reader
}

// Open connects to the adapter on portName ("/dev/tty.OBDII", "COM3", ...) and
// runs the init handshake.
func Open(portName string, baud int) (*Client, error) {
	port, err := serial.Open(portName, &serial.Mode{BaudRate: baud})
	if err != nil {
		return nil, fmt.Errorf("elm327: open %s: %w", portName, err)
	}
	c := &Client{port: port, reader: bufio.NewReader(port)}
	if err := c.init(); err != nil {
		port.Close()
		return nil, err
	}
	return c, nil
}

func (c *Client) init() error {
	for _, cmd := range []string{"ATZ", "ATE0", "ATL0", "ATSP0"} {
		if _, err := c.Command(cmd); err != nil {
			return fmt.Errorf("elm327: init %s: %w", cmd, err)
		}
		time.Sleep(100 * time.Millisecond)
	}
	return nil
}

// Command sends one command and returns the response payload. This is the core
// framing: the adapter delimits every response with the '>' prompt, and lines
// within it are separated by CR ('\r'), never '\n'. So: read until '>', split on
// '\r', and drop the echoed command / status lines.
func (c *Client) Command(cmd string) (string, error) {
	if _, err := c.port.Write([]byte(cmd + "\r")); err != nil {
		return "", err
	}
	resp, err := c.reader.ReadString('>') // <-- read until the prompt
	if err != nil {
		return "", err
	}
	resp = strings.TrimSuffix(resp, ">")

	var lines []string
	for _, ln := range strings.Split(resp, "\r") {
		ln = strings.TrimSpace(ln)
		if ln == "" || ln == cmd { // skip blanks and an echoed command
			continue
		}
		lines = append(lines, ln)
	}
	return strings.Join(lines, "\n"), nil
}

// Close releases the serial port.
func (c *Client) Close() error { return c.port.Close() }

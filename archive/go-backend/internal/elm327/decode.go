// Package elm327 speaks the ELM327 protocol: serial framing plus from-scratch
// decoding of Mode 01 (live data) and Mode 03 (fault codes) responses.
package elm327

import (
	"errors"
	"fmt"
	"strconv"
	"strings"

	"carobd/internal/obd"
)

// ErrNoData means the ECU had no reading for that PID (unsupported / not ready).
var ErrNoData = errors.New("elm327: NO DATA")

// DecodePID decodes a Mode 01 response ("41 0C 1A F8") into its value using the
// formula registered for pid ("010C").
func DecodePID(pid, raw string) (float64, error) {
	if strings.Contains(strings.ToUpper(raw), "NO DATA") {
		return 0, ErrNoData
	}
	def, ok := obd.Registry[pid]
	if !ok {
		return 0, fmt.Errorf("elm327: no decoder for PID %s", pid)
	}
	b, err := parseHexBytes(raw)
	if err != nil {
		return 0, err
	}
	if len(b) < 2 || b[0] != 0x41 {
		return 0, fmt.Errorf("elm327: not a Mode 01 response: %q", raw)
	}
	data := b[2:] // drop 0x41 + PID echo
	if len(data) == 0 {
		return 0, fmt.Errorf("elm327: no data bytes: %q", raw)
	}
	return def.Decode(data), nil
}

// DecodeDTCs decodes a Mode 03 response ("43 02 17") into codes (["P0217"]).
func DecodeDTCs(raw string) ([]string, error) {
	b, err := parseHexBytes(raw)
	if err != nil {
		return nil, err
	}
	if len(b) == 0 || b[0] != 0x43 {
		return nil, fmt.Errorf("elm327: not a Mode 03 response: %q", raw)
	}
	letters := [4]byte{'P', 'C', 'B', 'U'}
	var codes []string
	for i := 1; i+1 < len(b); i += 2 {
		b1, b2 := b[i], b[i+1]
		if b1 == 0 && b2 == 0 {
			continue // padding
		}
		letter := letters[(b1>>6)&0x3]
		first := (b1 >> 4) & 0x3
		second := b1 & 0x0F
		codes = append(codes, fmt.Sprintf("%c%d%X%02X", letter, first, second, b2))
	}
	return codes, nil
}

// parseHexBytes turns "41 0C 1A F8" (with any '>' prompt / spacing) into bytes.
func parseHexBytes(raw string) ([]byte, error) {
	fields := strings.Fields(strings.ReplaceAll(raw, ">", ""))
	if len(fields) == 0 {
		return nil, errors.New("elm327: empty response")
	}
	out := make([]byte, 0, len(fields))
	for _, f := range fields {
		v, err := strconv.ParseUint(f, 16, 8)
		if err != nil {
			return nil, fmt.Errorf("elm327: bad hex %q in %q", f, raw)
		}
		out = append(out, byte(v))
	}
	return out, nil
}

// Package obd holds the OBD-2 PID definitions and their decode formulas.
// Formulas match the Python reference in testing/test_record_parsing.py so the
// Go decoder can be validated against the same fixtures.
package obd

import "math"

// PID describes a Mode 01 parameter and how to decode its data bytes (A, B, ...).
type PID struct {
	Command string // e.g. "010C"
	Name    string // e.g. "engine_rpm"
	Unit    string // e.g. "rpm"
	Decode  func(data []byte) float64
}

func round1(f float64) float64 { return math.Round(f*10) / 10 }

func word(d []byte) int { return int(d[0])<<8 | int(d[1]) } // A*256 + B

// Registry maps a PID command to its definition. Extend as you add sensors.
var Registry = map[string]PID{
	"0104": {"0104", "engine_load", "percent", func(d []byte) float64 { return round1(float64(d[0]) * 100 / 255) }},
	"0105": {"0105", "coolant_temp", "C", func(d []byte) float64 { return float64(d[0]) - 40 }},
	"010C": {"010C", "engine_rpm", "rpm", func(d []byte) float64 { return float64(word(d)) / 4 }},
	"010D": {"010D", "vehicle_speed", "km/h", func(d []byte) float64 { return float64(d[0]) }},
	"010F": {"010F", "intake_air_temp", "C", func(d []byte) float64 { return float64(d[0]) - 40 }},
	"0110": {"0110", "maf_air_flow", "g/s", func(d []byte) float64 { return float64(word(d)) / 100 }},
	"0111": {"0111", "throttle_position", "percent", func(d []byte) float64 { return round1(float64(d[0]) * 100 / 255) }},
	"0114": {"0114", "o2_sensor_voltage", "V", func(d []byte) float64 { return float64(d[0]) / 200 }},
	"012F": {"012F", "fuel_level", "percent", func(d []byte) float64 { return round1(float64(d[0]) * 100 / 255) }},
	"0142": {"0142", "control_module_voltage", "V", func(d []byte) float64 { return float64(word(d)) / 1000 }},
}

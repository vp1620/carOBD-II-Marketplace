// Command carobd is a framework skeleton for the Go backend: poll OBD-2 PIDs from
// an ELM327 adapter and stream them to browsers over WebSockets.
//
// PARKED / FUTURE WORK — see ../README.md. Not part of the Phase 1 Python build.
// The wiring is real; the adapter port and error handling are left as TODOs.
package main

import (
	"log"
	"net/http"
	"time"

	"carobd/internal/elm327"
	"carobd/internal/obd"
	"carobd/internal/server"
)

const (
	portName = "/dev/tty.OBDII" // TODO: discover / make configurable
	baudRate = 38400
)

// pollList is the set of PIDs polled each cycle.
var pollList = []string{"010C", "010D", "0105", "0111", "0110", "0114", "0142"}

func main() {
	hub := server.NewHub()
	http.HandleFunc("/ws", hub.Handle)

	go pollLoop(hub)

	log.Println("carobd: listening on :8080 (WebSocket at /ws)")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func pollLoop(hub *server.Hub) {
	client, err := elm327.Open(portName, baudRate)
	if err != nil {
		// No adapter connected — leave the loop idle so the server still runs.
		// TODO: for offline dev, drive this from archive/parser-fixtures instead.
		log.Printf("carobd: no adapter (%v) — poll loop idle", err)
		return
	}
	defer client.Close()

	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	for range ticker.C {
		for _, pid := range pollList {
			raw, err := client.Command(pid)
			if err != nil {
				log.Printf("carobd: %s: %v", pid, err)
				continue
			}
			value, err := elm327.DecodePID(pid, raw)
			if err != nil {
				continue // NO DATA / unsupported PID
			}
			def := obd.Registry[pid]
			hub.Broadcast(server.Reading{
				Type:  "pid",
				PID:   pid,
				Name:  def.Name,
				Value: value,
				Unit:  def.Unit,
			})
		}
	}
}

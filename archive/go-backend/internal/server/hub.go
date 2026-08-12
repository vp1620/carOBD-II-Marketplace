// Package server broadcasts OBD readings to browsers over WebSockets.
package server

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
)

// Reading is one transaction pushed to clients — mirrors the JSON shape in
// testing/sample_obd_output.json.
type Reading struct {
	Timestamp string   `json:"timestamp,omitempty"`
	VehicleID string   `json:"vehicle_id,omitempty"`
	Type      string   `json:"type"`
	PID       string   `json:"pid,omitempty"`
	Name      string   `json:"name"`
	Value     float64  `json:"value,omitempty"`
	Unit      string   `json:"unit,omitempty"`
	Codes     []string `json:"codes,omitempty"`
}

// Hub fans out readings to every connected WebSocket client.
type Hub struct {
	mu       sync.Mutex
	clients  map[*websocket.Conn]struct{}
	upgrader websocket.Upgrader
}

func NewHub() *Hub {
	return &Hub{
		clients:  map[*websocket.Conn]struct{}{},
		upgrader: websocket.Upgrader{CheckOrigin: func(*http.Request) bool { return true }}, // TODO: tighten for prod
	}
}

// Handle upgrades an HTTP request to a WebSocket and registers the client.
func (h *Hub) Handle(w http.ResponseWriter, r *http.Request) {
	conn, err := h.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("server: upgrade: %v", err)
		return
	}
	h.mu.Lock()
	h.clients[conn] = struct{}{}
	h.mu.Unlock()
}

// Broadcast sends a reading to all clients as JSON, dropping any that error.
func (h *Hub) Broadcast(rd Reading) {
	payload, err := json.Marshal(rd)
	if err != nil {
		return
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	for conn := range h.clients {
		if err := conn.WriteMessage(websocket.TextMessage, payload); err != nil {
			conn.Close()
			delete(h.clients, conn)
		}
	}
}

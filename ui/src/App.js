import React, { useEffect, useState } from "react";

function App() {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchEvents = async () => {
    try {
      const response = await fetch("http://localhost:5000/events");

      if (!response.ok) {
        throw new Error("Server error");
      }

      const data = await response.json();
      setEvents(data);
      setLoading(false);
      setError(null);

    } catch (err) {
      setError("Backend not reachable");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>GitHub Webhook Events</h1>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {events.map((event) => (
        <div
          key={event._id}
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            margin: "10px 0",
            borderRadius: "8px",
            background: "#f9f9f9"
          }}
        >
          <h3>{event.type}</h3>
          <p><b>Author:</b> {event.author}</p>

          {event.from_branch && (
            <p><b>From:</b> {event.from_branch}</p>
          )}

          <p><b>To:</b> {event.to_branch}</p>
          <p><b>Time:</b> {event.timestamp}</p>
        </div>
      ))}
    </div>
  );
}

export default App;
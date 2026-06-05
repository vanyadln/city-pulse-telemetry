import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import useCityPulse from '../hooks/useCityPulse';
import 'leaflet/dist/leaflet.css';

export default function SentimentMap() {
    // INITIALIZE THE HOOK TO EXTRACT THE LIVE STATE VARIABLES
    const { pulses, isConnected } = useCityPulse('ws://localhost:8080/ws');

    const getColor = (score) => {
    // Force the input into a floating-point number so comparison math works
    const numericScore = parseFloat(score);

    if (numericScore > 0.1) return '#22c55e';  // Bright Green
    if (numericScore < -0.1) return '#ef4444'; // Bright Red
    return '#eab308';                          // Neutral Yellow
};

    return (
        <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif', backgroundColor: '#111827', color: '#fff' }}>
            {/* Sidebar Feed */}
            <div style={{ width: '30%', padding: '20px', overflowY: 'auto', borderRight: '1px solid #374151', backgroundColor: '#1f2937' }}>
                <h2>CityPulse</h2>
                <p style={{ fontSize: '14px', color: pulses.length > 0 ? '#22c55e' : '#ef4444' }}>
                    {pulses.length > 0 ? '● Live telemetry pipeline active' : '● Pipeline disconnected'}
                </p>
                
                <hr style={{ borderColor: '#374151' }} />
                <h3>Live Feed Streams</h3>
                <div>
                    
                    {pulses.map((p, idx) => (
                      <div key={idx} style={{ padding: '10px', marginBottom: '10px', backgroundColor: getColor(p.sentiment_score) + '22', borderRadius: '4px', borderLeft: `4px solid ${getColor(p.sentiment_score)}` }}>
                      <strong style={{ color: '#9ca3af', fontSize: '12px' }}>{p.city || 'Unknown City'}</strong>
                      <p style={{ margin: '5px 0', fontSize: '14px' }}>{p.text || p.title}</p>
                      <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Score: {p.sentiment_score}</span>
                    </div>
                    ))}
                </div>
            </div>

            {/* Interactive Map */}
            <div style={{ width: '70%', height: '100%' }}>
                <MapContainer center={[22.5937, 78.9629]} zoom={3} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        attribution="&copy; CARTO"
                    />
                    {pulses.map((p, idx) => {
    const markerColor = getColor(p.sentiment_score);
    
    return (
        <CircleMarker
            key={`${idx}-${p.sentiment_score}`} // Forces Leaflet to re-render the color when data changes
            center={[p.lat, p.lon]}
            radius={8} // Fixed clean size so it doesn't look ugly and massive
            pathOptions={{
                fillColor: markerColor,
                color: markerColor,
                weight: 1,
                fillOpacity: 0.6 // Vibrant fill color
            }}
        >
            <Popup>
                <strong>{p.city}</strong><br />
                {p.text}<br />
                <span>Sentiment: {p.sentiment_score}</span>
            </Popup>
        </CircleMarker>
    );
})}
                </MapContainer>
            </div>
        </div>
    );
}
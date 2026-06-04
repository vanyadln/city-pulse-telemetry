import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import useCityPulse from '../hooks/useCityPulse';
import 'leaflet/dist/leaflet.css';

export default function SentimentMap() {
    const { pulses, connected } = useCityPulse('https://city-pulse-telemetry.onrender.com');

    const getColor = (score) => {
        if (score > 0.1) return '#22c55e'; // Bright Green
        if (score < -0.1) return '#ef4444'; // Bright Red
        return '#eab308'; // Neutral Yellow
    };

    return (
        <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif', backgroundColor: '#111827', color: '#f3f4f6' }}>
            {/* Sidebar Feed */}
            <div style={{ width: '30%', padding: '20px', overflowY: 'auto', borderRight: '1px solid #374151' }}>
                <h2 style={{ margin: 0 }}>CityPulse Dashboard</h2>
                <p style={{ fontSize: '14px', color: connected ? '#22c55e' : '#ef4444' }}>
                    ● {connected ? 'Live telemetry pipeline active' : 'Pipeline disconnected'}
                </p>
                <hr style={{ borderColor: '#374151' }} />
                <h3>Live Feed Streams</h3>
                <div>
                    {pulses.map((p, idx) => (
                        <div key={idx} style={{ padding: '10px', marginBottom: '10px', backgroundColor: '#1f2937', borderRadius: '6px', borderLeft: `5px solid ${getColor(p.sentiment_score || p.sentiment)}` }}>
                            <strong style={{ color: '#9ca3af', fontSize: '12px' }}>{p.city ? p.city.toUpperCase() : 'UNKNOWN'} | {p.source || 'Stream'}</strong>
                            <p style={{ margin: '5px 0', fontSize: '14px' }}>"{p.text || p.title}"</p>
                            <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Score: {(p.sentiment_score || p.sentiment || 0).toFixed(2)}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Interactive Map */}
            <div style={{ width: '70%', height: '100%' }}>
                <MapContainer center={[22.5937, 78.9629]} zoom={3} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; CARTO'
                    />
                    {pulses.map((p, idx) => {
                        // Generate a completely unique tracking key using city name and its specific text length
                        const uniqueKey = `${p.city}-${idx}-${(p.text || p.title || '').length}`;
                        const currentOpacity = idx === 0 ? 1.0 : 0.4; // Make the newest dot shine brightest, fade out older ones!
                        const currentRadius = idx === 0 ? 16 : 10;   // Make the newest data point pulse larger!

                        return (
                            <CircleMarker
                                key={uniqueKey}
                                center={[p.lat, p.lon || p.lng]}
                                radius={currentRadius}
                                fillColor={getColor(p.sentiment_score || p.sentiment)}
                                color="#ffffff"
                                weight={idx === 0 ? 2 : 0.5}
                                fillOpacity={currentOpacity}
                            >
                                <Popup>
                                    <strong>{p.city.toUpperCase()}</strong><br/>
                                    Sentiment: {(p.sentiment_score || p.sentiment || 0).toFixed(2)}<br/>
                                    <em>"{p.text || p.title}"</em>
                                </Popup>
                            </CircleMarker>
                        );
                    })}
                </MapContainer>
            </div>
        </div>
    );
}
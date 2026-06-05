import { useState, useEffect } from 'react';

export default function useCityPulse(url) {
    const [pulses, setPulses] = useState([]);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        const ws = new WebSocket(wss://city-pulse-telemetry-production.up.railway.app/ws);

        ws.onopen = () => setConnected(true);
        ws.onclose = () => setConnected(false);
        
        ws.onmessage = (event) => {
            const rawData = JSON.parse(event.data);
            
            // Handle both streaming events and the baseline snapshot packet
            if (rawData.type === 'event') {
                setPulses((prev) => [rawData.data, ...prev.slice(0, 49)]);
            } else if (rawData.type === 'snapshot') {
                setPulses(rawData.data.reverse());
            }
        };

        return () => ws.close();
    }, [url]);

    return { pulses, connected };
}
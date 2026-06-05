import { useState, useEffect } from 'react';

export default function useCityPulse(url) {
    const [pulses, setPulses] = useState([]);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        // This opens the clean string passed from SentimentMap
        const ws = new WebSocket(url);

        ws.onopen = () => setConnected(true);
        ws.onclose = () => setConnected(false);
        
        ws.onmessage = (event) => {
            const rawData = JSON.parse(event.data);
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
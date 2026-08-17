(() => {
    const journeyWaypoints = [
        { name: "Adairsville, Georgia", lat: 34.3687, lng: -84.9341 },
        { name: "Nashville, Tennessee", lat: 36.1627, lng: -86.7816 },
        { name: "St. Louis, Missouri", lat: 38.6270, lng: -90.1994 },
        { name: "Kansas City, Missouri", lat: 39.0997, lng: -94.5786 },
        { name: "Denver, Colorado", lat: 39.7392, lng: -104.9903 },
        { name: "Salt Lake City, Utah", lat: 40.7608, lng: -111.8910 },
        { name: "Las Vegas, Nevada", lat: 36.1699, lng: -115.1398 },
        { name: "Los Angeles, California", lat: 34.0522, lng: -118.2437 },
        { name: "San Francisco, California", lat: 37.7749, lng: -122.4194 },
        { name: "Portland, Oregon", lat: 45.5152, lng: -122.6784 },
        { name: "Seattle, Washington", lat: 47.6062, lng: -122.3321 },
        { name: "Vancouver, Canada", lat: 49.2827, lng: -123.1207 },
        { name: "Anchorage, Alaska", lat: 61.2181, lng: -149.9003 },
        { name: "Honolulu, Hawaii", lat: 21.3069, lng: -157.8583 },
        { name: "Tokyo, Japan", lat: 35.6762, lng: 139.6503 },
        { name: "Osaka, Japan", lat: 34.6937, lng: 135.5023 },
        { name: "Seoul, South Korea", lat: 37.5665, lng: 126.9780 },
        { name: "Shanghai, China", lat: 31.2304, lng: 121.4737 },
        { name: "Hong Kong", lat: 22.3193, lng: 114.1694 },
        { name: "Singapore", lat: 1.3521, lng: 103.8198 },
        { name: "Bangkok, Thailand", lat: 13.7563, lng: 100.5018 },
        { name: "Mumbai, India", lat: 19.0760, lng: 72.8777 },
        { name: "Dubai, UAE", lat: 25.2048, lng: 55.2708 },
        { name: "Athens, Greece", lat: 37.9838, lng: 23.7275 },
        { name: "Rome, Italy", lat: 41.9028, lng: 12.4964 },
        { name: "Paris, France", lat: 48.8566, lng: 2.3522 },
        { name: "London, United Kingdom", lat: 51.5074, lng: -0.1278 },
        { name: "New York, USA", lat: 40.7128, lng: -74.0060 },
        { name: "Washington, D.C.", lat: 38.9072, lng: -77.0369 },
        { name: "Atlanta, Georgia", lat: 33.7490, lng: -84.3880 },
        { name: "Adairsville, Georgia", lat: 34.3687, lng: -84.9341 }
    ];

    let mapPolyline = null;
    let startMarker = null;
    let currentMarker = null;
    let destinationMarker = null;

    function calculateDistanceKm(a, b) {
        const R = 6371;
        const lat1 = a.lat * Math.PI / 180;
        const lat2 = b.lat * Math.PI / 180;
        const dLat = (b.lat - a.lat) * Math.PI / 180;
        const dLng = (b.lng - a.lng) * Math.PI / 180;
        const h = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
        return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
    }

    const journeySegments = [];
    let fullJourneyDistance = 0;

    for (let i = 0; i < journeyWaypoints.length - 1; i++) {
        const start = journeyWaypoints[i];
        const end = journeyWaypoints[i + 1];
        const distanceKm = calculateDistanceKm(start, end);
        journeySegments.push({ start, end, distanceKm });
        fullJourneyDistance += distanceKm;
    }

    function interpolatePosition(start, end, ratio) {
        ratio = Math.max(0, Math.min(ratio, 1));
        let endLng = end.lng;
        const lngDiff = endLng - start.lng;
        if (lngDiff > 180) endLng -= 360;
        if (lngDiff < -180) endLng += 360;

        const lat = start.lat + (end.lat - start.lat) * ratio;
        let lng = start.lng + (endLng - start.lng) * ratio;
        if (lng > 180) lng -= 360;
        if (lng < -180) lng += 360;
        return { lat, lng };
    }

    function calculateJourneyPosition(totalDistanceKm) {
        const safeDistance = Math.max(0, Number(totalDistanceKm) || 0);
        const completedLaps = Math.floor(safeDistance / fullJourneyDistance);
        let remaining = safeDistance % fullJourneyDistance;
        const completedPoints = [journeyWaypoints[0]];

        for (const segment of journeySegments) {
            if (remaining >= segment.distanceKm) {
                remaining -= segment.distanceKm;
                completedPoints.push(segment.end);
                continue;
            }

            const ratio = segment.distanceKm > 0 ? remaining / segment.distanceKm : 0;
            const currentPosition = interpolatePosition(segment.start, segment.end, ratio);
            completedPoints.push(currentPosition);
            return {
                lap: completedLaps + 1,
                currentPosition,
                next: segment.end,
                completedPoints,
                remainingToNextKm: segment.distanceKm - remaining
            };
        }

        return {
            lap: completedLaps + 1,
            currentPosition: journeyWaypoints[0],
            next: journeyWaypoints[1],
            completedPoints: [journeyWaypoints[0]],
            remainingToNextKm: journeySegments[0].distanceKm
        };
    }

    window.drawMapRoute = function drawMapRoute(totalDistanceKm) {
        if (typeof map === "undefined" || typeof L === "undefined") return;

        const journey = calculateJourneyPosition(totalDistanceKm);

        if (mapPolyline) map.removeLayer(mapPolyline);
        if (startMarker) map.removeLayer(startMarker);
        if (currentMarker) map.removeLayer(currentMarker);
        if (destinationMarker) map.removeLayer(destinationMarker);

        const routeLatLngs = journey.completedPoints.map(p => [p.lat, p.lng]);

        mapPolyline = L.polyline(routeLatLngs, {
            color: '#2c5282',
            weight: 4,
            opacity: 0.85
        }).addTo(map);

        const start = journeyWaypoints[0];
        startMarker = L.marker([start.lat, start.lng])
            .addTo(map)
            .bindPopup('<b>Journey Start</b><br>July 2024<br>' + start.name);

        const currentIcon = L.divIcon({
            className: 'custom-div-icon',
            html: "<div style='background-color:#E11D48;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 0 8px rgba(0,0,0,0.5);'></div>",
            iconSize: [18, 18],
            iconAnchor: [9, 9]
        });

        currentMarker = L.marker(
            [journey.currentPosition.lat, journey.currentPosition.lng],
            { icon: currentIcon }
        ).addTo(map).bindPopup(
            '<b>Current Progress</b>' +
            '<br>Total: ' + Number(totalDistanceKm).toLocaleString(undefined, { maximumFractionDigits: 1 }) + ' km' +
            '<br>World Lap: ' + journey.lap +
            '<br>Heading to: ' + journey.next.name +
            '<br>Distance to next: ' + journey.remainingToNextKm.toFixed(0) + ' km'
        ).openPopup();

        destinationMarker = L.circleMarker([journey.next.lat, journey.next.lng], {
            radius: 6,
            color: '#2c5282',
            fillColor: '#63b3ed',
            fillOpacity: 1,
            weight: 2
        }).addTo(map).bindPopup('<b>Next Destination</b><br>' + journey.next.name);

        const bounds = L.latLngBounds(routeLatLngs);
        bounds.extend([journey.next.lat, journey.next.lng]);
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 6 });
    };

    // Running Logs card: link directly to the public Strava profile.
    function updateRunningLogsCard() {
        const stravaProfileUrl = 'https://www.strava.com/athletes/146407804';
        const cards = document.querySelectorAll('#works .card');

        for (const card of cards) {
            const heading = card.querySelector('h3');
            if (!heading || heading.textContent.trim() !== 'Running Logs') continue;

            const description = card.querySelector('p');
            if (description) {
                description.textContent = 'View my latest running activities and training history on Strava.';
            }

            const link = card.querySelector('a.btn-outline');
            if (link) {
                link.href = stravaProfileUrl;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.removeAttribute('download');
                link.innerHTML = '<i class="fa-brands fa-strava"></i> Open Strava';
                link.setAttribute('aria-label', 'Open Takuya Murami Strava profile');
            }

            break;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateRunningLogsCard, { once: true });
    } else {
        updateRunningLogsCard();
    }
})();

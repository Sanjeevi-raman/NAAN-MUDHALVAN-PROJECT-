/**
 * PocketSmart AI - Location & Geolocation Service
 * Requests browser location permission, updates hidden latitude/longitude form inputs,
 * provides live feedback, and gracefully handles permission denial without crashing.
 */

function initGeolocation(btnId, statusId, latInputId, lonInputId) {
    const btn = document.getElementById(btnId);
    const statusBox = document.getElementById(statusId);
    const latInput = document.getElementById(latInputId);
    const lonInput = document.getElementById(lonInputId);

    if (!btn || !statusBox || !latInput || !lonInput) return;

    btn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            statusBox.innerHTML = `
                <div class="alert alert-warning" style="margin-top:0.75rem;">
                    Geolocation is not supported by your browser. You can still plan without exact nearby venues.
                </div>
            `;
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `Detecting your location...`;
        statusBox.innerHTML = `<p style="font-size:0.85rem;color:var(--neutral-600);margin-top:0.5rem;">Requesting device location permission...</p>`;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                latInput.value = lat;
                lonInput.value = lon;

                btn.disabled = false;
                btn.className = "btn btn-accent btn-sm";
                btn.innerHTML = `✓ Location Enabled (${lat.toFixed(4)}, ${lon.toFixed(4)})`;

                statusBox.innerHTML = `
                    <div class="alert alert-success" style="margin-top:0.75rem;padding:0.6rem 0.9rem;font-size:0.85rem;">
                        <strong>Location acquired!</strong> 60 KM nearby-first ranking activated for party venues & catering.
                    </div>
                `;
            },
            (error) => {
                btn.disabled = false;
                btn.innerHTML = `📍 Retry Location Access`;
                let errorMsg = "Location access is unavailable. Enable location to get nearby recommendations.";
                if (error.code === error.PERMISSION_DENIED) {
                    errorMsg = "Location access is unavailable. Enable location to get nearby recommendations.";
                } else if (error.code === error.POSITION_UNAVAILABLE) {
                    errorMsg = "Location information is currently unavailable from your device.";
                } else if (error.code === error.TIMEOUT) {
                    errorMsg = "Location request timed out. Please try again.";
                }

                statusBox.innerHTML = `
                    <div class="alert alert-warning" style="margin-top:0.75rem;padding:0.6rem 0.9rem;font-size:0.85rem;">
                        ${errorMsg}
                    </div>
                `;
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }
        );
    });
}

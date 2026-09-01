(() => {
    const image = document.getElementById('latest-run-card-image');
    const updated = document.getElementById('latest-run-card-updated');
    if (!image) return;

    async function refreshRunCard() {
        try {
            const response = await fetch(`data/latest_run.json?cache=${Date.now()}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const run = await response.json();
            const version = encodeURIComponent(run.activity_id || run.updated_at || Date.now());
            image.src = `assets/latest_run_card.png?v=${version}`;

            if (updated) {
                const when = run.date || run.updated_at || '';
                updated.textContent = when
                    ? `Latest activity: ${when}`
                    : 'Updated automatically from Garmin';
            }
        } catch (error) {
            console.error('Latest run card refresh error:', error);
        }
    }

    refreshRunCard();
})();

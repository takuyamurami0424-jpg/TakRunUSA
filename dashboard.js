(() => {
    const dashboard = document.getElementById('running-dashboard');
    if (!dashboard) return;

    const loading = document.getElementById('dashboard-loading');
    const errorBox = document.getElementById('dashboard-error');
    const content = document.getElementById('dashboard-content');

    const numberFormat = new Intl.NumberFormat('en-US', {
        maximumFractionDigits: 1
    });

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function formatDate(value) {
        if (!value) return '—';
        const date = new Date(value + 'T00:00:00');
        if (Number.isNaN(date.getTime())) return value;
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(date);
    }

    function renderPB(label, pb) {
        const key = label
            .toLowerCase()
            .replace('half marathon', 'half')
            .replace('marathon', 'marathon')
            .replace('10k', '10k')
            .replace('5k', '5k');

        setText(`pb-${key}-time`, pb ? pb.time : '—');
        setText(`pb-${key}-date`, pb ? formatDate(pb.date) : 'No Garmin result yet');

        const badge = document.getElementById(`pb-${key}-badge`);
        if (!badge) return;

        if (pb && pb.new_pb) {
            badge.textContent = 'NEW PB!';
            badge.classList.add('new-pb');
        } else {
            badge.textContent = pb ? `${pb.distance_km} km activity` : 'Waiting for data';
            badge.classList.remove('new-pb');
        }
    }

    function renderMonthlyMileage(months) {
        const chart = document.getElementById('mileage-chart');
        if (!chart) return;

        chart.innerHTML = '';
        const maxDistance = Math.max(...months.map(m => Number(m.distance_km) || 0), 1);

        months.forEach(month => {
            const column = document.createElement('div');
            column.className = `mileage-column${month.is_current ? ' current' : ''}`;

            const value = document.createElement('div');
            value.className = 'mileage-value';
            value.textContent = `${numberFormat.format(month.distance_km)} km`;

            const wrap = document.createElement('div');
            wrap.className = 'mileage-bar-wrap';

            const bar = document.createElement('div');
            bar.className = 'mileage-bar';
            bar.style.height = `${Math.max(2, (month.distance_km / maxDistance) * 100)}%`;
            bar.title = `${month.key}: ${numberFormat.format(month.distance_km)} km`;

            const label = document.createElement('div');
            label.className = 'mileage-label';
            label.textContent = month.label;

            wrap.appendChild(bar);
            column.appendChild(value);
            column.appendChild(wrap);
            column.appendChild(label);
            chart.appendChild(column);
        });
    }

    async function renderRace() {
        const raceName = document.getElementById('next-race-name');
        const raceMeta = document.getElementById('next-race-meta');
        const raceDays = document.getElementById('next-race-days');

        if (!raceName || !raceMeta || !raceDays) return;

        try {
            const response = await fetch(`data/next_race.json?cache=${Date.now()}`);
            if (!response.ok) throw new Error('Race config not found');

            const race = await response.json();
            if (!race.date || !race.name) throw new Error('Race config incomplete');

            const raceDate = new Date(`${race.date}T12:00:00`);
            const now = new Date();
            const days = Math.max(0, Math.ceil((raceDate - now) / 86400000));

            raceName.textContent = race.name;
            raceMeta.textContent = [
                formatDate(race.date),
                race.goal ? `Goal: ${race.goal}` : null,
                race.location || null
            ].filter(Boolean).join(' · ');
            raceDays.textContent = days.toLocaleString();
        } catch (error) {
            raceName.textContent = 'Next race not set';
            raceMeta.textContent = 'Add the next confirmed race when you are ready.';
            raceDays.textContent = '—';
        }
    }

    async function loadDashboard() {
        try {
            const response = await fetch(`data/dashboard.json?cache=${Date.now()}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            const summary = data.summary || {};

            setText('dash-month', numberFormat.format(summary.this_month_km || 0));
            setText('dash-year', numberFormat.format(summary.this_year_km || 0));
            setText('dash-week', numberFormat.format(summary.last_7_days_km || 0));
            setText('dash-total', numberFormat.format(summary.total_km || 0));

            renderPB('5K', data.pbs?.['5K']);
            renderPB('10K', data.pbs?.['10K']);
            renderPB('Half Marathon', data.pbs?.['Half Marathon']);
            renderPB('Marathon', data.pbs?.['Marathon']);
            renderMonthlyMileage(data.monthly_mileage || []);
            await renderRace();

            loading?.classList.add('hidden');
            errorBox?.classList.add('hidden');
            content?.classList.remove('hidden');
        } catch (error) {
            console.error('Running dashboard load error:', error);
            loading?.classList.add('hidden');
            errorBox?.classList.remove('hidden');
        }
    }

    loadDashboard();
})();

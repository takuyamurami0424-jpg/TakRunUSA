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
        if (!chart || !months.length) return;

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

    function renderTrainingTrend(trend) {
        const current = trend?.current || {};
        const weekly = trend?.weekly || [];

        setText('trend-distance', `${numberFormat.format(current.distance_km || 0)} km`);
        setText('trend-runs', Number(current.run_count || 0).toLocaleString());
        setText('trend-pace', current.avg_pace_per_km ? `${current.avg_pace_per_km}/km` : '—');
        setText('trend-hr', current.avg_hr != null ? `${current.avg_hr} bpm` : '—');
        setText('trend-longest', `${numberFormat.format(current.longest_run_km || 0)} km`);

        const change = document.getElementById('trend-change');
        if (change) {
            change.classList.remove('trend-up', 'trend-down', 'trend-steady');

            if (trend?.distance_change_pct == null) {
                change.textContent = 'No prior baseline';
            } else {
                const pct = Number(trend.distance_change_pct);
                const sign = pct > 0 ? '+' : '';
                change.textContent = `${sign}${pct.toFixed(1)}% vs prior 4 weeks`;

                if (trend.direction === 'up') change.classList.add('trend-up');
                else if (trend.direction === 'down') change.classList.add('trend-down');
                else change.classList.add('trend-steady');
            }
        }

        const chart = document.getElementById('trend-weekly-chart');
        if (!chart || !weekly.length) return;

        chart.innerHTML = '';
        const maxDistance = Math.max(...weekly.map(w => Number(w.distance_km) || 0), 1);

        weekly.forEach(week => {
            const item = document.createElement('div');
            item.className = 'trend-week';

            const value = document.createElement('div');
            value.className = 'trend-week-value';
            value.textContent = `${numberFormat.format(week.distance_km)} km`;

            const barWrap = document.createElement('div');
            barWrap.className = 'trend-week-bar-wrap';

            const bar = document.createElement('div');
            bar.className = 'trend-week-bar';
            bar.style.height = `${Math.max(4, (week.distance_km / maxDistance) * 100)}%`;
            bar.title = `${week.date_range}: ${numberFormat.format(week.distance_km)} km · ${week.run_count} runs`;

            const label = document.createElement('div');
            label.className = 'trend-week-label';
            label.innerHTML = `<strong>${week.label}</strong><span>${week.date_range}</span>`;

            barWrap.appendChild(bar);
            item.appendChild(value);
            item.appendChild(barWrap);
            item.appendChild(label);
            chart.appendChild(item);
        });
    }

    async function renderRace() {
        const raceName = document.getElementById('next-race-name');
        const raceMeta = document.getElementById('next-race-meta');
        const raceDays = document.getElementById('next-race-days');
        const raceGoal = document.getElementById('next-race-goal');

        if (!raceName || !raceMeta || !raceDays) return;

        try {
            const response = await fetch(`data/next_race.json?cache=${Date.now()}`);
            if (!response.ok) throw new Error('Race config not found');

            const race = await response.json();
            if (race.configured === false || !race.date || !race.name) {
                throw new Error('Race config incomplete');
            }

            const raceDate = new Date(`${race.date}T12:00:00`);
            const now = new Date();
            const rawDays = Math.ceil((raceDate - now) / 86400000);
            const days = Math.max(0, rawDays);

            raceName.textContent = race.name;
            raceMeta.textContent = [
                formatDate(race.date),
                race.location || null
            ].filter(Boolean).join(' · ');

            if (raceGoal) {
                raceGoal.textContent = race.goal ? `Goal: ${race.goal}` : 'Goal not set';
            }

            raceDays.textContent = days.toLocaleString();

            if (rawDays < 0) {
                raceDays.textContent = '0';
                raceMeta.textContent += ' · Race completed';
            }
        } catch (error) {
            raceName.textContent = 'Next race not set';
            raceMeta.textContent = 'Edit data/next_race.json when your next race is confirmed.';
            if (raceGoal) raceGoal.textContent = 'Goal not set';
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
            renderTrainingTrend(data.training_trend || {});
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

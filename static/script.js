let voteChartInstance = null;

function submitVote(subject_id) {
    const selectedOption = document.querySelector('input[name="option"]:checked');

    if (!selectedOption) {
        alert("Velg et alternativ.");
        return;
    }

    fetch('/vote', {
        method: 'POST',
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
            subject_id,
            option_id: selectedOption.value
        })
    })
        .then(response => response.json())
        .then(data => updateVoteChart(data));
}

function updateVoteChart(votesData) {
    const list = votesData.options || votesData.subjects || [];
    const labels = list.map(s => s.label || s.title);
    const counts = list.map(s => s.vote_count);

    document.getElementById('vote-count').textContent = votesData.total;

    if (!voteChartInstance) {
        const ctx = document.getElementById('voteChart').getContext('2d');
        voteChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Stemmer',
                    data: counts,
                    backgroundColor: 'rgba(75, 192, 192, 0.4)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: { scales: { y: { beginAtZero: true } } }
        });
    } else {
        voteChartInstance.data.labels = labels;
        voteChartInstance.data.datasets[0].data = counts;
        voteChartInstance.update();
    }
}

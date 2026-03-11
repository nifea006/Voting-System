let voteChart;

function vote(form) {
    const subject = form.elements.subject.value;
    fetch('/vote', {
        method: 'POST',
        body: new URLSearchParams({ subject })
    })
        .then(response => response.json())
        .then(data => {
            updateVoteChart(data);
        });
}

function updateVoteChart(votes) {
    document.getElementById('vote-count').textContent = votes.total;

    if (!voteChart) {
        const ctx = document.getElementById('voteChart').getContext('2d');
        voteChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(votes.subjects),
                datasets: [{
                    label: 'Votes',
                    data: Object.values(votes.subjects),
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } else {
        voteChart.data.labels = Object.keys(votes.subjects);
        voteChart.data.datasets[0].data = Object.values(votes.subjects);
        voteChart.update();
    }
}
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
        .then(data => {
            if (data.status !== 'success') {
                alert(data.message);
                return;
            }
            showResultsAfterVote();
            updateVoteChart(data);
        });
}

function updateVoteChart(votesData) {
    const list = votesData.options || votesData.subjects || [];
    const labels = list.map(option => option.label || option.title);
    const counts = list.map(option => option.vote_count);

    document.getElementById('vote-count').textContent = votesData.total;

    if (!voteChartInstance) {
        const ctx = document.getElementById('voteChart').getContext('2d');
        voteChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: "Stemmer",
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

function showResultsAfterVote() {
    const chartContainer = document.getElementById('vote-chart-container');
    const totalVotesRow = document.getElementById('total-votes-row');
    const submitButton = document.getElementById('vote-submit');

    if (chartContainer) {
        chartContainer.hidden = false;
    }
    if (totalVotesRow) {
        totalVotesRow.hidden = false;
    }
    if (submitButton) {
        submitButton.textContent = 'Endre stemme';
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const voteDataEl = document.getElementById('vote-data');
    if (!voteDataEl) {
        return;
    }

    const hasVoted = voteDataEl.dataset.hasVoted === '1';
    let initialVoteData = null;
    try {
        initialVoteData = JSON.parse(voteDataEl.dataset.initialVote || '{}');
    } catch (error) {
        initialVoteData = null;
    }

    if (hasVoted) {
        showResultsAfterVote();
        if (initialVoteData) {
            updateVoteChart(initialVoteData);
        }
    }
});

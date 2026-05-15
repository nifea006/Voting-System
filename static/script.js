let voteChartInstance = null;
let currentVoteData = null;
let currentChartType = 'bar';
let currentChartPalette = {
    key: null,
    colors: []
};

function generateChartColors(count) {
    if (count <= 0) {
        return [];
    }

    const startShade = Math.floor(Math.random() * 360);
    const shadeStep = 137.508;
    const colors = [];

    for (let i = 0; i < count; i += 1) {
        const shade = (startShade + (i * shadeStep)) % 360;
        const saturation = 65 + ((i * 7) % 15);
        const lightness = 48 + ((i * 5) % 10);
        colors.push(`hsl(${Math.round(shade)} ${saturation}% ${lightness}%)`);
    }

    return colors;
}

function getChartColors(labels) {
    const paletteKey = labels.join("||");
    if (currentChartPalette.key === paletteKey && currentChartPalette.colors.length === labels.length) {
        return currentChartPalette.colors;
    }

    const colors = generateChartColors(labels.length);
    currentChartPalette = {
        key: paletteKey,
        colors
    };

    return colors;
}

function getChartOptions(chartType) {
    const integerScale = {
        beginAtZero: true,
        ticks: {
            precision: 0,
            stepSize: 1
        }
    };

    if (chartType === 'radar' || chartType === 'polarArea') {
        return {
            scales: {
                r: integerScale
            }
        };
    }

    if (chartType === 'doughnut') {
        return {};
    }

    return {
        scales: {
            y: integerScale
        }
    };
}

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

            currentVoteData = data;
            showResultsAfterVote();
            updateVoteChart(currentVoteData);
        });
}

function updateVoteChart(votesData = currentVoteData, selectedType = null) {
    votesData = votesData || currentVoteData;
    if (!votesData) return;

    currentVoteData = votesData;
    currentChartType = selectedType || currentChartType;
    console.log("currentChartType:", currentChartType, "selectedType:", selectedType)

    const list = votesData.options || votesData.subjects || [];
    const labels = list.map(option => option.label || option.title);
    const counts = list.map(option => option.vote_count);
    const chartType = currentChartType;
    const backgroundColors = getChartColors(labels);

    document.getElementById('vote-count').textContent = votesData.total;

    if (!voteChartInstance) {
        const ctx = document.getElementById('voteChart').getContext('2d');
        voteChartInstance = new Chart(ctx, {
            type: chartType,
            data: {
                labels,
                datasets: [{
                    label: "Stemmer",
                    data: counts,
                    backgroundColor: backgroundColors,
                    borderColor: "#1f2937",
                    borderWidth: 1,
                    hoverOffset: chartType === 'doughnut' ? 4 : 0
                }]
            },
            options: getChartOptions(chartType)
        });
    } else {
        voteChartInstance.config.type = chartType;
        voteChartInstance.data.labels = labels;
        voteChartInstance.data.datasets[0].data = counts;
        voteChartInstance.data.datasets[0].backgroundColor = backgroundColors;
        voteChartInstance.data.datasets[0].hoverOffset = chartType === 'doughnut' ? 4 : 0;
        voteChartInstance.options = getChartOptions(chartType);
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
            currentVoteData = initialVoteData;
            updateVoteChart(currentVoteData);
        }
    }
});

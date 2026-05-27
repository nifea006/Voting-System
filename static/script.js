let voteChartInstance = null;
let currentVoteData = null;
let currentChartType = "bar";
let allowedChartTypes = ["bar", "doughnut", "line", "polarArea", "radar"];

const CHART_TYPE_WITHOUT_AXIS = "doughnut";
const RADIAL_CHART_TYPES = new Set(["radar", "polarArea"]);
const VOTE_COUNT_SELECTOR = "[data-vote-count]";

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

    for (let index = 0; index < count; index += 1) {
        const shade = (startShade + (index * shadeStep)) % 360;
        const saturation = 65 + ((index * 7) % 15);
        const lightness = 48 + ((index * 5) % 10);

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
    currentChartPalette = { key: paletteKey, colors };
    return colors;
}

function getChartOptions(chartType) {
    if (chartType === CHART_TYPE_WITHOUT_AXIS) {
        return {};
    }

    const axis = RADIAL_CHART_TYPES.has(chartType) ? "r" : "y";

    return {
        scales: {
            [axis]: {
                beginAtZero: true,
                ticks: {
                    precision: 0,
                    stepSize: 1
                }
            }
        }
    };
}

function getVoteChartDataset(counts, backgroundColors, chartType) {
    return {
        label: "Stemmer",
        data: counts,
        backgroundColor: backgroundColors,
        borderColor: "#1f2937",
        borderWidth: 1,
        hoverOffset: chartType === CHART_TYPE_WITHOUT_AXIS ? 4 : 0
    };
}

function setVoteCount(totalVotes) {
    document.querySelectorAll(VOTE_COUNT_SELECTOR).forEach((element) => {
        element.textContent = totalVotes;
    });
}

function showResultsAfterVote() {
    const chartContainer = document.getElementById("vote-chart-container");
    const totalVotesRow = document.getElementById("total-votes-row");
    const submitButton = document.getElementById("vote-submit");
    const voteForm = document.querySelector("[data-vote-form]");
    const allowVoteChanges = voteForm?.dataset.allowVoteChanges === "1";

    if (chartContainer) {
        chartContainer.hidden = false;
    }

    if (totalVotesRow) {
        totalVotesRow.hidden = false;
    }

    if (submitButton) {
        submitButton.textContent = allowVoteChanges ? "Endre stemme" : "Stem registrert";
        submitButton.disabled = !allowVoteChanges;
    }

    if (!allowVoteChanges && voteForm) {
        voteForm.querySelectorAll("input[name='option']").forEach((input) => {
            input.disabled = true;
        });
    }
}

function renderVoterLists(voterLists = []) {
    const voterListSection = document.getElementById("voter-list-section");
    const voterListContainer = document.getElementById("voter-list-container");

    if (!voterListSection || !voterListContainer) {
        return;
    }

    voterListContainer.innerHTML = "";

    voterLists.forEach((option) => {
        const card = document.createElement("article");
        card.className = "voter-list-card";

        const title = document.createElement("h4");
        title.textContent = option.label;
        card.appendChild(title);

        if (option.voters && option.voters.length > 0) {
            const list = document.createElement("ul");

            option.voters.forEach((voter) => {
                const item = document.createElement("li");
                item.textContent = voter;
                list.appendChild(item);
            });

            card.appendChild(list);
        } else {
            const emptyState = document.createElement("p");
            emptyState.textContent = "Ingen stemmer ennå.";
            card.appendChild(emptyState);
        }

        voterListContainer.appendChild(card);
    });

    voterListSection.hidden = false;
}

function updateVoteChart(votesData = currentVoteData, selectedType = null) {
    const resolvedVoteData = votesData || currentVoteData;

    if (!resolvedVoteData) {
        return;
    }

    currentVoteData = resolvedVoteData;
    if (selectedType && allowedChartTypes.includes(selectedType)) {
        currentChartType = selectedType;
    } else if (!allowedChartTypes.includes(currentChartType)) {
        currentChartType = allowedChartTypes[0] || "bar";
    }

    const list = resolvedVoteData.options || resolvedVoteData.subjects || [];
    const labels = list.map((option) => option.label || option.title);
    const counts = list.map((option) => option.vote_count);
    const backgroundColors = getChartColors(labels);
    const dataset = getVoteChartDataset(counts, backgroundColors, currentChartType);

    setVoteCount(resolvedVoteData.total);

    if (!voteChartInstance) {
        const chartElement = document.getElementById("voteChart");

        if (!chartElement) {
            return;
        }

        voteChartInstance = new Chart(chartElement.getContext("2d"), {
            type: currentChartType,
            data: {
                labels,
                datasets: [dataset]
            },
            options: getChartOptions(currentChartType)
        });

        return;
    }

    voteChartInstance.config.type = currentChartType;
    voteChartInstance.data.labels = labels;
    voteChartInstance.data.datasets[0] = dataset;
    voteChartInstance.options = getChartOptions(currentChartType);
    voteChartInstance.update();
}

function submitVote(subjectId) {
    const selectedOption = document.querySelector("input[name='option']:checked");

    if (!selectedOption) {
        alert("Velg et alternativ.");
        return;
    }

    fetch("/vote", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
            subject_id: subjectId,
            option_id: selectedOption.value
        })
    })
        .then(async (response) => {
            let data = null;

            try {
                data = await response.json();
            } catch (error) {
                if (response.status === 401) {
                    window.location.href = "/login";
                    return null;
                }

                throw new Error("Kunne ikke registrere stemmen. Prøv igjen.");
            }

            if (response.status === 401) {
                window.location.href = "/login";
                return null;
            }

            if (!response.ok) {
                throw new Error(data?.message || "Kunne ikke registrere stemmen. Prøv igjen.");
            }

            return data;
        })
        .then((data) => {
            if (!data) {
                return;
            }

            if (data.status !== "success") {
                alert(data.message);
                return;
            }

            currentVoteData = data;
            showResultsAfterVote();
            updateVoteChart(currentVoteData);

            if (data.show_voter_lists) {
                renderVoterLists(data.voter_lists || []);
            }
        })
        .catch((error) => {
            alert(error.message || "Kunne ikke registrere stemmen. Prøv igjen.");
        });
}

function createOptionRow(value = "") {
    const row = document.createElement("div");
    row.className = "option-row";

    const input = document.createElement("input");
    input.type = "text";
    input.name = "options";
    input.value = value;
    input.required = true;

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "remove-option";
    removeButton.textContent = "-";

    row.append(input, removeButton);
    return row;
}

function updateOptionRemoveButtons(optionsContainer) {
    const rows = optionsContainer.querySelectorAll(".option-row");
    const canRemove = rows.length > 2;

    rows.forEach((row) => {
        const button = row.querySelector(".remove-option");

        if (!button) {
            return;
        }

        button.disabled = !canRemove;
        button.style.visibility = canRemove ? "visible" : "hidden";
    });
}

function syncChartToggleButton(button, checkbox) {
    button.classList.toggle("active", checkbox.checked);
}

function initChartTogglePicker() {
    const chartToggleGroup = document.getElementById("chart-toggle-group");

    if (!chartToggleGroup) {
        return;
    }

    chartToggleGroup.addEventListener("click", (event) => {
        const button = event.target.closest("[data-chart-toggle]");

        if (!button) {
            return;
        }

        const chartType = button.dataset.chartToggle;
        const checkbox = chartToggleGroup.querySelector(
            `input[name="allowed_chart_types"][value="${chartType}"]`
        );

        if (!checkbox) {
            return;
        }

        const checkedBoxes = chartToggleGroup.querySelectorAll("input[name='allowed_chart_types']:checked");
        const isTryingToDisableLast = checkbox.checked && checkedBoxes.length === 1;

        if (isTryingToDisableLast) {
            return;
        }

        checkbox.checked = !checkbox.checked;
        syncChartToggleButton(button, checkbox);
    });

    chartToggleGroup
        .querySelectorAll("[data-chart-toggle]")
        .forEach((button) => {
            const chartType = button.dataset.chartToggle;
            const checkbox = chartToggleGroup.querySelector(
                `input[name="allowed_chart_types"][value="${chartType}"]`
            );

            if (checkbox) {
                syncChartToggleButton(button, checkbox);
            }
        });
}

function initCreateSubjectForm() {
    const addOptionButton = document.getElementById("add-option");
    const optionsContainer = document.getElementById("options-container");

    if (!addOptionButton || !optionsContainer) {
        return;
    }

    addOptionButton.addEventListener("click", () => {
        optionsContainer.appendChild(createOptionRow());
        updateOptionRemoveButtons(optionsContainer);
    });

    optionsContainer.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-option");

        if (!removeButton) {
            return;
        }

        const row = removeButton.closest(".option-row");

        if (!row) {
            return;
        }

        row.remove();
        updateOptionRemoveButtons(optionsContainer);
    });

    updateOptionRemoveButtons(optionsContainer);
}

function initDeleteConfirmations() {
    document.querySelectorAll("form[data-confirm-message]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirmMessage;

            if (message && !window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
}

function initVotePage() {
    const voteDataElement = document.getElementById("vote-data");
    const voteForm = document.querySelector("[data-vote-form]");
    const chartSwitcher = document.getElementById("selectChartType");

    if (!voteDataElement || !voteForm) {
        return;
    }

    const hasVoted = voteDataElement.dataset.hasVoted === "1";
    let initialVoteData = null;
    let parsedAllowedChartTypes = [];

    try {
        initialVoteData = JSON.parse(voteDataElement.dataset.initialVote || "{}");
    } catch (error) {
        initialVoteData = null;
    }

    try {
        parsedAllowedChartTypes = JSON.parse(voteDataElement.dataset.allowedChartTypes || "[]");
    } catch (error) {
        parsedAllowedChartTypes = [];
    }

    if (Array.isArray(parsedAllowedChartTypes) && parsedAllowedChartTypes.length > 0) {
        allowedChartTypes = parsedAllowedChartTypes;
        currentChartType = allowedChartTypes[0];
    }

    voteForm.addEventListener("submit", (event) => {
        event.preventDefault();
        submitVote(voteForm.dataset.subjectId);
    });

    if (chartSwitcher) {
        chartSwitcher.addEventListener("click", (event) => {
            const button = event.target.closest("[data-chart-type]");

            if (!button) {
                return;
            }

            updateVoteChart(null, button.dataset.chartType);
        });
    }

    if (!hasVoted || !initialVoteData) {
        return;
    }

    showResultsAfterVote();
    currentVoteData = initialVoteData;
    updateVoteChart(currentVoteData);
}

document.addEventListener("DOMContentLoaded", () => {
    initVotePage();
    initCreateSubjectForm();
    initChartTogglePicker();
    initDeleteConfirmations();
});

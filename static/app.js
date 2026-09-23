const form = document.querySelector("#predictionForm");
const submitButton = document.querySelector("#submitButton");
const fillExampleButton = document.querySelector("#fillExample");

const states = {
    empty: document.querySelector("#emptyState"),
    loading: document.querySelector("#loadingState"),
    success: document.querySelector("#successState"),
    error: document.querySelector("#errorState"),
};

const scoreValue = document.querySelector("#scoreValue");
const scoreMeter = document.querySelector("#scoreMeter");
const scoreMessage = document.querySelector("#scoreMessage");
const errorMessage = document.querySelector("#errorMessage");
const apiEndpointLabel = document.querySelector("#apiEndpointLabel");

const configuredApiBase = document.querySelector("meta[name='api-base-url']")?.content.trim();
const isFastApiOrigin = window.location.port === "8000";
const API_BASE = configuredApiBase || (isFastApiOrigin ? "" : "http://127.0.0.1:8000");
const PREDICT_URL = `${API_BASE}/predict`;

apiEndpointLabel.textContent = PREDICT_URL;

const exampleData = {
    age: 21,
    gender: "Male",
    country: "India",
    academic_level: "Undergraduate",
    most_used_platform: "Instagram",
    purpose_of_use: "Entertainment",
    average_daily_usage_hours: 5.0,
    daily_unlocks: 120,
    study_hours: 3.0,
    physical_activity_hours: 1.0,
    sleep_hours_per_night: 7.0,
    stress_level: "Medium",
};

function showState(activeState) {
    Object.values(states).forEach((state) => state.classList.add("hidden"));
    states[activeState].classList.remove("hidden");
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    submitButton.classList.toggle("is-loading", isLoading);
    submitButton.querySelector(".button-text").textContent = isLoading ? "Predicting" : "Predict Score";
}

function collectPayload() {
    const formData = new FormData(form);

    return {
        age: Number(formData.get("age")),
        gender: formData.get("gender"),
        country: String(formData.get("country")).trim(),
        academic_level: formData.get("academic_level"),
        most_used_platform: formData.get("most_used_platform"),
        purpose_of_use: formData.get("purpose_of_use"),
        average_daily_usage_hours: Number(formData.get("average_daily_usage_hours")),
        daily_unlocks: Number(formData.get("daily_unlocks")),
        study_hours: Number(formData.get("study_hours")),
        physical_activity_hours: Number(formData.get("physical_activity_hours")),
        sleep_hours_per_night: Number(formData.get("sleep_hours_per_night")),
        stress_level: formData.get("stress_level"),
    };
}

function explainScore(score) {
    if (score < 4) {
        return "The score is on the lower side. This may indicate that the entered lifestyle and stress factors need attention.";
    }

    if (score < 7) {
        return "The score is in a moderate range. Balanced sleep, study routine, activity, and controlled screen time may help improve it.";
    }

    return "The score is in a stronger range. The entered habits suggest comparatively better mental health indicators.";
}

function getErrorText(errorPayload) {
    if (Array.isArray(errorPayload?.detail)) {
        return errorPayload.detail
            .map((item) => {
                const field = item.loc?.slice(1).join(" ") || "Field";
                return `${field}: ${item.msg}`;
            })
            .join(" ");
    }

    if (typeof errorPayload?.detail === "string") {
        return errorPayload.detail;
    }

    return "Please check the form values and try again.";
}

async function readResponseBody(response) {
    const text = await response.text();

    if (!text) {
        return null;
    }

    try {
        return JSON.parse(text);
    } catch {
        return { detail: text };
    }
}

function renderScore(prediction) {
    const score = Number(prediction);
    const boundedScore = Math.max(0, Math.min(10, score));

    scoreValue.textContent = score.toFixed(2);
    scoreMeter.style.width = `${boundedScore * 10}%`;
    scoreMessage.textContent = explainScore(score);
    showState("success");
}

fillExampleButton.addEventListener("click", () => {
    Object.entries(exampleData).forEach(([key, value]) => {
        const field = form.elements[key];
        if (field) {
            field.value = value;
        }
    });
    showState("empty");
});

form.addEventListener("reset", () => {
    setTimeout(() => showState("empty"), 0);
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!form.reportValidity()) {
        return;
    }

    setLoading(true);
    showState("loading");

    try {
        const response = await fetch(PREDICT_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(collectPayload()),
        });

        const result = await readResponseBody(response);

        if (!response.ok) {
            throw new Error(getErrorText(result));
        }

        if (!result || typeof result.prediction === "undefined") {
            throw new Error("The API did not return a prediction. Check that the FastAPI backend is running on port 8000.");
        }

        renderScore(result.prediction);
    } catch (error) {
        errorMessage.textContent = error.message || "The API request failed. Please make sure the server is running.";
        showState("error");
    } finally {
        setLoading(false);
    }
});

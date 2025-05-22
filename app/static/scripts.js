// API Base URL - Change this if your API is hosted on a different domain or port
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Tab functionality
function openTab(tabId) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }

    // Deactivate all tab buttons
    const tabButtons = document.getElementsByClassName('tab-btn');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    // Show the selected tab content and activate the button
    document.getElementById(tabId).classList.add('active');
    const activeButton = document.querySelector(`[onclick="openTab('${tabId}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
}

// Helper functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = 'Loading...';
    element.classList.add('loading-text');
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    element.classList.remove('loading-text');
}

function displayResponse(elementId, data) {
    const element = document.getElementById(elementId);
    element.innerHTML = typeof data === 'object' ?
        JSON.stringify(data, null, 2) :
        data.toString();
}

function displayError(elementId, error) {
    const element = document.getElementById(elementId);
    element.innerHTML = `Error: ${error.message || error}`;
    element.style.color = '#e74c3c';
}

function resetResponseStyles(elementId) {
    const element = document.getElementById(elementId);
    element.style.color = '';
}

async function makeApiRequest(endpoint, method, payload) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: method !== 'GET' ? JSON.stringify(payload) : undefined
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || 'An error occurred');
    }

    return data;
}

// Knowledge Base API Functions
async function addDocuments() {
    const responseElementId = 'add-documents-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        // Parse the payload from the textarea
        // IMPORTANT: Ensure document IDs in the payload are either unsigned integers or UUIDs.
        // For example: "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479" or "id": 123
        const payloadStr = document.getElementById('add-documents-payload').value;
        const payload = JSON.parse(payloadStr);

        // Make the API request
        const response = await makeApiRequest('/kb/documents', 'POST', payload);

        // Display the response
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

async function queryKnowledgeBase() {
    const responseElementId = 'query-kb-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        // Parse the payload from the textarea
        const payloadStr = document.getElementById('query-kb-payload').value;
        const payload = JSON.parse(payloadStr);

        // Make the API request
        const response = await makeApiRequest('/kb/query', 'POST', payload);

        // Display the response
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

// RAG API Functions
async function ragGenerate() {
    const responseElementId = 'rag-generate-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        // Parse the payload from the textarea
        const payloadStr = document.getElementById('rag-generate-payload').value;
        const payload = JSON.parse(payloadStr);

        // Make the API request
        const response = await makeApiRequest('/rag/generate', 'POST', payload);

        // Display the response
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

// Agent API Functions
async function agentAnswer() {
    const responseElementId = 'agent-answer-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        // Parse the payload from the textarea
        const payloadStr = document.getElementById('agent-answer-payload').value;
        const payload = JSON.parse(payloadStr);

        // Make the API request
        const response = await makeApiRequest('/agent/answer', 'POST', payload);

        // Display the response
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

// Add event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Format code in textareas
    const textareas = document.querySelectorAll('.code-editor');
    textareas.forEach(textarea => {
        const value = textarea.value;
        try {
            // Try to parse and reformat JSON
            const formattedValue = JSON.stringify(JSON.parse(value), null, 2);
            textarea.value = formattedValue;
        } catch (e) {
            // If not valid JSON, leave as is
            console.warn('Could not format textarea content as JSON', e);
        }
    });
});

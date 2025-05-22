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

// Store the ID of the last successfully uploaded document in the Full API Flow
let currentUploadedDocId = null;

async function makeApiRequest(endpoint, method, payload, isFormData = false) {
    const headers = {};
    let bodyToSend;

    if (isFormData) {
        bodyToSend = payload; // payload is already FormData
        // Do not set Content-Type for FormData; the browser will do it with the correct boundary.
    } else if (payload && (method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE')) { // DELETE can also have a body
        headers['Content-Type'] = 'application/json';
        bodyToSend = JSON.stringify(payload);
    } else {
        bodyToSend = undefined;
    }

    const requestOptions = {
        method: method,
        headers: headers,
    };

    if (method !== 'GET' && method !== 'HEAD') {
        requestOptions.body = bodyToSend;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);

    let data;
    const responseContentType = response.headers.get("content-type");

    if (response.status === 204) { // No Content
        data = { success: true, status: response.status, message: "Operation successful (No Content)" };
    } else if (responseContentType && responseContentType.includes("application/json")) {
        data = await response.json();
    } else {
        const textResponse = await response.text();
        if (response.ok) {
            data = { success: true, status: response.status, message: textResponse || "Operation successful" };
        } else {
            // Attempt to parse as JSON if it's an error, FastAPI often returns JSON errors
            try {
                data = JSON.parse(textResponse);
            } catch (e) {
                data = { detail: textResponse || `HTTP error ${response.status}` };
            }
        }
    }

    if (!response.ok) {
        let errorMessage = `An error occurred: ${response.statusText} (${response.status})`; // Default
        if (data) {
            if (data.detail) {
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail) && data.detail.length > 0 && data.detail[0].msg) {
                    errorMessage = data.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
                } else {
                    try {
                        errorMessage = JSON.stringify(data.detail);
                    } catch (e) { /* ignore if not stringifiable */ }
                }
            } else if (data.message && typeof data.message === 'string') {
                errorMessage = data.message;
            } else if (data.error && data.error.message && typeof data.error.message === 'string') {
                errorMessage = data.error.message;
            } else if (typeof data === 'string') {
                errorMessage = data;
            }
        }
        throw new Error(errorMessage);
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

// Full API Flow Functions
async function uploadDocumentFlow() {
    const fileInput = document.getElementById('upload-file-flow');
    const responseElementId = 'upload-document-flow-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);
    currentUploadedDocId = null; // Reset previous ID
    document.getElementById('view-doc-id-flow').value = '';
    document.getElementById('delete-doc-id-flow').value = '';


    if (!fileInput.files || fileInput.files.length === 0) {
        displayError(responseElementId, 'Please select a file to upload.');
        hideLoading(responseElementId);
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await makeApiRequest('/kb/upload', 'POST', formData, true); // true for isFormData
        if (response && response.data && response.data.document_id) {
            currentUploadedDocId = response.data.document_id;
            document.getElementById('view-doc-id-flow').value = currentUploadedDocId;
            document.getElementById('delete-doc-id-flow').value = currentUploadedDocId;
            const successData = {
                message: `File uploaded successfully. Document ID: ${currentUploadedDocId}`,
                originalResponse: response
            };
            displayResponse(responseElementId, successData);
        } else {
            displayResponse(responseElementId, response); // Fallback for different success structures
        }
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

async function viewDocumentFlow() {
    const docId = document.getElementById('view-doc-id-flow').value;
    const responseElementId = 'view-document-flow-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    if (!docId) {
        displayError(responseElementId, 'Please enter a Document ID or upload a document first.');
        hideLoading(responseElementId);
        return;
    }

    try {
        const response = await makeApiRequest(`/kb/documents/${docId}`, 'GET');
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

async function queryKnowledgeBaseFlow() {
    const responseElementId = 'query-kb-flow-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        const payloadStr = document.getElementById('query-kb-flow-payload').value;
        const payload = JSON.parse(payloadStr);
        const response = await makeApiRequest('/kb/query', 'POST', payload);
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

async function ragGenerateFlow() {
    const responseElementId = 'rag-generate-flow-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        const payloadStr = document.getElementById('rag-generate-flow-payload').value;
        const payload = JSON.parse(payloadStr);
        const response = await makeApiRequest('/rag/generate', 'POST', payload);
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

async function agentAnswerFlow() {
    const responseElementId = 'agent-answer-flow-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    try {
        const payloadStr = document.getElementById('agent-answer-flow-payload').value;
        const payload = JSON.parse(payloadStr);
        const response = await makeApiRequest('/agent/answer', 'POST', payload);
        displayResponse(responseElementId, response);
    } catch (error) {
        displayError(responseElementId, error);
    } finally {
        hideLoading(responseElementId);
    }
}

async function deleteDocumentFlow() {
    const docId = document.getElementById('delete-doc-id-flow').value;
    const responseElementId = 'delete-document-flow-response';
    resetResponseStyles(responseElementId);
    showLoading(responseElementId);

    if (!docId) {
        displayError(responseElementId, 'Please enter a Document ID or upload a document first.');
        hideLoading(responseElementId);
        return;
    }

    try {
        const response = await makeApiRequest(`/kb/documents/${docId}`, 'DELETE', null);
        displayResponse(responseElementId, response);
        if (response && response.success) {
            document.getElementById('delete-doc-id-flow').value = '';
            if (currentUploadedDocId === docId) {
                currentUploadedDocId = null;
                document.getElementById('view-doc-id-flow').value = '';
            }
        }
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

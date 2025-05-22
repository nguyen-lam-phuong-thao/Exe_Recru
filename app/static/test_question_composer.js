document.addEventListener('DOMContentLoaded', () => {
    const userInputTextarea = document.getElementById('userInput');
    const composeButton = document.getElementById('composeButton');
    const questionsOutputDiv = document.getElementById('questionsOutput');
    const errorOutputDiv = document.getElementById('errorOutput');
    const errorMessageP = document.getElementById('errorMessage');

    const API_URL = 'http://localhost:8000/api/v1/question-composer/compose-questions';

    composeButton.addEventListener('click', async () => {
        const userInputRaw = userInputTextarea.value.trim();
        if (!userInputRaw) {
            displayError('User characteristics cannot be empty.');
            return;
        }

        let userInputJson;
        try {
            userInputJson = JSON.parse(userInputRaw);
        } catch (error) {
            displayError('Invalid JSON format for user characteristics. Please check the input.');
            console.error("JSON parsing error:", error);
            return;
        }

        // Clear previous results and errors
        questionsOutputDiv.innerHTML = '<p>Loading...</p>';
        errorOutputDiv.style.display = 'none';
        errorMessageP.textContent = '';

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ data: userInputJson })
            });

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    // If parsing error response fails, use status text
                    throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
                }
                // Try to get a more specific message from the API's error structure
                const detailMessage = errorData.detail?.[0]?.msg || errorData.message || JSON.stringify(errorData.detail || errorData);
                throw new Error(`API Error: ${response.status} - ${detailMessage}`);
            }

            const result = await response.json();
            console.log("API Response:", result);

            if (result.error_code !== 'ERROR_CODE_SUCCESS' || !result.data || !result.data.questions) {
                displayError(result.message || 'Failed to compose questions. Unexpected response structure.');
                return;
            }

            displayQuestions(result.data.questions);

        } catch (error) {
            console.error('Error composing questions:', error);
            displayError(error.message || 'An unexpected error occurred.');
        }
    });

    function displayQuestions(questions) {
        if (!questions || questions.length === 0) {
            questionsOutputDiv.innerHTML = '<p>No questions were generated.</p>';
            return;
        }

        const ul = document.createElement('ul');
        questions.forEach(q => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>ID:</strong> ${q.id}<br>
                            <strong>Text:</strong> ${q.text}<br>
                            <strong>Category:</strong> ${q.category}`;
            ul.appendChild(li);
        });
        questionsOutputDiv.innerHTML = ''; // Clear loading/previous
        questionsOutputDiv.appendChild(ul);
    }

    function displayError(message) {
        errorMessageP.textContent = message;
        errorOutputDiv.style.display = 'block';
        questionsOutputDiv.innerHTML = '<p>Failed to load questions.</p>'; // Clear loading/previous content
    }
});

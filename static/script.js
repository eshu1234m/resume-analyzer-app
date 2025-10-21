document.addEventListener('DOMContentLoaded', () => {
    // --- Element Selectors ---
    const form = document.getElementById('resume-form');
    const resultsDiv = document.getElementById('results');
    const loader = document.getElementById('loader');
    const analyzeAnotherBtn = document.getElementById('analyze-another');
    const formContainer = document.querySelector('main');
    const resumeInput = document.getElementById('resume');
    const fileNameDisplay = document.getElementById('file-name-display');

    // --- Event Listener for File Selection ---
    // This provides visual feedback to the user by showing the name of the selected file.
    resumeInput.addEventListener('change', () => {
        if (resumeInput.files.length > 0) {
            fileNameDisplay.textContent = resumeInput.files[0].name;
        } else {
            fileNameDisplay.textContent = 'No file chosen';
        }
    });

    // --- Event Listener for Form Submission ---
    // This function handles the main analysis logic when the user clicks the submit button.
    form.addEventListener('submit', async function(event) {
        event.preventDefault(); // Prevent the default browser form submission

        const formData = new FormData(form);
        
        // --- UI Updates: Show Loader, Hide Form ---
        loader.style.display = 'block';
        formContainer.style.display = 'none';
        resultsDiv.style.display = 'none';
        resultsDiv.innerHTML = ''; // Clear previous results

        try {
            // --- API Call to the Flask Backend ---
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            // Get the raw text response from the server
            const rawText = await response.text();

            // Check if the server responded with an error status
            if (!response.ok) {
                // Try to parse as JSON for a structured error message
                try {
                    const errorData = JSON.parse(rawText);
                    throw new Error(errorData.error || 'Something went wrong on the server.');
                } catch (e) {
                    // If parsing fails, throw a generic server error
                    throw new Error(`Server returned an error: ${response.status} ${response.statusText}`);
                }
            }
            
            // --- Process and Display Successful Response ---
            const analysis = JSON.parse(rawText);
            let htmlContent = `<h2>Analysis Complete!</h2>`;

            // Check which type of analysis was performed (Job Description vs. General)
            if (analysis.match_score !== undefined) {
                // --- Display for Resume vs. Job Description Analysis ---
                htmlContent += `
                    <h3>Match Score: <span class="score">${analysis.match_score}/100</span></h3>
                    <p>${analysis.summary || 'A summary of how well your resume matches the job description.'}</p>
                    <h4>❌ Missing Keywords:</h4>
                    <p>${analysis.missing_keywords.join(', ') || 'Great job, no critical keywords seem to be missing!'}</p>
                    <h4>💡 Tailoring Suggestions:</h4>
                    <ul>${analysis.tailoring_suggestions.map(item => `<li>${item}</li>`).join('')}</ul>
                `;
            } else {
                // --- Display for General Resume Analysis ---
                htmlContent += `
                    <h3>ATS Score: <span class="score">${analysis.ats_score || 'N/A'}/100</span></h3>
                    <h4>✅ Strengths:</h4>
                    <ul>${analysis.strengths.map(item => `<li>${item}</li>`).join('')}</ul>
                    <h4>📝 Feedback for Improvement:</h4>
                    <ul>${analysis.feedback.map(item => `<li>${item}</li>`).join('')}</ul>
                    <h4>🚀 Suggested Job Roles:</h4>
                    <ul>${analysis.job_suggestions.map(role => {
                        const linkedinUrl = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(role)}&location=India`;
                        return `<li>${role} - <a href="${linkedinUrl}" target="_blank">Search on LinkedIn</a></li>`;
                    }).join('')}</ul>
                `;
            }
            resultsDiv.innerHTML = htmlContent;

        } catch (error) {
            // --- Error Handling ---
            // Display a user-friendly error message in the results box.
            let errorMessage = "An unknown error occurred.";
            if (error instanceof SyntaxError) {
                // This specific error means the AI response was not valid JSON
                errorMessage = `There was a problem parsing the AI's response. This can happen with very large resumes. Please try again.`;
                console.error("JSON Parsing Error:", error);
            } else {
                errorMessage = error.message;
            }
            resultsDiv.innerHTML = `<div class="error-box">
                <h3>Analysis Failed</h3>
                <p>${errorMessage}</p>
                <p>Please try again with a different PDF file.</p>
            </div>`;
        } finally {
            // --- UI Cleanup ---
            // This code runs whether the analysis succeeded or failed.
            loader.style.display = 'none';
            resultsDiv.style.display = 'block';
            analyzeAnotherBtn.style.display = 'block';
        }
    });

    // --- Event Listener for the "Analyze Another" Button ---
    // Resets the UI to its original state.
    analyzeAnotherBtn.addEventListener('click', () => {
        resultsDiv.style.display = 'none';
        analyzeAnotherBtn.style.display = 'none';
        form.reset();
        fileNameDisplay.textContent = 'No file chosen'; // Reset the file name display
        formContainer.style.display = 'block';
    });
});


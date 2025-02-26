// Main JavaScript for LinkedIn Job Scraper web interface

document.addEventListener('DOMContentLoaded', function() {
    // File selector functionality
    const fileSelector = document.getElementById('fileSelector');
    const loadFileButton = document.getElementById('loadFileButton');
    const loadingMessage = document.getElementById('loadingMessage');
    const jobListingsContainer = document.getElementById('jobListingsContainer');
    const jobListingsBody = document.getElementById('jobListingsBody');

    // Function to update the table with new job data
    function updateJobListings(jobs) {
        // Clear current table content
        jobListingsBody.innerHTML = '';
        
        if (jobs && jobs.length > 0) {
            // Add each job to the table
            jobs.forEach(job => {
                const row = document.createElement('tr');
                row.style.cursor = 'pointer';
                
                // Add job data cells
                row.innerHTML = `
                    <td>${job.title}</td>
                    <td>${job.company}</td>
                    <td>${job.location}</td>
                    <td>${job.date_posted}</td>
                    <td>
                        <a href="${job.link}" target="_blank" class="btn btn-sm btn-primary">View Job</a>
                    </td>
                `;
                
                // Make row clickable
                row.addEventListener('click', function(e) {
                    if (!e.target.classList.contains('btn')) {
                        const link = row.querySelector('a.btn-primary').getAttribute('href');
                        window.open(link, '_blank');
                    }
                });
                
                jobListingsBody.appendChild(row);
            });
            
            // Show the table and hide any alerts
            const tableContainer = jobListingsBody.closest('.table-responsive');
            const alertContainer = jobListingsContainer.querySelector('.alert');
            
            if (tableContainer) tableContainer.classList.remove('d-none');
            if (alertContainer) alertContainer.classList.add('d-none');
        } else {
            // No jobs found, show alert
            let alertContainer = jobListingsContainer.querySelector('.alert');
            const tableContainer = jobListingsBody.closest('.table-responsive');
            
            if (!alertContainer) {
                alertContainer = document.createElement('div');
                alertContainer.className = 'alert alert-info';
                alertContainer.textContent = 'No job listings found in the selected file.';
                jobListingsContainer.appendChild(alertContainer);
            } else {
                alertContainer.classList.remove('d-none');
            }
            
            if (tableContainer) tableContainer.classList.add('d-none');
        }
    }

    // Function to load job data from a specific file
    function loadJobFile(filename) {
        // Show loading indicator
        loadingMessage.classList.remove('d-none');
        document.getElementById('loadingText').textContent = `Loading jobs from ${filename}...`;
        
        // Update page header to show loading state
        const headerText = document.querySelector('header p.text-muted');
        if (headerText) {
            headerText.textContent = `Loading jobs from ${filename}...`;
        }
        
        // Fetch job data from the server
        fetch(`/jobs/${filename}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update the job listings
                    updateJobListings(data.jobs);
                    
                    // Format the filename for display
                    let displayName = filename;
                    // Try to extract parts from the new filename format: job_location_date_time.json
                    const parts = filename.match(/^(.+?)_(.+?)_([A-Za-z]+\d+_\d+)_(\d+)\.json$/);
                    if (parts) {
                        const job = parts[1].replace(/_/g, ' ');
                        const location = parts[2].replace(/_/g, ' ');
                        const date = parts[3];
                        displayName = `${job} in ${location} (${date})`;
                    }
                    // Fallback format for old-style filenames
                    else if (filename.startsWith('all_jobs_')) {
                        displayName = filename.replace('all_jobs_', 'search from ').replace('.json', '');
                    }
                    
                    // Update header text with formatted filename
                    if (headerText) {
                        // Create or update the span with data-filename attribute
                        let fileNameSpan = document.getElementById('currentFileName');
                        if (!fileNameSpan) {
                            fileNameSpan = document.createElement('span');
                            fileNameSpan.id = 'currentFileName';
                            // Replace any existing content with our new span
                            headerText.innerHTML = `Showing ${data.jobCount} jobs from `;
                            headerText.appendChild(fileNameSpan);
                        }
                        
                        fileNameSpan.setAttribute('data-filename', filename);
                        fileNameSpan.textContent = displayName;
                        
                        // Make sure the rest of the text is correct
                        if (headerText.textContent.indexOf(`Showing ${data.jobCount} jobs from`) === -1) {
                            headerText.childNodes[0].nodeValue = `Showing ${data.jobCount} jobs from `;
                        }
                    }
                    
                    console.log(`Loaded ${data.jobCount} jobs from ${filename}`);
                } else {
                    console.error('Error loading job data:', data.error);
                    alert(`Failed to load job data: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error loading job data:', error);
                alert('Failed to load job data. Please try again.');
            })
            .finally(() => {
                // Hide loading indicator
                loadingMessage.classList.add('d-none');
            });
    }

    // Add event listener to the load button
    if (loadFileButton) {
        loadFileButton.addEventListener('click', function() {
            const selectedFile = fileSelector.value;
            if (selectedFile) {
                loadJobFile(selectedFile);
            }
        });
    }
    
    // Add event listener to the select to auto-load on change
    if (fileSelector) {
        fileSelector.addEventListener('change', function() {
            const selectedFile = fileSelector.value;
            if (selectedFile) {
                loadJobFile(selectedFile);
            }
        });
    }

    // Handle form submission for running the scraper
    const scraperForm = document.querySelector('form[action="/run-scraper"]');
    if (scraperForm) {
        scraperForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const title = document.getElementById('title').value;
            const location = document.getElementById('location').value;
            const experience = document.getElementById('experience').value;
            
            if (!title || !location) {
                alert('Please enter both job title and location');
                return;
            }
            
            // Create or update the status container
            let statusContainer = document.getElementById('scraperStatusContainer');
            if (!statusContainer) {
                statusContainer = document.createElement('div');
                statusContainer.id = 'scraperStatusContainer';
                statusContainer.className = 'alert alert-info mt-3';
                scraperForm.parentNode.appendChild(statusContainer);
            }
            
            // Update the status message
            statusContainer.innerHTML = `
                <div class="d-flex align-items-center">
                    <strong>Starting scraper for "${title}" jobs in "${location}"...</strong>
                    <div class="spinner-border spinner-border-sm ms-2" role="status" aria-hidden="true"></div>
                </div>
                <div class="progress mt-2" style="height: 5px;">
                    <div id="scraperProgressBar" class="progress-bar progress-bar-striped progress-bar-animated" style="width: 5%;"></div>
                </div>
                <small class="mt-2 d-block">This may take several minutes. You can continue using the site while the scraper runs.</small>
            `;
            
            // Display loading state on the button
            const submitBtn = scraperForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
            
            // Convert form data to JSON
            const formData = {
                title: title,
                location: location,
                experience: experience
            };
            
            // Send the request via fetch API
            fetch('/run-scraper', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                // Initial response received, now we poll for completion
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Failed to start scraper');
                }
            })
            .then(data => {
                console.log('Scraper started:', data);
                
                // Update status message to indicate the scraper is running
                statusContainer.querySelector('strong').textContent = 
                    `Scraping LinkedIn for "${title}" jobs in "${location}"...`;
                
                // Set up a progress animation
                const progressBar = document.getElementById('scraperProgressBar');
                let progress = 10;
                let progressTimer = setInterval(() => {
                    progress += 5;
                    if (progress > 95) progress = 95; // Never reach 100% until truly complete
                    progressBar.style.width = `${progress}%`;
                }, 10000); // Increment every 10 seconds
                
                // Poll for completion - check every 10 seconds
                let pollCount = 0;
                const maxPolls = 90; // 15 minutes max (90 * 10 seconds)
                
                function checkScraperStatus() {
                    pollCount++;
                    
                    // Check if the latest file has been updated
                    fetch('/api/jobs')
                        .then(response => response.json())
                        .then(jobs => {
                            // Check if we have a new file
                            const headerText = document.querySelector('header p.text-muted');
                            const currentFileElement = document.getElementById('currentFileName');
                            const currentFile = currentFileElement ? currentFileElement.getAttribute('data-filename') : null;
                            
                            // If poll limit reached, assume it's complete or failed
                            if (pollCount >= maxPolls) {
                                clearInterval(progressTimer);
                                clearTimeout(pollTimer);
                                
                                // Update the status
                                statusContainer.innerHTML = `
                                    <div class="alert alert-warning">
                                        <strong>Scraper process timed out</strong>
                                        <p>The scraper might still be running. Refresh the page to check for new results.</p>
                                    </div>
                                `;
                                
                                // Re-enable the submit button
                                submitBtn.disabled = false;
                                submitBtn.innerHTML = originalBtnText;
                                return;
                            }
                            
                            // Check if we have any files
                            fetch('/')
                                .then(response => response.text())
                                .then(html => {
                                    const parser = new DOMParser();
                                    const doc = parser.parseFromString(html, 'text/html');
                                    const fileSelector = doc.getElementById('fileSelector');
                                    
                                    if (fileSelector) {
                                        const options = fileSelector.querySelectorAll('option');
                                        if (options.length > 0) {
                                            const latestFile = options[0].value;
                                            
                                            // Check if we have a new file that we didn't have before
                                            if (currentFile && latestFile !== currentFile) {
                                                // Scraper has finished with a new file!
                                                clearInterval(progressTimer);
                                                clearTimeout(pollTimer);
                                                
                                                // Update the progress to 100%
                                                progressBar.style.width = '100%';
                                                progressBar.classList.remove('progress-bar-animated');
                                                
                                                // Update the status
                                                statusContainer.innerHTML = `
                                                    <div class="alert alert-success">
                                                        <strong>Scraper completed successfully!</strong>
                                                        <p>New job listings have been found. <a href="javascript:void(0)" id="loadNewResults">Click here</a> to view them.</p>
                                                    </div>
                                                `;
                                                
                                                // Add event listener to the link
                                                document.getElementById('loadNewResults').addEventListener('click', function() {
                                                    loadJobFile(latestFile);
                                                    window.scrollTo(0, 0);
                                                });
                                                
                                                // Re-enable the submit button
                                                submitBtn.disabled = false;
                                                submitBtn.innerHTML = originalBtnText;
                                                
                                                // Load the new results
                                                loadJobFile(latestFile);
                                                return;
                                            }
                                        }
                                    }
                                    
                                    // Continue polling
                                    pollTimer = setTimeout(checkScraperStatus, 10000);
                                });
                        })
                        .catch(error => {
                            console.error('Error checking scraper status:', error);
                            // Continue polling despite errors
                            pollTimer = setTimeout(checkScraperStatus, 10000);
                        });
                }
                
                // Start polling after a short delay
                let pollTimer = setTimeout(checkScraperStatus, 5000);
            })
            .catch(error => {
                console.error('Error starting scraper:', error);
                
                // Show error message
                statusContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Failed to start scraper</strong>
                        <p>${error.message}</p>
                    </div>
                `;
                
                // Re-enable the submit button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    }
    
    // Check for URL parameters (e.g., after redirect from scraper)
    function checkUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Check for error parameter
        const error = urlParams.get('error');
        if (error) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show';
            alertDiv.innerHTML = `
                <strong>Error:</strong> ${error}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            document.querySelector('.container').prepend(alertDiv);
        }
        
        // Check for file parameter
        const file = urlParams.get('file');
        if (file && fileSelector) {
            // Find the option with this file
            const options = fileSelector.querySelectorAll('option');
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === file) {
                    fileSelector.value = file;
                    loadJobFile(file);
                    break;
                }
            }
        }
    }
    
    // Check URL parameters on page load
    checkUrlParameters();
    
    // Make table rows clickable to view job details
    const jobRows = document.querySelectorAll('table tbody tr');
    jobRows.forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            // If they didn't click on the button itself
            if (!e.target.classList.contains('btn')) {
                const link = this.querySelector('a.btn-primary').getAttribute('href');
                window.open(link, '_blank');
            }
        });
    });
}); 
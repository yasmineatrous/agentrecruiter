// AI Candidate Fit Evaluator - Frontend JavaScript

class CandidateEvaluator {
    constructor() {
        this.form = document.getElementById('evaluationForm');
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        this.errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        this.resultsContainer = document.getElementById('resultsContainer');
        this.apiStatus = document.getElementById('apiStatus');

        this.latestEvaluation = null;
        this.downloadBtn = document.getElementById('downloadJsonBtn');
        this.downloadBtn.addEventListener('click', () => {
            if (this.latestEvaluation) {
                this.downloadJSON(this.latestEvaluation);
            }
        });

        this.initializeEventListeners();
        this.checkApiStatus();
    }

    initializeEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // File input validation
        const fileInputs = this.form.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => this.validateFile(e));
        });
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData();
        const candidateName = document.getElementById('candidateName').value;
        const resumeFile = document.getElementById('resumeFile').files[0];
        const jobDescriptionFile = document.getElementById('jobDescriptionFile').files[0];
        
        // Validate files
        if (!resumeFile || !jobDescriptionFile) {
            this.showError('Please select both resume and job description files.');
            return;
        }
        
        // Validate file sizes (10MB max)
        const maxSize = 10 * 1024 * 1024;
        if (resumeFile.size > maxSize || jobDescriptionFile.size > maxSize) {
            this.showError('File size must be less than 10MB.');
            return;
        }
        
        // Prepare form data
        formData.append('resume_file', resumeFile);
        formData.append('job_description_file', jobDescriptionFile);
        if (candidateName) {
            formData.append('candidate_name', candidateName);
        }
        
        // Show loading modal
        this.showLoading();
        
        try {
            const response = await fetch('/evaluate-candidate', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Evaluation failed');
            }
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Error:', error);
            this.showError(error.message || 'An error occurred during evaluation.');
        } finally {
            this.hideLoading();
        }
    }

    validateFile(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = {
            'resumeFile': ['.pdf', '.docx'],
            'jobDescriptionFile': ['.pdf', '.docx', '.txt']
        };
        
        // Check file size
        if (file.size > maxSize) {
            this.showError('File size must be less than 10MB.');
            event.target.value = '';
            return;
        }
        
        // Check file type
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const allowedExtensions = allowedTypes[event.target.id] || [];
        
        if (!allowedExtensions.includes(fileExtension)) {
            this.showError(`Invalid file type. Allowed types: ${allowedExtensions.join(', ')}`);
            event.target.value = '';
            return;
        }
    }

    showLoading() {
        this.updateApiStatus('processing');
        this.updateLoadingStatus('Parsing documents...');
        this.loadingModal.show();
        
        // Simulate loading progress
        const statuses = [
            'Parsing documents...',
            'Extracting candidate profile...',
            'Analyzing job requirements...',
            'Generating embeddings...',
            'Performing semantic search...',
            'Evaluating candidate fit...',
            'Generating insights...'
        ];
        
        let currentIndex = 0;
        const interval = setInterval(() => {
            if (currentIndex < statuses.length - 1) {
                currentIndex++;
                this.updateLoadingStatus(statuses[currentIndex]);
            } else {
                clearInterval(interval);
            }
        }, 2000);
        
        this.loadingInterval = interval;
    }

    hideLoading() {
        if (this.loadingInterval) {
            clearInterval(this.loadingInterval);
        }
        this.loadingModal.hide();
        this.updateApiStatus('ready');
    }

    updateLoadingStatus(status) {
        const loadingStatus = document.getElementById('loadingStatus');
        if (loadingStatus) {
            loadingStatus.textContent = status;
        }
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.errorModal.show();
        this.updateApiStatus('error');
    }

    updateApiStatus(status) {
        const statusMap = {
            'ready': { text: 'Ready', class: 'status-ready' },
            'processing': { text: 'Processing...', class: 'status-processing' },
            'error': { text: 'Error', class: 'status-error' }
        };
        
        const statusInfo = statusMap[status] || statusMap['ready'];
        this.apiStatus.textContent = statusInfo.text;
        this.apiStatus.className = statusInfo.class;
    }

    displayResults(evaluation) {
        this.latestEvaluation = evaluation; // save latest result
        this.downloadBtn.style.display = 'inline-block'; // show download button

        const html = this.generateResultsHTML(evaluation);
        this.resultsContainer.innerHTML = html;
        this.resultsContainer.classList.add('fade-in');
        
        // Initialize progress bar animation
        setTimeout(() => {
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = evaluation.fit_percentage + '%';
            }
        }, 100);
    }

    downloadJSON(data, filename = 'evaluation_result.json') {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();

        URL.revokeObjectURL(url);
    }

    generateResultsHTML(evaluation) {
        const fitClass = this.getFitClass(evaluation.fit_score);
        const progressClass = this.getProgressClass(evaluation.fit_percentage);
        
        return `
            <div class="evaluation-results">
                <!-- Fit Score -->
                <div class="fit-score ${fitClass}">
                    <i class="fas fa-chart-bar me-2"></i>
                    ${evaluation.fit_score}
                    <div class="mt-2">
                        <div class="progress">
                            <div class="progress-bar ${progressClass}" role="progressbar" style="width: 0%" 
                                 aria-valuenow="${evaluation.fit_percentage}" aria-valuemin="0" aria-valuemax="100">
                                ${evaluation.fit_percentage.toFixed(1)}%
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Candidate Profile -->
                <div class="candidate-profile">
                    <h5 class="mb-3">
                        <i class="fas fa-user me-2"></i>
                        ${evaluation.candidate_name ? evaluation.candidate_name : 'Candidate'} Profile
                    </h5>
                    
                    ${this.generateProfileSection('Education', evaluation.candidate_profile.education, 'fa-graduation-cap')}
                    ${this.generateProfileSection('Skills', evaluation.candidate_profile.skills, 'fa-tools')}
                    ${this.generateProfileSection('Experience', evaluation.candidate_profile.experience, 'fa-briefcase')}
                    ${this.generateProfileSection('Certifications', evaluation.candidate_profile.certifications, 'fa-certificate')}
                    ${this.generateProfileSection('Projects', evaluation.candidate_profile.projects, 'fa-project-diagram')}
                </div>

                <!-- Comparison Matrix -->
                <div class="comparison-matrix mb-4">
                    <div class="matrix-header">
                        <i class="fas fa-list-check me-2"></i>
                        Requirement Analysis
                    </div>
                    ${evaluation.comparison_matrix.map(item => this.generateMatrixItem(item)).join('')}
                </div>

                <!-- Explanation -->
                <div class="explanation-section">
                    <h6><i class="fas fa-lightbulb me-2"></i>Overall Assessment</h6>
                    <p class="mb-0">${evaluation.explanation}</p>
                </div>

                <!-- Strengths and Areas for Improvement -->
                <div class="strengths-weaknesses">
                    <div class="strengths">
                        <h6><i class="fas fa-thumbs-up me-2"></i>Key Strengths</h6>
                        ${evaluation.strengths.length > 0 ? 
                            `<ul>${evaluation.strengths.map(strength => `<li>${strength}</li>`).join('')}</ul>` :
                            '<p class="text-muted mb-0">No specific strengths identified.</p>'
                        }
                    </div>
                    <div class="weaknesses">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Areas for Improvement</h6>
                        ${evaluation.areas_for_improvement.length > 0 ? 
                            `<ul>${evaluation.areas_for_improvement.map(area => `<li>${area}</li>`).join('')}</ul>` :
                            '<p class="text-muted mb-0">No specific areas for improvement identified.</p>'
                        }
                    </div>
                </div>

                <!-- Recommendations -->
                <div class="recommendations">
                    <h6><i class="fas fa-lightbulb me-2"></i>Hiring Recommendations</h6>
                    ${evaluation.recommendations.length > 0 ? 
                        `<ul>${evaluation.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul>` :
                        '<p class="text-muted mb-0">No specific recommendations provided.</p>'
                    }
                </div>
            </div>
        `;
    }

    generateProfileSection(title, items, icon) {
        if (!items || items.length === 0) return '';
        
        return `
            <div class="profile-section">
                <h6><i class="fas ${icon} me-2"></i>${title}</h6>
                <div class="profile-tags">
                    ${items.map(item => `<span class="profile-tag">${item}</span>`).join('')}
                </div>
            </div>
        `;
    }

    generateMatrixItem(item) {
        const matchIcon = item.match ? 'fa-check-circle match' : 'fa-times-circle no-match';
        const confidenceClass = this.getConfidenceClass(item.confidence);
        
        return `
            <div class="matrix-item">
                <div class="matrix-requirement">
                    <strong>${item.requirement}</strong>
                    <div class="text-muted small mt-1">${item.explanation}</div>
                </div>
                <div class="matrix-match">
                    <i class="fas ${matchIcon} match-icon"></i>
                    <span class="confidence-badge ${confidenceClass}">
                        ${Math.round(item.confidence * 100)}%
                    </span>
                </div>
            </div>
        `;
    }

    getFitClass(fitScore) {
        const score = fitScore.toLowerCase();
        if (score.includes('high')) return 'high-fit';
        if (score.includes('moderate')) return 'moderate-fit';
        return 'low-fit';
    }

    getProgressClass(percentage) {
        if (percentage >= 80) return 'bg-success';
        if (percentage >= 50) return 'bg-warning';
        return 'bg-danger';
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.5) return 'confidence-medium';
        return 'confidence-low';
    }

    async checkApiStatus() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                this.updateApiStatus('ready');
            } else {
                this.updateApiStatus('error');
            }
        } catch (error) {
            this.updateApiStatus('error');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CandidateEvaluator();
});

// Add some utility functions for enhanced user experience
document.addEventListener('DOMContentLoaded', () => {
    // Add tooltips to form elements
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Add drag and drop functionality for file inputs
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        const parentDiv = input.parentElement;
        
        parentDiv.addEventListener('dragover', (e) => {
            e.preventDefault();
            parentDiv.classList.add('bg-light', 'border-primary');
        });
        
        parentDiv.addEventListener('dragleave', (e) => {
            e.preventDefault();
            parentDiv.classList.remove('bg-light', 'border-primary');
        });
        
        parentDiv.addEventListener('drop', (e) => {
            e.preventDefault();
            parentDiv.classList.remove('bg-light', 'border-primary');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
});

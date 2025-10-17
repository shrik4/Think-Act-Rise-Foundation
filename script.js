// --- MOCK DATA SIMULATING REAL-TIME API RESPONSE ---
        // This simulates the data we would scrape or fetch from the newdelhi.dcourts.gov.in backend
        const MOCK_COMPLEXES = [
            { id: 'patiala', name: 'Patiala House Courts' },
            { id: 'tis_hazari', name: 'Tis Hazari Courts' },
            { id: 'karkardooma', name: 'Karkardooma Courts' },
        ];

        const MOCK_JUDGES = {
            'patiala': [
                { id: '101', name: 'Ms. Aruna Puri, CMM' },
                { id: '102', name: 'Mr. Vivek Sharma, ASJ' },
                { id: '103', name: 'Ms. Meenu Kaushik, MM' },
            ],
            'tis_hazari': [
                { id: '201', name: 'Dr. Neera Bhatia, ASJ' },
                { id: '202', name: 'Mr. Ritesh Singh, CMM' },
            ],
            'karkardooma': [
                { id: '301', name: 'Mr. Rajesh Goel, ADJ' },
                { id: '302', name: 'Ms. Sunita Gupta, ASJ' },
                { id: '303', 'name': 'Mr. Alok Kumar, MM' },
            ]
        };
        
        // --- CORE MOCKING FUNCTIONS ---

        function _mock_fetch_complexes() {
            // Simulates fetching the list of court complexes in real time
            return new Promise(resolve => {
                setTimeout(() => resolve(MOCK_COMPLEXES), 500);
            });
        }

        async function fetchJudges(complexId) {
            const response = await fetch(`/api/judges?complex_id=${complexId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        }
        
        // --- APPLICATION STATE AND LOGIC ---
        
        let appState = {
            complexes: [],
            judges: [],
            selectedComplexId: null,
            selectedDate: new Date().toISOString().split('T')[0] // Default to today
        };

        const elements = {
            complexSelect: null,
            dateInput: null,
            judgesList: null,
            downloadAllBtn: null,
            statusMessage: null
        };
        
        // Utility to display status messages
        function setStatus(message, isError = false) {
            if (elements.statusMessage) {
                elements.statusMessage.textContent = message;
                elements.statusMessage.className = `p-3 mt-4 rounded-lg font-medium text-sm transition duration-300 ${
                    isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                }`;
                // Auto-clear after a few seconds
                clearTimeout(window.statusTimer);
                window.statusTimer = setTimeout(() => {
                    elements.statusMessage.textContent = '';
                    elements.statusMessage.className = 'mt-4';
                }, 8000);
            }
        }
        
        // 1. Initial Load: Fetch Court Complexes
        async function loadCourtComplexes() {
            try {
                elements.complexSelect.innerHTML = '<option value="" disabled>Loading Complexes...</option>';
                const complexes = await fetchCourtComplexes();
                appState.complexes = complexes;
                
                let options = '<option value="" selected disabled>Select Court Complex</option>';
                complexes.forEach(c => {
                    options += `<option value="${c.id}">${c.name}</option>`;
                });
                elements.complexSelect.innerHTML = options;
                elements.complexSelect.disabled = false;

            } catch (error) {
                setStatus('Error loading court complexes. Please try again.', true);
                console.error("Load Complexes Error:", error);
            }
        }

        // 2. Cascade: Fetch Judges/Courts
        async function handleComplexChange(event) {
            const complexId = event.target.value;
            appState.selectedComplexId = complexId;
            
            // Get complex name for display/download
            const complex = appState.complexes.find(c => c.id === complexId);
            const complexName = complex ? complex.name : 'Unknown Complex';
            
            elements.judgesList.innerHTML = `
                <div class="flex items-center space-x-2 p-4 text-indigo-600">
                    <div class="spinner w-5 h-5 border-2 border-indigo-600 rounded-full"></div>
                    <span>Fetching Judges for ${complexName}...</span>
                </div>
            `;
            elements.downloadAllBtn.disabled = true;
 
             try {
                 const judges = await fetchJudges(complexId);
                 appState.judges = judges;
                 renderJudgesList(complexName);
            } catch (error) {
                setStatus('Error fetching judges list.', true);
                appState.judges = [];
                renderJudgesList(complexName);
            }
        }

        // 3. Render List of Judges/Courts
        function renderJudgesList(complexName) {
            const date = appState.selectedDate;
            
            if (appState.judges.length === 0) {
                elements.judgesList.innerHTML = `<p class="text-center text-gray-500 p-8">No Judges found for ${complexName}.</p>`;
                elements.downloadAllBtn.disabled = true;
                return;
            }
            
            let listHtml = `<div class="p-4 bg-indigo-50/50 rounded-t-lg font-semibold text-indigo-800 border-b border-indigo-200">
                                ${appState.judges.length} Judges/Courts Found for ${complexName} on ${date}
                            </div>
                            <ul class="divide-y divide-gray-200">`;
            
            appState.judges.forEach(judge => {
                listHtml += `
                    <li class="p-4 flex justify-between items-center hover:bg-white transition duration-150">
                        <span class="text-gray-800 font-medium">${judge.name}</span>
                        <button 
                            id="btn-${judge.id}"
                            onclick="handleSingleDownload('${judge.id}', '${judge.name}', '${complexName}', '${date}')" 
                            class="download-btn bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 transition duration-300 shadow-md">
                            Download PDF
                        </button>
                    </li>
                `;
            });
            listHtml += '</ul>';
            
            elements.judgesList.innerHTML = listHtml;
            elements.downloadAllBtn.disabled = false;
        }

        // 4. Handle Single PDF Download
        async function handleSingleDownload(judgeId, judgeName, complexName, date) {
            const button = document.getElementById(`btn-${judgeId}`);
            button.disabled = true;
            const originalText = button.textContent;
            button.innerHTML = '<div class="spinner w-4 h-4 border-2 border-white rounded-full mr-2 inline-block"></div> Generating...';
        
            try {
                await downloadPdf(judgeName, complexName, date);
                setStatus('PDF downloaded successfully!');
            } catch (error) {
                setStatus(error.message, true);
            } finally {
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }
        
        // 5. Handle Bulk "Download All" (The Key Requirement)
        async function handleBulkDownload(complexName, date) {
            if (appState.judges.length === 0) {
                setStatus("No judges to download for the selected complex.", true);
                return;
            }
        
            const allButtons = document.querySelectorAll('.download-btn');
            const bulkButton = elements.downloadAllBtn;
        
            allButtons.forEach(btn => btn.disabled = true);
            bulkButton.disabled = true;
            const originalText = bulkButton.textContent;
            
            let successCount = 0;
            let failureCount = 0;
            
            bulkButton.innerHTML = `<div class="spinner w-4 h-4 border-2 border-white rounded-full mr-2 inline-block"></div> Starting Bulk Download...`;
            
            // Use Promise.allSettled to wait for ALL downloads, regardless of individual success/failure
            const downloadPromises = appState.judges.map(judge => {
                const judgeButton = document.getElementById(`btn-${judge.id}`);
                judgeButton.innerHTML = '<div class="spinner w-4 h-4 border-2 border-white rounded-full mr-2 inline-block"></div> Generating...';
                
                // Track progress
                const trackProgress = (status) => {
                    if (status === 'fulfilled') successCount++;
                    if (status === 'rejected') failureCount++;
                    
                    bulkButton.textContent = `Downloaded ${successCount}/${appState.judges.length}. Failed: ${failureCount}`;
                    
                    if (successCount + failureCount === appState.judges.length) {
                         // Final Status update
                        if (failureCount === 0) {
                            setStatus(`Bulk Download Complete! All ${successCount} PDF files were successfully generated and downloaded.`, false);
                        } else {
                            setStatus(`Bulk Download Finished with ${failureCount} errors. ${successCount} files were downloaded.`, true);
                        }
                    }
                };
        
                return downloadPdf(judge.name, complexName, date)
                    .then(result => trackProgress('fulfilled'))
                    .catch(error => trackProgress('rejected'))
                    .finally(() => {
                        // Restore button text after attempt
                        judgeButton.textContent = 'Download PDF';
                    });
            });
        
            await Promise.allSettled(downloadPromises);
        
            // Restore UI state
            allButtons.forEach(btn => btn.disabled = false);
            bulkButton.textContent = originalText;
            bulkButton.disabled = false;
        }

        // 6. Init Function (Run on window load)
        window.onload = function() {
            elements.complexSelect = document.getElementById('courtComplexSelect');
            elements.dateInput = document.getElementById('causeListDate');
            elements.judgesList = document.getElementById('judgesListContainer');
            elements.downloadAllBtn = document.getElementById('downloadAllBtn');
            elements.statusMessage = document.getElementById('statusMessage');

            // Set default date to today
            elements.dateInput.value = appState.selectedDate;

            // Add event listeners
            elements.complexSelect.addEventListener('change', handleComplexChange);
            elements.dateInput.addEventListener('change', (e) => {
                appState.selectedDate = e.target.value;
                // Re-render the list to update the date in the heading
                if (appState.selectedComplexId) {
                    const complex = appState.complexes.find(c => c.id === appState.selectedComplexId);
                    if(complex) renderJudgesList(complex.name);
                }
            });

            // Initial fetch of complexes
            loadCourtComplexes();
        };

        // Expose functions to the global scope for HTML event handlers
        window.handleSingleDownload = handleSingleDownload;
        window.handleBulkDownload = (complexId) => {
            const complex = appState.complexes.find(c => c.id === complexId);
            if (complex) handleBulkDownload(complex.name, appState.selectedDate);
        };

        // --- CORE API FUNCTIONS ---
 
         async function fetchCourtComplexes() {
             const response = await fetch('/api/court_complexes');
             if (!response.ok) {
                 throw new Error(`HTTP error! status: ${response.status}`);
             }
             return await response.json();
         }
 
         async function fetchJudges(complexId) {
             const response = await fetch(`/api/judges?complex_id=${complexId}`);
             if (!response.ok) {
                 throw new Error(`HTTP error! status: ${response.status}`);
             }
             return await response.json();
         }
         
         async function downloadPdf(judgeName, complexName, date) {
             try {
                 const response = await fetch('/api/download_pdf', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                     },
                     body: JSON.stringify({ judge_name: judgeName, complex_name: complexName, date: date }),
                 });
             
                 if (response.ok) {
                     const blob = await response.blob();
                     const url = window.URL.createObjectURL(blob);
                     const a = document.createElement('a');
                     a.href = url;
                     a.download = `cause_list_${judgeName}_${complexName}_${date}.pdf`;
                     document.body.appendChild(a);
                     a.click();
                     a.remove();
                     window.URL.revokeObjectURL(url);
                     console.log('PDF downloaded successfully');
                 } else {
                     const errorData = await response.json();
                     console.error('Failed to download PDF:', errorData.message);
                     alert('Failed to download PDF: ' + errorData.message);
                 }
             } catch (error) {
                 console.error('Error during PDF download:', error);
                 alert('Error during PDF download. Please try again.');
             }
         }
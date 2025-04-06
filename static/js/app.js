document.addEventListener('DOMContentLoaded', function() {
    const recommenderForm = document.getElementById('recommender-form');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultsDiv = document.getElementById('recommender-results');

    recommenderForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const platform = document.getElementById('platform').value;
        const category = document.getElementById('category').value;
        const numAccounts = parseInt(document.getElementById('num_accounts').value);
        
        if (!category) {
            alert('Please enter a category');
            return;
        }
        
        if (isNaN(numAccounts) || numAccounts < 1 || numAccounts > 20) {
            alert('Number of accounts must be between 1 and 20');
            return;
        }
        
        // Show progress
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = 'Searching for accounts...';
        resultsDiv.innerHTML = '';
        
        try {
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 5;
                if (progress <= 90) {
                    progressBar.style.width = progress + '%';
                }
            }, 200);
            
            // Make API request
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    platform,
                    category,
                    num_accounts: numAccounts
                })
            });
            
            const data = await response.json();
            
            // Clear progress interval
            clearInterval(progressInterval);
            
            if (data.status === 'success') {
                progressBar.style.width = '100%';
                progressText.textContent = 'Found accounts!';
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    displayRecommendedAccounts(data.accounts);
                }, 500);
            } else {
                throw new Error(data.message || 'Failed to find accounts');
            }
        } catch (error) {
            progressContainer.classList.add('hidden');
            resultsDiv.innerHTML = `
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    ${error.message}
                </div>
            `;
        }
    });
});

function displayRecommendedAccounts(accounts) {
    const resultsDiv = document.getElementById('recommender-results');
    if (!accounts || accounts.length === 0) {
        resultsDiv.innerHTML = `
            <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
                No accounts found for this category.
            </div>
        `;
        return;
    }

    resultsDiv.innerHTML = `
        <div class="grid gap-6 md:grid-cols-2">
            ${accounts.map(account => `
                <div class="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">@${account.username}</h3>
                            ${account.name && account.name !== account.username ? `
                                <p class="text-sm text-gray-600">${account.name}</p>
                            ` : ''}
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-medium text-gray-900">${formatNumber(account.followers_count)} followers</div>
                            ${account.following_count ? `
                                <div class="text-sm text-gray-500">${formatNumber(account.following_count)} following</div>
                            ` : ''}
                        </div>
                    </div>
                    ${account.description ? `
                        <p class="text-gray-700 mb-4 line-clamp-3">${account.description}</p>
                    ` : ''}
                    <div class="mt-4 pt-4 border-t border-gray-100">
                        <p class="text-sm text-gray-600">
                            <span class="font-medium text-gray-900">Why recommended:</span><br>
                            ${account.reason}
                        </p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function formatNumber(num) {
    if (!num && num !== 0) return 'N/A';
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

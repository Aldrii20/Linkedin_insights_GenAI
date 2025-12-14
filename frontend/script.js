const API_BASE = 'http://localhost:5000/api';


let currentPageData = null;


document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
    console.log('  Script loaded and DOM ready');
    
    
    const scrapeBtn = document.getElementById('scrapeBtn');
    if (scrapeBtn) {
        scrapeBtn.addEventListener('click', handleScrape);
    }
    
   y
    const linkedinUrlInput = document.getElementById('linkedinUrl');
    if (linkedinUrlInput) {
        linkedinUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleScrape();
        });
    }
    
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', handleTabChange);
    });
    
    
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchPages);
    }
    
    
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchPages();
        });
    }
}


function handleTabChange(event) {
    const tabName = event.target.dataset.tab;
    
    
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
   
    const targetTab = document.getElementById(`${tabName}Tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
}


async function handleScrape() {
    const linkedinUrlInput = document.getElementById('linkedinUrl');
    const url = linkedinUrlInput ? linkedinUrlInput.value.trim() : '';

    if (!url) {
        showError('Please enter a LinkedIn URL or company ID');
        return;
    }

    try {
        showLoading(true);
        hideMessages();

        console.log(' Scraping:', url);

        const response = await fetch(`${API_BASE}/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url: url,
                force_rescrape: true
            })
        });

        const result = await response.json();
        console.log(' API Response:', result);

        if (!result.success) {
            throw new Error(result.message || 'Failed to scrape');
        }

        currentPageData = result.data;
        console.log('  Page data received:', {
            name: currentPageData.name,
            followers: currentPageData.followers_count,
            employees: currentPageData.employees_text,
            posts: currentPageData.posts?.length || 0
        });

        displayResults(result.data);
        showSuccess('  Page scraped successfully!');

        // Generate AI summary
        await generateSummary(result.data.id);

    } catch (error) {
        console.error(' Error:', error);
        showError(error.message || 'Scraping failed. Make sure the URL is valid and public.');
    } finally {
        showLoading(false);
    }
}

// Display results
function displayResults(pageData) {
    console.log(' Displaying results:', pageData.name);
    
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }

    
    const companyImage = document.getElementById('companyImage');
    const noImage = document.getElementById('noImage');
    if (pageData.profile_pic_url) {
        if (companyImage) {
            companyImage.src = pageData.profile_pic_url;
            companyImage.style.display = 'block';
        }
        if (noImage) noImage.style.display = 'none';
    } else {
        if (companyImage) companyImage.style.display = 'none';
        if (noImage) noImage.style.display = 'flex';
    }

    
    const companyName = document.getElementById('companyName');
    if (companyName) companyName.textContent = pageData.name || 'Unknown Company';

    const companyIndustry = document.getElementById('companyIndustry');
    if (companyIndustry) companyIndustry.textContent = pageData.industry || 'Not specified';

    const companyUrl = document.getElementById('companyUrl');
    if (companyUrl) {
        companyUrl.textContent = pageData.url || '';
        companyUrl.href = pageData.url || '#';
    }

   
    const followersElem = document.getElementById('followers');
    if (followersElem) {
        followersElem.textContent = formatNumber(pageData.followers_count || 0);
    }

    const employeesElem = document.getElementById('employees');
    if (employeesElem) {
        employeesElem.textContent = pageData.employees_text || pageData.employees_count || '0';
    }

    const postsCountElem = document.getElementById('postsCount');
    if (postsCountElem) {
        const postsCount = (pageData.posts && pageData.posts.length) || 0;
        postsCountElem.textContent = postsCount;
    }

    console.log('     Stats displayed');

    
    const companyDescription = document.getElementById('companyDescription');
    if (companyDescription) {
        companyDescription.textContent = pageData.description || 'No description available';
    }

    
    displayPosts(pageData.posts || []);
    displayEmployees(pageData.employees || []);
    displayMetadata(pageData);

    // Scroll to results
    setTimeout(() => {
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    }, 100);
}


function displayPosts(posts) {
    const postsList = document.getElementById('postsList');
    
    if (!postsList) {
        console.error(' postsList element not found');
        return;
    }
    
    console.log('📰 Displaying', posts.length, 'posts');
    
    if (!posts || posts.length === 0) {
        postsList.innerHTML = '<p class="no-data">No posts found</p>';
        return;
    }

    postsList.innerHTML = posts.map((post) => `
        <div class="post-item">
            <p class="post-content">${escapeHtml(post.content || 'No content')}</p>
            <div class="post-stats">
                <span class="post-stat">👍 ${formatNumber(post.likes_count || 0)}</span>
                <span class="post-stat">💬 ${formatNumber(post.comments_count || 0)}</span>
                <span class="post-stat">🔄 ${formatNumber(post.shares_count || 0)}</span>
            </div>
        </div>
    `).join('');
}


function displayEmployees(employees) {
    const employeesList = document.getElementById('employeesList');
    
    if (!employeesList) {
        console.error(' employeesList element not found');
        return;
    }
    
    console.log('👥 Displaying', employees.length, 'employees');
    
    if (!employees || employees.length === 0) {
        employeesList.innerHTML = '<p class="no-data">No employees found</p>';
        return;
    }

    employeesList.innerHTML = employees.map(emp => `
        <div class="employee-item">
            <p class="employee-name">${escapeHtml(emp.name || 'Unknown')}</p>
            <p class="employee-headline">${escapeHtml(emp.headline || 'Employee')}</p>
            ${emp.profile_url ? `<a href="${escapeHtml(emp.profile_url)}" target="_blank" class="btn btn-sm">View Profile →</a>` : ''}
        </div>
    `).join('');
}


function displayMetadata(pageData) {
    const metadataContainer = document.getElementById('metadataContainer');
    
    if (!metadataContainer) {
        console.error(' metadataContainer element not found');
        return;
    }

    console.log('   Displaying metadata');

    metadataContainer.innerHTML = `
        <div class="metadata-item">
            <span class="metadata-label">🌐 Website:</span>
            <span class="metadata-value">
                ${pageData.website ? `<a href="${escapeHtml(pageData.website)}" target="_blank">${escapeHtml(pageData.website)}</a>` : 'Not specified'}
            </span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">🏢 Industry:</span>
            <span class="metadata-value">${escapeHtml(pageData.industry || 'Not specified')}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">👥 Followers:</span>
            <span class="metadata-value">${formatNumber(pageData.followers_count)}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">👔 Company Size:</span>
            <span class="metadata-value">${pageData.employees_text || pageData.employees_count || 'Not specified'} employees</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">🎯 Specialties:</span>
            <span class="metadata-value">${escapeHtml(pageData.specialities || 'Not specified')}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">⏰ Last Scraped:</span>
            <span class="metadata-value">${pageData.last_scraped ? new Date(pageData.last_scraped).toLocaleString() : 'Unknown'}</span>
        </div>
    `;
}


async function generateSummary(pageId) {
    const summaryContainer = document.getElementById('companySummary');
    const summaryLoading = document.getElementById('summaryLoading');
    
    if (!summaryContainer) {
        console.error(' companySummary element not found');
        return;
    }

    try {
        console.log('     Generating AI summary...');
        
        if (summaryLoading) summaryLoading.style.display = 'flex';
        summaryContainer.style.display = 'none';

        const response = await fetch(`${API_BASE}/pages/${pageId}/summary`);
        const result = await response.json();

        if (result.success && result.data && result.data.summary) {
            summaryContainer.textContent = result.data.summary;
            summaryContainer.style.display = 'block';
            console.log('  Summary generated successfully');
        } else {
            summaryContainer.textContent = 'Failed to generate summary';
            summaryContainer.style.display = 'block';
        }
    } catch (error) {
        console.error(' Summary error:', error);
        summaryContainer.textContent = 'Error generating summary. It will be generated later.';
        summaryContainer.style.display = 'block';
    } finally {
        if (summaryLoading) summaryLoading.style.display = 'none';
    }
}


async function searchPages() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value.trim() : '';

    if (!query) {
        alert('Please enter a search query');
        return;
    }

    try {
        console.log('🔎 Searching for:', query);
        
        const response = await fetch(`${API_BASE}/pages/search?q=${encodeURIComponent(query)}`);
        const result = await response.json();

        const resultsList = document.getElementById('resultsList');
        const searchResults = document.getElementById('searchResults');

        if (!result.success || !result.data.pages || result.data.pages.length === 0) {
            if (resultsList) resultsList.innerHTML = '<p>No results found</p>';
            if (searchResults) searchResults.style.display = 'block';
            return;
        }

        if (resultsList) {
            resultsList.innerHTML = result.data.pages.map(page => `
                <div class="result-card" onclick="loadPage('${page.id}')">
                    <p class="result-name">${escapeHtml(page.name)}</p>
                    <p class="result-industry">${escapeHtml(page.industry || 'Not specified')}</p>
                    <p class="result-followers">👥 ${formatNumber(page.followers_count)} followers</p>
                </div>
            `).join('');
        }

        if (searchResults) searchResults.style.display = 'block';
        console.log('  Found', result.data.pages.length, 'results');

    } catch (error) {
        console.error(' Search error:', error);
        alert('Search failed: ' + error.message);
    }
}


async function loadPage(pageId) {
    try {
        console.log('📦 Loading page:', pageId);
        
        const response = await fetch(`${API_BASE}/pages/${pageId}?include_posts=true&include_employees=true`);
        const result = await response.json();

        if (result.success) {
            currentPageData = result.data;
            displayResults(result.data);
            
            const resultsSection = document.getElementById('resultsSection');
            if (resultsSection) {
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            alert('Failed to load page');
        }
    } catch (error) {
        console.error(' Load error:', error);
        alert('Failed to load page: ' + error.message);
    }
}


function formatNumber(num) {
    if (num === null || num === undefined || num === '') return '0';
    num = Number(num);
    if (isNaN(num)) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}


function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function showLoading(show) {
    const scrapeBtn = document.getElementById('scrapeBtn');
    const spinner = document.querySelector('.spinner');
    
    if (scrapeBtn) scrapeBtn.disabled = show;
    if (spinner) spinner.style.display = show ? 'inline-block' : 'none';
}


function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
}


function showSuccess(message) {
    const successMessage = document.getElementById('successMessage');
    if (successMessage) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 5000);
    }
}


function hideMessages() {
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');
    if (errorMessage) errorMessage.style.display = 'none';
    if (successMessage) successMessage.style.display = 'none';
}

console.log('  All functions loaded successfully');

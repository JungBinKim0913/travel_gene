"""
Streamlit 앱에서 사용하는 CSS 스타일들
"""

SHARE_PAGE_STYLES = """
<style>
    .trip-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    .day-card {
        background: var(--background-color);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        margin-bottom: 15px;
        border-left: 4px solid #667eea;
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    .activity-item {
        background: var(--secondary-background-color);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #28a745;
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    .share-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
    }
    .trip-stats {
        display: flex;
        justify-content: space-around;
        background: rgba(255,255,255,0.1);
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
    }
    .stat-item {
        text-align: center;
    }
    
    :root {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
        --border-color: #e0e0e0;
        --muted-text-color: #666666;
        --light-text-color: #888888;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #2d2d2d;
            --secondary-background-color: #3d3d3d;
            --text-color: #ffffff;
            --border-color: #4d4d4d;
            --muted-text-color: #cccccc;
            --light-text-color: #aaaaaa;
        }
    }
    
    .stApp[data-theme="dark"] {
        --background-color: #2d2d2d;
        --secondary-background-color: #3d3d3d;
        --text-color: #ffffff;
        --border-color: #4d4d4d;
        --muted-text-color: #cccccc;
        --light-text-color: #aaaaaa;
    }
    
    .stApp[data-theme="light"] {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
        --border-color: #e0e0e0;
        --muted-text-color: #666666;
        --light-text-color: #888888;
    }
    
    .stApp {
        color-scheme: light dark;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
    }
</style>

<script>
function updateTheme() {
    const stApp = document.querySelector('.stApp');
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches ||
                   document.body.classList.contains('dark') ||
                   stApp?.getAttribute('data-theme') === 'dark';
    
    const root = document.documentElement;
    
    if (isDark) {
        root.style.setProperty('--background-color', '#2d2d2d');
        root.style.setProperty('--secondary-background-color', '#3d3d3d');
        root.style.setProperty('--text-color', '#ffffff');
        root.style.setProperty('--border-color', '#4d4d4d');
        root.style.setProperty('--muted-text-color', '#cccccc');
        root.style.setProperty('--light-text-color', '#aaaaaa');
    } else {
        root.style.setProperty('--background-color', '#ffffff');
        root.style.setProperty('--secondary-background-color', '#f8f9fa');
        root.style.setProperty('--text-color', '#000000');
        root.style.setProperty('--border-color', '#e0e0e0');
        root.style.setProperty('--muted-text-color', '#666666');
        root.style.setProperty('--light-text-color', '#888888');
    }
}

document.addEventListener('DOMContentLoaded', updateTheme);
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme);

const observer = new MutationObserver(updateTheme);
observer.observe(document.body, { 
    attributes: true, 
    attributeFilter: ['class', 'data-theme'],
    subtree: true 
});

setTimeout(updateTheme, 100);
</script>
""" 
(() => {
    const PROFILE_URL = 'https://note.com/tak0424';

    function formatBlogDate(value) {
        if (!value) return '';

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;

        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(date);
    }

    function createArticleCard(article) {
        const card = document.createElement('article');
        card.className = 'blog-card';

        const thumbWrap = document.createElement('div');
        thumbWrap.className = 'blog-thumb-wrap';

        if (article.thumbnail) {
            const img = document.createElement('img');
            img.className = 'blog-thumb';
            img.src = article.thumbnail;
            img.alt = '';
            img.loading = 'lazy';
            img.referrerPolicy = 'no-referrer';
            thumbWrap.appendChild(img);
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'blog-thumb-placeholder';
            placeholder.innerHTML = '<i class="fa-solid fa-pen-nib"></i>';
            thumbWrap.appendChild(placeholder);
        }

        const body = document.createElement('div');
        body.className = 'blog-body';

        const meta = document.createElement('div');
        meta.className = 'blog-meta';
        meta.textContent = formatBlogDate(article.published_at);

        const title = document.createElement('h3');
        title.className = 'blog-title';
        title.textContent = article.title || 'Untitled';

        const excerpt = document.createElement('p');
        excerpt.className = 'blog-excerpt';
        excerpt.textContent = article.excerpt || '';

        const link = document.createElement('a');
        link.className = 'blog-read-more';
        link.href = article.url || PROFILE_URL;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.innerHTML = 'Read Article <i class="fa-solid fa-arrow-up-right-from-square"></i>';

        body.append(meta, title, excerpt, link);
        card.append(thumbWrap, body);

        return card;
    }

    function displayBlog(data) {
        const loading = document.getElementById('blog-loading');
        const error = document.getElementById('blog-error');
        const grid = document.getElementById('blog-grid');
        const profileLink = document.getElementById('blog-profile-link');

        if (!grid) return;

        grid.innerHTML = '';
        const articles = Array.isArray(data?.articles) ? data.articles : [];

        if (profileLink) {
            profileLink.href = data?.profile_url || PROFILE_URL;
        }

        if (!articles.length) {
            if (loading) loading.classList.add('hidden');
            if (error) {
                error.textContent = 'まだ表示できるブログ記事がありません。';
                error.classList.remove('hidden');
            }
            return;
        }

        for (const article of articles.slice(0, 3)) {
            grid.appendChild(createArticleCard(article));
        }

        if (loading) loading.classList.add('hidden');
        if (error) error.classList.add('hidden');
        grid.classList.remove('hidden');
    }

    async function loadBlog() {
        try {
            const response = await fetch(`data/blog.json?cache=${Date.now()}`);
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }

            const data = await response.json();
            displayBlog(data);
        } catch (error) {
            console.warn('Blog data load error:', error);
            const loading = document.getElementById('blog-loading');
            const errorElement = document.getElementById('blog-error');
            if (loading) loading.classList.add('hidden');
            if (errorElement) errorElement.classList.remove('hidden');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadBlog, { once: true });
    } else {
        loadBlog();
    }
})();

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse, urljoin
from collections import Counter
import re
import time

# Page config
st.set_page_config(
    page_title="ITC Website Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🔍 ITC Website Analysis Dashboard")
st.markdown("Comprehensive SEO & Content Analysis Tool")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    website_url = st.text_input(
        "Enter Website URL", 
        value="https://www.itcportal.com",
        help="Enter the full URL including https://"
    )
    analyze_button = st.button("🚀 Analyze Website", type="primary")
    
    st.markdown("---")
    st.markdown("### 📊 Analysis Includes:")
    st.markdown("""
    - SEO Metrics
    - Keyword Analysis
    - Content Structure
    - Performance Metrics
    - Links Analysis
    """)

# Helper Functions
@st.cache_data(ttl=3600)
def fetch_website(url):
    """Fetch website content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        load_time = time.time() - start_time
        
        if response.status_code == 200:
            return response, load_time
        else:
            return None, None
    except Exception as e:
        st.error(f"Error fetching website: {str(e)}")
        return None, None

def extract_meta_tags(soup):
    """Extract meta tags"""
    meta_data = {}
    
    # Title
    title = soup.find('title')
    meta_data['title'] = title.text.strip() if title else "No title found"
    meta_data['title_length'] = len(meta_data['title'])
    
    # Meta description
    desc = soup.find('meta', attrs={'name': 'description'})
    meta_data['description'] = desc['content'] if desc and desc.get('content') else "No description found"
    meta_data['description_length'] = len(meta_data['description'])
    
    # Meta keywords
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    meta_data['meta_keywords'] = keywords['content'] if keywords and keywords.get('content') else "No keywords found"
    
    # Open Graph tags
    og_title = soup.find('meta', property='og:title')
    meta_data['og_title'] = og_title['content'] if og_title and og_title.get('content') else "Not set"
    
    og_desc = soup.find('meta', property='og:description')
    meta_data['og_description'] = og_desc['content'] if og_desc and og_desc.get('content') else "Not set"
    
    return meta_data

def extract_headings(soup):
    """Extract heading tags"""
    headings = {}
    for i in range(1, 7):
        tags = soup.find_all(f'h{i}')
        headings[f'h{i}'] = [tag.text.strip() for tag in tags]
    return headings

def extract_keywords(text, top_n=20):
    """Extract top keywords from text"""
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
    
    # Common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'is', 'was', 'are', 'be', 'been', 'have', 'has', 'had',
                  'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                  'this', 'that', 'these', 'those', 'it', 'its', 'from', 'by', 'as'}
    
    words = [word for word in text.split() if word not in stop_words and len(word) > 3]
    word_freq = Counter(words)
    
    return word_freq.most_common(top_n)

def analyze_links(soup, base_url):
    """Analyze internal and external links"""
    links = soup.find_all('a', href=True)
    internal_links = []
    external_links = []
    
    base_domain = urlparse(base_url).netloc
    
    for link in links:
        href = link['href']
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        if parsed.netloc == base_domain or parsed.netloc == '':
            internal_links.append(full_url)
        else:
            external_links.append(full_url)
    
    return internal_links, external_links

def analyze_images(soup):
    """Analyze images"""
    images = soup.find_all('img')
    total_images = len(images)
    images_with_alt = sum(1 for img in images if img.get('alt'))
    images_without_alt = total_images - images_with_alt
    
    return {
        'total': total_images,
        'with_alt': images_with_alt,
        'without_alt': images_without_alt
    }

# Main Analysis
if analyze_button:
    if not website_url:
        st.error("Please enter a valid URL")
    else:
        with st.spinner("🔄 Analyzing website... This may take a moment..."):
            response, load_time = fetch_website(website_url)
            
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract data
                meta_data = extract_meta_tags(soup)
                headings = extract_headings(soup)
                text_content = soup.get_text()
                keywords = extract_keywords(text_content)
                internal_links, external_links = analyze_links(soup, website_url)
                image_data = analyze_images(soup)
                
                st.success("✅ Analysis Complete!")
                
                # ===== SECTION 1: OVERVIEW METRICS =====
                st.header("📊 Overview Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Page Load Time", f"{load_time:.2f}s", 
                             delta="Good" if load_time < 3 else "Needs Improvement",
                             delta_color="normal" if load_time < 3 else "inverse")
                
                with col2:
                    st.metric("Total Words", f"{len(text_content.split()):,}")
                
                with col3:
                    st.metric("Total Images", image_data['total'])
                
                with col4:
                    ssl_status = "✅ Secure" if website_url.startswith('https') else "⚠️ Not Secure"
                    st.metric("SSL Status", ssl_status)
                
                # ===== SECTION 2: SEO ANALYSIS =====
                st.header("🎯 SEO Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Meta Tags")
                    
                    # Title analysis
                    title_status = "✅" if 30 <= meta_data['title_length'] <= 60 else "⚠️"
                    st.markdown(f"**Title Tag** {title_status}")
                    st.info(meta_data['title'])
                    st.caption(f"Length: {meta_data['title_length']} characters (Optimal: 30-60)")
                    
                    # Description analysis
                    desc_status = "✅" if 120 <= meta_data['description_length'] <= 160 else "⚠️"
                    st.markdown(f"**Meta Description** {desc_status}")
                    st.info(meta_data['description'])
                    st.caption(f"Length: {meta_data['description_length']} characters (Optimal: 120-160)")
                
                with col2:
                    st.subheader("SEO Score Card")
                    
                    # Calculate SEO score
                    score = 0
                    total_checks = 6
                    
                    checks = {
                        "Title tag present": meta_data['title'] != "No title found",
                        "Title length optimal": 30 <= meta_data['title_length'] <= 60,
                        "Meta description present": meta_data['description'] != "No description found",
                        "Description length optimal": 120 <= meta_data['description_length'] <= 160,
                        "SSL enabled": website_url.startswith('https'),
                        "Images have alt tags": image_data['with_alt'] > image_data['total'] * 0.7
                    }
                    
                    for check, passed in checks.items():
                        icon = "✅" if passed else "❌"
                        st.markdown(f"{icon} {check}")
                        if passed:
                            score += 1
                    
                    seo_score = (score / total_checks) * 100
                    st.metric("Overall SEO Score", f"{seo_score:.0f}%")
                
                # ===== SECTION 3: HEADING STRUCTURE =====
                st.header("📝 Content Structure")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("Heading Distribution")
                    heading_counts = {tag: len(content) for tag, content in headings.items() if content}
                    
                    if heading_counts:
                        df_headings = pd.DataFrame(list(heading_counts.items()), 
                                                  columns=['Tag', 'Count'])
                        fig = px.bar(df_headings, x='Tag', y='Count', 
                                    title='Heading Tags Distribution',
                                    color='Count',
                                    color_continuous_scale='Blues')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No heading tags found")
                
                with col2:
                    st.subheader("H1 Tags")
                    if headings['h1']:
                        for i, h1 in enumerate(headings['h1'][:5], 1):
                            st.markdown(f"**{i}.** {h1}")
                    else:
                        st.warning("⚠️ No H1 tags found (Bad for SEO)")
                
                # ===== SECTION 4: KEYWORD ANALYSIS =====
                st.header("🔑 Keyword Analysis")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Top Keywords")
                    if keywords:
                        df_keywords = pd.DataFrame(keywords, columns=['Keyword', 'Frequency'])
                        
                        fig = px.bar(df_keywords, x='Frequency', y='Keyword', 
                                    orientation='h',
                                    title='Top 20 Keywords by Frequency',
                                    color='Frequency',
                                    color_continuous_scale='Viridis')
                        fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No keywords extracted")
                
                with col2:
                    st.subheader("Keyword Table")
                    if keywords:
                        st.dataframe(df_keywords, use_container_width=True, height=600)
                
                # ===== SECTION 5: LINKS ANALYSIS =====
                st.header("🔗 Links Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Links", len(internal_links) + len(external_links))
                
                with col2:
                    st.metric("Internal Links", len(internal_links))
                
                with col3:
                    st.metric("External Links", len(external_links))
                
                # Links pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Internal Links', 'External Links'],
                    values=[len(internal_links), len(external_links)],
                    hole=.4,
                    marker_colors=['#3498db', '#e74c3c']
                )])
                fig.update_layout(title='Link Distribution')
                st.plotly_chart(fig, use_container_width=True)
                
                # ===== SECTION 6: IMAGE ANALYSIS =====
                st.header("🖼️ Image Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Image Statistics")
                    st.metric("Total Images", image_data['total'])
                    st.metric("Images with Alt Text", image_data['with_alt'])
                    st.metric("Images without Alt Text", image_data['without_alt'])
                    
                    if image_data['without_alt'] > 0:
                        st.warning(f"⚠️ {image_data['without_alt']} images missing alt text (Bad for SEO & Accessibility)")
                
                with col2:
                    # Image alt text chart
                    fig = go.Figure(data=[go.Pie(
                        labels=['With Alt Text', 'Without Alt Text'],
                        values=[image_data['with_alt'], image_data['without_alt']],
                        marker_colors=['#2ecc71', '#e74c3c']
                    )])
                    fig.update_layout(title='Image Alt Text Coverage')
                    st.plotly_chart(fig, use_container_width=True)
                
                # ===== SECTION 7: RECOMMENDATIONS =====
                st.header("💡 Recommendations")
                
                recommendations = []
                
                if not (30 <= meta_data['title_length'] <= 60):
                    recommendations.append("📝 Optimize title tag length (30-60 characters)")
                
                if not (120 <= meta_data['description_length'] <= 160):
                    recommendations.append("📝 Optimize meta description length (120-160 characters)")
                
                if not headings['h1']:
                    recommendations.append("⚠️ Add H1 tags to your pages")
                
                if image_data['without_alt'] > 0:
                    recommendations.append(f"🖼️ Add alt text to {image_data['without_alt']} images")
                
                if load_time > 3:
                    recommendations.append("⚡ Improve page load time (target < 3 seconds)")
                
                if not website_url.startswith('https'):
                    recommendations.append("🔒 Implement SSL certificate (HTTPS)")
                
                if recommendations:
                    for rec in recommendations:
                        st.warning(rec)
                else:
                    st.success("🎉 Great job! Your website follows most SEO best practices!")
                
            else:
                st.error("❌ Failed to fetch website. Please check the URL and try again.")

else:
    # Welcome message
    st.info("👈 Enter a website URL in the sidebar and click 'Analyze Website' to begin!")
    
    st.markdown("---")
    st.markdown("""
    ### 🌟 Features:
    - **SEO Analysis**: Title, meta tags, headings structure
    - **Keyword Extraction**: Top keywords and their frequency
    - **Content Analysis**: Word count, heading distribution
    - **Link Analysis**: Internal vs external links
    - **Image Analysis**: Alt text coverage
    - **Performance Metrics**: Page load time
    - **Actionable Recommendations**: SEO improvement suggestions
    
    ### 📌 Note:
    This tool performs basic website analysis. For comprehensive analysis, consider using specialized SEO tools.
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | Website Analyzer v1.0")
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
    page_title="Website Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 3px solid #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

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
    
    title = soup.find('title')
    meta_data['title'] = title.text.strip() if title else "No title found"
    meta_data['title_length'] = len(meta_data['title'])
    
    desc = soup.find('meta', attrs={'name': 'description'})
    meta_data['description'] = desc['content'] if desc and desc.get('content') else "No description found"
    meta_data['description_length'] = len(meta_data['description'])
    
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    meta_data['meta_keywords'] = keywords['content'] if keywords and keywords.get('content') else "No keywords found"
    
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
    text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
    
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

def get_domain_name(url):
    """Extract clean domain name from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    # Remove www. and .com/.org etc for display
    domain = domain.replace('www.', '')
    return domain.split('.')[0].upper()

# Initialize session state
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'website_name' not in st.session_state:
    st.session_state.website_name = ""

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/web.png", width=80)
    st.title("Website Analyzer")
    
    website_url = st.text_input(
        "Enter Website URL", 
        value="https://www.itcportal.com",
        help="Enter the full URL including https://"
    )
    
    analyze_button = st.button("🚀 Analyze Website", type="primary", use_container_width=True)
    
    if st.session_state.analyzed:
        st.success(f"✅ Analyzing: **{st.session_state.website_name}**")
    
    st.markdown("---")
    st.markdown("### 📊 Features:")
    st.markdown("""
    - SEO Metrics
    - Keyword Analysis
    - Content Structure
    - Performance Metrics
    - Links Analysis
    - Image Analysis
    - Recommendations
    """)
    
    st.markdown("---")
    st.caption("Built with Streamlit 🎈")

# Main content
if not st.session_state.analyzed and not analyze_button:
    # Welcome screen
    st.title("🔍 Welcome to Website Analyzer")
    st.markdown("### Comprehensive SEO & Content Analysis Tool")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **SEO Analysis**\n\nAnalyze meta tags, titles, descriptions, and overall SEO health")
    
    with col2:
        st.info("🔑 **Keyword Insights**\n\nDiscover top keywords and content themes")
    
    with col3:
        st.info("⚡ **Performance**\n\nMeasure load times and optimization opportunities")
    
    st.markdown("---")
    st.markdown("### 🚀 How to Use:")
    st.markdown("""
    1. Enter any website URL in the sidebar
    2. Click '🚀 Analyze Website' button
    3. Explore comprehensive analysis across multiple tabs
    4. Get actionable recommendations for improvement
    """)
    
    st.info("👈 **Get started by entering a URL in the sidebar!**")

# Main Analysis
if analyze_button:
    if not website_url:
        st.error("Please enter a valid URL")
    else:
        with st.spinner("🔄 Analyzing website... This may take a moment..."):
            response, load_time = fetch_website(website_url)
            
            if response:
                # Extract website name
                st.session_state.website_name = get_domain_name(website_url)
                st.session_state.analyzed = True
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract data
                meta_data = extract_meta_tags(soup)
                headings = extract_headings(soup)
                text_content = soup.get_text()
                keywords = extract_keywords(text_content)
                internal_links, external_links = analyze_links(soup, website_url)
                image_data = analyze_images(soup)
                
                st.success("✅ Analysis Complete!")

if st.session_state.analyzed:
    # Dynamic title with website name
    st.title(f"📊 {st.session_state.website_name} Website Analysis")
    st.markdown(f"**Analyzing:** `{website_url}`")
    st.markdown("---")
    
    # Recreate data (from cache if available)
    response, load_time = fetch_website(website_url)
    if response:
        soup = BeautifulSoup(response.content, 'html.parser')
        meta_data = extract_meta_tags(soup)
        headings = extract_headings(soup)
        text_content = soup.get_text()
        keywords = extract_keywords(text_content)
        internal_links, external_links = analyze_links(soup, website_url)
        image_data = analyze_images(soup)
        
        # Calculate SEO score
        score = 0
        total_checks = 6
        checks = {
            "Title tag present": meta_data['title'] != "No title found",
            "Title length optimal": 30 <= meta_data['title_length'] <= 60,
            "Meta description present": meta_data['description'] != "No description found",
            "Description length optimal": 120 <= meta_data['description_length'] <= 160,
            "SSL enabled": website_url.startswith('https'),
            "Images have alt tags": image_data['with_alt'] > image_data['total'] * 0.7 if image_data['total'] > 0 else False
        }
        for check, passed in checks.items():
            if passed:
                score += 1
        seo_score = (score / total_checks) * 100
        
        # Create tabs for better organization
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview", 
            "🎯 SEO Analysis", 
            "🔑 Keywords", 
            "📝 Content", 
            "🔗 Links & Images",
            "💡 Recommendations"
        ])
        
        # TAB 1: OVERVIEW
        with tab1:
            st.header("Quick Metrics Overview")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "SEO Score", 
                    f"{seo_score:.0f}%",
                    delta="Good" if seo_score >= 70 else "Needs Work",
                    delta_color="normal" if seo_score >= 70 else "inverse"
                )
            
            with col2:
                st.metric(
                    "Page Load Time", 
                    f"{load_time:.2f}s",
                    delta="Fast" if load_time < 3 else "Slow",
                    delta_color="normal" if load_time < 3 else "inverse"
                )
            
            with col3:
                st.metric("Total Words", f"{len(text_content.split()):,}")
            
            with col4:
                st.metric("Total Images", image_data['total'])
            
            with col5:
                ssl_status = "🔒 Secure" if website_url.startswith('https') else "⚠️ Insecure"
                st.metric("SSL Status", ssl_status)
            
            st.markdown("---")
            
            # Visual metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("SEO Health Score")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=seo_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "SEO Score"},
                    delta={'reference': 70},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#4CAF50" if seo_score >= 70 else "#FF9800"},
                        'steps': [
                            {'range': [0, 40], 'color': "#FFEBEE"},
                            {'range': [40, 70], 'color': "#FFF3E0"},
                            {'range': [70, 100], 'color': "#E8F5E9"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 70
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Quick Stats")
                
                heading_counts = {tag: len(content) for tag, content in headings.items() if content}
                total_headings = sum(heading_counts.values())
                total_links = len(internal_links) + len(external_links)
                
                stats_data = {
                    'Metric': ['Total Headings', 'Total Links', 'Internal Links', 'External Links', 'Images with Alt', 'Images without Alt'],
                    'Count': [
                        total_headings,
                        total_links,
                        len(internal_links),
                        len(external_links),
                        image_data['with_alt'],
                        image_data['without_alt']
                    ]
                }
                df_stats = pd.DataFrame(stats_data)
                
                fig = px.bar(df_stats, x='Count', y='Metric', orientation='h',
                            color='Count', color_continuous_scale='Greens')
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # TAB 2: SEO ANALYSIS
        with tab2:
            st.header("🎯 SEO Analysis")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Meta Tags Analysis")
                
                # Title analysis
                title_status = "✅" if 30 <= meta_data['title_length'] <= 60 else "⚠️"
                st.markdown(f"**Title Tag** {title_status}")
                st.info(meta_data['title'])
                st.caption(f"Length: {meta_data['title_length']} characters (Optimal: 30-60)")
                
                st.markdown("---")
                
                # Description analysis
                desc_status = "✅" if 120 <= meta_data['description_length'] <= 160 else "⚠️"
                st.markdown(f"**Meta Description** {desc_status}")
                st.info(meta_data['description'])
                st.caption(f"Length: {meta_data['description_length']} characters (Optimal: 120-160)")
                
                st.markdown("---")
                
                # Meta keywords
                st.markdown("**Meta Keywords**")
                st.info(meta_data['meta_keywords'])
                
                st.markdown("---")
                
                # Open Graph
                st.markdown("**Open Graph Tags**")
                col_og1, col_og2 = st.columns(2)
                with col_og1:
                    st.text("OG Title:")
                    st.caption(meta_data['og_title'])
                with col_og2:
                    st.text("OG Description:")
                    st.caption(meta_data['og_description'])
            
            with col2:
                st.subheader("SEO Checklist")
                
                for check, passed in checks.items():
                    icon = "✅" if passed else "❌"
                    color = "green" if passed else "red"
                    st.markdown(f":{color}[{icon} {check}]")
                
                st.markdown("---")
                st.metric("Overall SEO Score", f"{seo_score:.0f}%")
                
                if seo_score >= 80:
                    st.success("Excellent SEO!")
                elif seo_score >= 60:
                    st.warning("Good, but can improve")
                else:
                    st.error("Needs improvement")
        
        # TAB 3: KEYWORDS
        with tab3:
            st.header("🔑 Keyword Analysis")
            
            if keywords:
                df_keywords = pd.DataFrame(keywords, columns=['Keyword', 'Frequency'])
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Top Keywords Visualization")
                    fig = px.bar(df_keywords, x='Frequency', y='Keyword', 
                                orientation='h',
                                title='Top 20 Keywords by Frequency',
                                color='Frequency',
                                color_continuous_scale='Viridis')
                    fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Keyword Data")
                    st.dataframe(df_keywords, use_container_width=True, height=600)
                    
                    # Download button
                    csv = df_keywords.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Keywords CSV",
                        data=csv,
                        file_name=f"{st.session_state.website_name}_keywords.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No keywords extracted")
        
        # TAB 4: CONTENT
        with tab4:
            st.header("📝 Content Structure")
            
            col1, col2 = st.columns(2)
            
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
                    for i, h1 in enumerate(headings['h1'][:10], 1):
                        st.markdown(f"**{i}.** {h1}")
                else:
                    st.warning("⚠️ No H1 tags found (Bad for SEO)")
            
            st.markdown("---")
            
            # All headings expansion
            with st.expander("🔍 View All Headings"):
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if headings[tag]:
                        st.markdown(f"### {tag.upper()} Tags ({len(headings[tag])})")
                        for i, heading in enumerate(headings[tag][:20], 1):
                            st.text(f"{i}. {heading}")
                        st.markdown("---")
        
        # TAB 5: LINKS & IMAGES
        with tab5:
            st.header("🔗 Links & Images Analysis")
            
            # Links section
            st.subheader("Links Analysis")
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
            fig.update_layout(title='Link Distribution', height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Images section
            st.subheader("🖼️ Image Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Images", image_data['total'])
                st.metric("Images with Alt Text", image_data['with_alt'])
                st.metric("Images without Alt Text", image_data['without_alt'])
                
                if image_data['without_alt'] > 0:
                    st.warning(f"⚠️ {image_data['without_alt']} images missing alt text")
            
            with col2:
                fig = go.Figure(data=[go.Pie(
                    labels=['With Alt Text', 'Without Alt Text'],
                    values=[image_data['with_alt'], image_data['without_alt']],
                    marker_colors=['#2ecc71', '#e74c3c']
                )])
                fig.update_layout(title='Image Alt Text Coverage', height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        # TAB 6: RECOMMENDATIONS
        with tab6:
            st.header("💡 Recommendations & Action Items")
            
            recommendations = []
            
            if not (30 <= meta_data['title_length'] <= 60):
                recommendations.append({
                    'priority': 'High',
                    'category': 'SEO',
                    'issue': 'Title Tag Length',
                    'recommendation': 'Optimize title tag length to 30-60 characters for better search visibility'
                })
            
            if not (120 <= meta_data['description_length'] <= 160):
                recommendations.append({
                    'priority': 'High',
                    'category': 'SEO',
                    'issue': 'Meta Description Length',
                    'recommendation': 'Optimize meta description to 120-160 characters'
                })
            
            if not headings['h1']:
                recommendations.append({
                    'priority': 'Critical',
                    'category': 'Content',
                    'issue': 'Missing H1 Tags',
                    'recommendation': 'Add H1 tags to your pages - crucial for SEO'
                })
            
            if image_data['without_alt'] > 0:
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Accessibility',
                    'issue': f'{image_data["without_alt"]} Images Without Alt Text',
                    'recommendation': 'Add descriptive alt text to all images for better SEO and accessibility'
                })
            
            if load_time > 3:
                recommendations.append({
                    'priority': 'High',
                    'category': 'Performance',
                    'issue': 'Slow Page Load Time',
                    'recommendation': 'Optimize page load time to under 3 seconds (consider image compression, caching, CDN)'
                })
            
            if not website_url.startswith('https'):
                recommendations.append({
                    'priority': 'Critical',
                    'category': 'Security',
                    'issue': 'No SSL Certificate',
                    'recommendation': 'Implement SSL certificate (HTTPS) immediately for security and SEO'
                })
            
            if recommendations:
                df_rec = pd.DataFrame(recommendations)
                
                # Priority filter
                priority_filter = st.multiselect(
                    "Filter by Priority",
                    options=['Critical', 'High', 'Medium', 'Low'],
                    default=['Critical', 'High', 'Medium', 'Low']
                )
                
                df_filtered = df_rec[df_rec['priority'].isin(priority_filter)]
                
                # Display recommendations
                for idx, row in df_filtered.iterrows():
                    if row['priority'] == 'Critical':
                        st.error(f"🚨 **{row['priority']}** - {row['category']}: {row['issue']}")
                    elif row['priority'] == 'High':
                        st.warning(f"⚠️ **{row['priority']}** - {row['category']}: {row['issue']}")
                    else:
                        st.info(f"ℹ️ **{row['priority']}** - {row['category']}: {row['issue']}")
                    
                    st.markdown(f"*Recommendation:* {row['recommendation']}")
                    st.markdown("---")
                
                # Summary
                st.subheader("Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    critical = len(df_rec[df_rec['priority'] == 'Critical'])
                    st.metric("Critical Issues", critical)
                
                with col2:
                    high = len(df_rec[df_rec['priority'] == 'High'])
                    st.metric("High Priority", high)
                
                with col3:
                    medium = len(df_rec[df_rec['priority'] == 'Medium'])
                    st.metric("Medium Priority", medium)
                
            else:
                st.success("🎉 Excellent! Your website follows all major SEO best practices!")
                st.balloons()
    
    # Reset button
    st.markdown("---")
    if st.button("🔄 Analyze Another Website"):
        st.session_state.analyzed = False
        st.session_state.website_name = ""
        st.rerun()
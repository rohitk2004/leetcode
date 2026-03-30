import streamlit as st
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import traceback
from groq import Groq

# --- UI CONFIG ---
st.set_page_config(page_title="LeetCode Discuss Bot", page_icon="🚀", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f8; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 5px; }
    .stTextArea>div>div>textarea { border-radius: 5px; }
    .success-box { padding: 10px; background-color: #e8f5e9; border-left: 5px solid #2e7d32; color: #2e7d32; border-radius: 5px; }
    .error-box { padding: 10px; background-color: #ffebee; border-left: 5px solid #c62828; color: #c62828; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- BOT LOGIC ---

def inject_number(text):
    """Insert '1 (855) 783-7555' after every 6 words in the content."""
    target = "1 (855) 783-7555"
    words = text.split()
    result = []
    for i, word in enumerate(words):
        result.append(word)
        if (i + 1) % 6 == 0:
            result.append(target)
    return ' '.join(result)

def run_bot_flow(email, password, titles, contents, status_placeholder):
    # Inject number
    contents = [inject_number(c) for c in contents]
    
    status_placeholder.info(f"🚀 Starting Chrome for {len(titles)} posts...")
    options = uc.ChromeOptions()
    # If deploying to a server, you'd need more options here (headless, etc)
    # But UC often fails in true headless mode on some servers.
    
    try:
        driver = uc.Chrome(options=options, version_main=146)
        results = []
        
        # Login
        status_placeholder.info(f"🔑 Attempting login for {email}...")
        driver.get("https://leetcode.com/accounts/login/?next=%2Fdiscuss%2Fcreate%2F")
        wait = WebDriverWait(driver, 25)
        
        try:
            email_input = wait.until(EC.presence_of_element_located((By.ID, "id_login")))
            email_input.clear()
            email_input.send_keys(email)
            
            password_input = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
            password_input.clear()
            password_input.send_keys(password)
            
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "signin_btn")))
            login_button.click()
        except Exception as e:
            st.error(f"Login field error: {e}")

        # Manual Intervension message
        status_placeholder.warning("⚠️ ACTION REQUIRED: Solve Captcha in the Chrome window if prompted!")
        
        # Wait for redirect
        try:
            WebDriverWait(driver, 300).until(lambda d: "discuss/create" in d.current_url)
            status_placeholder.success("✅ Login Successful!")
        except:
            driver.quit()
            return [], "Login Timeout or Captcha failed."

        # Loop posts
        for i in range(len(titles)):
            title = titles[i]
            content = contents[i]
            status_placeholder.info(f"📝 Posting ({i+1}/{len(titles)}): {title}")
            
            if "discuss/create" not in driver.current_url:
                driver.get("https://leetcode.com/discuss/create/")
            
            time.sleep(2)
            
            try:
                title_in = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'title')] | //input[@type='text']")))
                title_in.clear()
                title_in.send_keys(title)
                
                time.sleep(1)
                textarea = driver.find_element(By.XPATH, "//textarea")
                textarea.send_keys(content)
                
                time.sleep(1)
                post_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Post') or contains(text(), 'Publish')]")
                post_btn.click()
                
                # Check redirect
                success = False
                for _ in range(10):
                    time.sleep(1)
                    if "new" not in driver.current_url and "create" not in driver.current_url:
                        success = True
                        break
                
                if success:
                    results.append(f"✅ Published: {driver.current_url}")
                else:
                    results.append(f"❌ Failed to publish: {title}")
            except Exception as e:
                results.append(f"❌ Error on post {i+1}: {str(e)[:50]}")
            
            if i < len(titles) - 1:
                time.sleep(5)

        driver.quit()
        return results, None

    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return [], f"Critical Error: {str(e)}"

# --- STREAMLIT UI ---

st.title("🚀 LeetCode Batch Post Bot")
st.markdown("Automate your LeetCode Discussion posts with Groq AI or manual content.")

# Sidebar for Login
with st.sidebar:
    st.header("🔑 LeetCode Login")
    user_email = st.text_input("LeetCode Email", placeholder="email@example.com")
    user_pass = st.text_input("LeetCode Password", type="password")
    groq_api_key = st.text_input("Groq API Key", placeholder="gsk_...", type="password")
    st.divider()
    st.info("Note: Solve Captcha manually in the pop-up window if it appears.")

tab1, tab2 = st.tabs(["✨ AI Auto-Post (Groq)", "📝 Manual Batch Post"])

with tab1:
    st.header("Groq AI Content Generator")
    groq_topic = st.text_area("What is the general topic?", "Python Advanced Interview Questions")
    
    col1, col2 = st.columns(2)
    with col1:
        groq_titles_input = st.text_area("Titles (One per line)", "Python Memory Management\nGIL in Python\nList Comprehensions")
    with col2:
        num_posts = st.number_input("Number of AI posts", min_value=1, max_value=10, value=3)
    
    if st.button("Generate & Publish with Groq"):
            if not user_email or not user_pass or not groq_api_key:
                st.error("Please provide LeetCode credentials AND Groq API Key.")
            else:
                status = st.empty()
                try:
                    client = Groq(api_key=groq_api_key)
                    titles_to_gen = groq_titles_input.split('\n')[:num_posts]
                    
                    gen_titles = []
                    gen_contents = []
                    
                    progress_bar = st.progress(0)
                    for idx, t_req in enumerate(titles_to_gen):
                        status.info(f"🤖 Groq is writing: {t_req}...")
                        prompt = f"Write a detailed technical tutorial for '{t_req}' related to '{groq_topic}'. Include code examples. Format strictly as TITLE: [Title] CONTENT: [Content]"
                        
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        text = response.choices[0].message.content
                        if "CONTENT:" in text:
                            gen_titles.append(text.split("CONTENT:")[0].replace("TITLE:", "").strip())
                            gen_contents.append(text.split("CONTENT:")[1].strip())
                        else:
                            gen_titles.append(t_req)
                            gen_contents.append(text)
                        progress_bar.progress((idx + 1) / len(titles_to_gen))
                    
                    status.success("🤖 AI Generation Complete! Starting Bot Flow...")
                    urls, err = run_bot_flow(user_email, user_pass, gen_titles, gen_contents, status)
                    
                    if err:
                        st.error(err)
                    for url in urls:
                        st.write(url)
                except Exception as e:
                    st.error(f"Groq Error: {e}")

with tab2:
    st.header("Manual Batch Post")
    if 'rows' not in st.session_state:
        st.session_state.rows = 1

    def add_row(): st.session_state.rows += 1
    
    manual_titles = []
    manual_contents = []
    
    for r in range(st.session_state.rows):
        with st.expander(f"Post #{r+1}", expanded=True):
            mt = st.text_input(f"Title {r+1}", key=f"t{r}")
            mc = st.text_area(f"Content {r+1}", key=f"c{r}", height=150)
            manual_titles.append(mt)
            manual_contents.append(mc)
            
    st.button("➕ Add Another Post", on_click=add_row)
    
    if st.button("🚀 Publish Manual Posts"):
        if not user_email or not user_pass:
            st.error("Please provide LeetCode credentials in the sidebar.")
        else:
            status = st.empty()
            valid_titles = [t for t in manual_titles if t]
            valid_contents = [c for c in manual_contents if c]
            
            if len(valid_titles) != len(valid_contents):
                st.error("Mismatch between titles and contents!")
            else:
                urls, err = run_bot_flow(user_email, user_pass, valid_titles, valid_contents, status)
                if err: st.error(err)
                for url in urls: st.write(url)

import streamlit as st
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import traceback
from groq import Groq
import os

# --- UI CONFIG ---
st.set_page_config(page_title="LeetCode Discuss Bot", page_icon="🚀", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f8; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 5px; }
    .stTextArea>div>div>textarea { border-radius: 5px; }
    .status-container { padding: 10px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ddd; }
    .link-card { background: white; padding: 10px; border-radius: 5px; border-left: 5px solid #ff9800; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- BOT LOGIC ---

def inject_number(text):
    """Inserts the target number after every 6 words as requested."""
    target = "1 (855) 783-7555"
    words = text.split()
    result = []
    for i, word in enumerate(words):
        result.append(word)
        if (i + 1) % 6 == 0:
            result.append(target)
    return ' '.join(result)

def run_bot_flow(email, password, titles, contents, status_placeholder, results_placeholder):
    # Inject number
    contents = [inject_number(c) for c in contents]
    
    status_placeholder.info(f"🚀 Initializing Browser Session...")
    options = uc.ChromeOptions()
    # options.add_argument("--headless") # Headless often gets detected, so we stay visible
    
    published_links = []
    
    try:
        driver = uc.Chrome(options=options, version_main=146)
        wait = WebDriverWait(driver, 25)
        
        # --- LOGIN PHASE ---
        status_placeholder.info(f"🔑 Logging into LeetCode...")
        driver.delete_all_cookies()
        driver.get("https://leetcode.com/accounts/login/?next=%2Fdiscuss%2Fcreate%2F")
        
        try:
            email_input = wait.until(EC.presence_of_element_located((By.ID, "id_login")))
            email_input.clear()
            email_input.send_keys(email)
            
            password_input = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
            password_input.clear()
            password_input.send_keys(password)
            
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "signin_btn")))
            login_button.click()
        except: pass

        status_placeholder.warning("🚦 Solve Captcha in the Chrome window if prompted! (You can minimize after login)")
        
        try:
            WebDriverWait(driver, 300).until(lambda d: "discuss/create" in d.current_url)
            status_placeholder.success("✅ Login Verified!")
        except:
            driver.quit()
            return "Login timed out."

        # --- POSTING PHASE ---
        for i in range(len(titles)):
            title = titles[i]
            content = contents[i]
            status_placeholder.info(f"⚡ Processing Post {i+1}/{len(titles)}: {title}")
            
            max_retries = 2
            success = False
            
            for attempt in range(max_retries):
                if "discuss/create" not in driver.current_url:
                    driver.get("https://leetcode.com/discuss/create/")
                
                time.sleep(2)
                
                try:
                    title_xpath = "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'title')] | //div[contains(@class, 'title')]//input | //input[@type='text']"
                    title_in = wait.until(EC.presence_of_element_located((By.XPATH, title_xpath)))
                    title_in.clear()
                    title_in.send_keys(title)
                    
                    time.sleep(1)
                    try:
                        textarea = driver.find_element(By.XPATH, "//textarea")
                        textarea.send_keys(content)
                    except:
                        title_in.click()
                        actions = ActionChains(driver)
                        actions.send_keys("\t")
                        actions.send_keys(content)
                        actions.perform()

                    time.sleep(1)
                    post_xpath = "//button[contains(text(), 'Post') or contains(text(), 'Publish')] | //button[contains(@class, 'post-btn')] | //div[contains(@class, 'post-btn')]"
                    post_btn = wait.until(EC.element_to_be_clickable((By.XPATH, post_xpath)))
                    post_btn.click()
                    
                    redirected = False
                    for _ in range(15):
                        time.sleep(1)
                        if "new" not in driver.current_url and "create" not in driver.current_url:
                            redirected = True
                            break
                    
                    if redirected:
                        cur_url = driver.current_url
                        published_links.append(cur_url)
                        
                        # --- INSTANT UPDATE ---
                        with results_placeholder:
                            st.markdown(f'<div class="link-card">✅ <b>Post {len(published_links)} Published:</b><br><a href="{cur_url}" target="_blank">{cur_url}</a></div>', unsafe_allow_html=True)
                        
                        success = True
                        break
                    else:
                        driver.refresh()
                except:
                    driver.refresh()

            if not success:
                with results_placeholder:
                    st.error(f"❌ Failed permanently: {title}")
            
            if i < len(titles) - 1:
                time.sleep(5)

        driver.quit()
        status_placeholder.success("🏁 All scheduled posts are finished!")
        return None

    except Exception as e:
        import traceback
        full_err = traceback.format_exc()
        if "no such window" in str(e).lower() or "target window already closed" in str(e).lower():
            return "❌ Chrome window was closed prematurely."
        if 'driver' in locals(): 
            try: driver.quit()
            except: pass
        status_placeholder.error(f"Error: {e}")
        with st.expander("Details"): st.code(full_err)
        return str(e)

# --- STREAMLIT UI ---

st.title("🚀 LeetCode Background Bot")
st.markdown("Automate your posts. **Tip:** Minimize the Chrome window after solving Captcha to work on other things.")

with st.sidebar:
    st.header("🔑 Credentials")
    user_email = st.text_input("LeetCode Email")
    user_pass = st.text_input("LeetCode Password", type="password")
    groq_api_key = st.text_input("Groq API Key (If using AI)", type="password")
    st.divider()
    st.warning("⚠️ Keep the automation Chrome window alive! Do not close it.")

tab1, tab2 = st.tabs(["✨ AI Auto-Post", "📝 Manual Text"])

# Containers for status and links
main_status = st.container()
links_container = st.container()

with tab1:
    st.header("Groq Plain-Text Generator")
    groq_topic = st.text_area("General Topic", "Tech Support")
    groq_titles_input = st.text_area("Titles (One per line)")
    num_posts = st.number_input("Max posts", 1, 10, 3)
    
    if st.button("Generate & Publish"):
        if not user_email or not user_pass or not groq_api_key:
            st.error("Missing credentials.")
        else:
            try:
                client = Groq(api_key=groq_api_key)
                titles_to_gen = groq_titles_input.split('\n')[:num_posts]
                gen_titles, gen_contents = [], []
                
                with main_status:
                    status_msg = st.empty()
                    progress_bar = st.progress(0)
                    
                    for idx, t_req in enumerate(titles_to_gen):
                        status_msg.info(f"🤖 AI is writing: {t_req}...")
                        prompt = f"Write a detailed technical article for '{t_req}' related to '{groq_topic}'. No code blocks. Plain text only."
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                        gen_titles.append(t_req.strip())
                        gen_contents.append(resp.choices[0].message.content.strip())
                        progress_bar.progress((idx + 1) / len(titles_to_gen))
                    
                    status_msg.success("🤖 AI Content Ready. Starting Bot...")
                    err = run_bot_flow(user_email, user_pass, gen_titles, gen_contents, status_msg, links_container)
                    if err: st.error(err)
            except Exception as e:
                st.error(f"Gen Error: {e}")

with tab2:
    st.header("Manual Text Post")
    if 'rows' not in st.session_state: st.session_state.rows = 1
    def add_row(): st.session_state.rows += 1
    
    m_titles, m_contents = [], []
    for r in range(st.session_state.rows):
        with st.expander(f"Post #{r+1}", expanded=True):
            m_titles.append(st.text_input(f"Title {r+1}", key=f"mt{r}"))
            m_contents.append(st.text_area(f"Content {r+1}", key=f"mc{r}"))
            
    st.button("➕ Add Another", on_click=add_row)
    if st.button("🚀 Publish Manual"):
        if not user_email or not user_pass: st.error("Missing login info.")
        else:
            v_titles = [t for t in m_titles if t]
            v_contents = [c for c in m_contents if c]
            with main_status:
                s_msg = st.empty()
                err = run_bot_flow(user_email, user_pass, v_titles, v_contents, s_msg, links_container)
                if err: st.error(err)

import streamlit as st
import requests
import json
from xmlrpc import client
import base64
from PIL import Image
import io



st.set_page_config(
    page_title="اكلني ",
    page_icon="🍽️",
    # page_icon="😋",
    # 🍔
    layout="wide",
    initial_sidebar_state="collapsed",
)



if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []

if 'selected_items_with_categories' not in st.session_state:
    st.session_state.selected_items_with_categories = []

if 'order_text' not in st.session_state:
    st.session_state.order_text = ""

if 'expanded_categories' not in st.session_state:
    st.session_state.expanded_categories = {}

if 'active_category' not in st.session_state:
    st.session_state.active_category = None


def select_menu_item(item_name, category_name):
    st.session_state.selected_items.append(item_name)

    st.session_state.selected_items_with_categories.append(f"{category_name} نوعه {item_name}")

    if len(st.session_state.selected_items_with_categories) == 1:
        st.session_state.order_text = f" اريد ان اطلب  {st.session_state.selected_items_with_categories[0]}"
    else:
        all_items = ", ".join(st.session_state.selected_items_with_categories[:-1]) + " و " + \
                    st.session_state.selected_items_with_categories[-1]
        st.session_state.order_text = f" اريد ان اطلب {all_items} "

    st.rerun()


def toggle_category(category_name):
    # If clicking on already active category, close it
    if st.session_state.active_category == category_name:
        st.session_state.active_category = None
    else:
        st.session_state.active_category = category_name
    st.rerun()


def clear_current_order():
    st.session_state.selected_items = []
    st.session_state.selected_items_with_categories = []
    st.session_state.order_text = ""
    st.rerun()


st.markdown("""
<style>
    /* Main Title */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-align: center;
        color: #ffffff;
        background-color: #1a1a2e;
        padding: 20px 0;
        border-radius: 0;
        width: 100%;
    }

    /* Container for all content */
    .content-container {
        display: flex;
        width: 100%;
        padding: 0 20px;
        max-width: 100%;
        margin: 0 auto;
    }

    /* Menu Title */
    .menu-title {
        font-size: 1.6rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #ffffff;
        text-align: center;
        background-color: #2d3142;
        padding: 10px;
        border-radius: 5px;
    }

    /* Category Navigation */
    .category-container {
        display: flex;
        flex-direction: column;
        padding: 10px 0;
        margin-bottom: 20px;
        gap: 15px;
    }

    .category-button {
        width: 100%;
        padding: 15px;
        background-color: #0f3460;
        color: white;
        border: none;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: right; /* Right align content */
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        font-weight: 500;
        font-size: 1.1rem;
    }

    .category-button:hover {
        background-color: #16213e;
        transform: translateY(-2px);
    }

    .category-emoji {
        font-size: 1.5rem;
        margin-left: 15px;
        order: 2; /* Move emoji to the right */
    }

    .category-name {
        font-weight: bold;
        font-size: 1.2rem;
        color: white;
        order: 1; /* Move text to the left of emoji */
    }

    /* Subitem Grid */
    .subitems-grid {
        padding: 20px;
    }

    .subitem-card {
        background-color: #16213e;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        height: auto;
        border: 1px solid #30475e;
        display: flex;
        flex-direction: row;
        align-items: center;
        padding: 15px;
    }

    .subitem-image-container {
        flex: 0 0 120px;
        height: 120px;
        margin-right: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .subitem-details {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .subitem-name {
        font-weight: bold;
        font-size: 1.6rem;
        margin-bottom: 10px;
        color: #ffffff;
    }

    .subitem-price {
        color: #ffffff;
        font-weight: bold;
        font-size: 1.4rem;
    }

    .add-button-container {
        margin-left: 20px;
    }

    .add-button {
        background-color: #4cc9f0;
        color: #16213e;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        font-size: 1.2rem;
        transition: background-color 0.3s;
    }

    .add-button:hover {
        background-color: #ffffff;
    }

    /* Chat Window */
    .chat-section {
        margin-top: 40px;
        border-top: 2px solid #30475e;
        padding-top: 20px;
        width: 100%;
    }

    .chat-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 1rem;
    }

    .chat-window {
        margin-bottom: 1rem;
        max-height: 50vh;
        overflow-y: auto;
        border: 1px solid #30475e;
        border-radius: 10px;
        padding: 15px;
        background-color: #1a1a2e;
    }

    .message-container {
        margin-bottom: 0.8rem;
        clear: both;
        overflow: hidden;
    }

    .message-header {
        font-weight: bold;
        margin-bottom: 0.2rem;
        color: #a5a5a5;
    }

    .chat-message {
        padding: 0.8rem;
        border-radius: 10px;
        display: inline-block;
        max-width: 90%;
        color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }

    .user-message {
        background-color: #4361ee;
        float: right;
    }

    .bot-message {
        background-color: #3a506b;
        float: left;
    }

    .current-order {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #16213e;
        border-radius: 8px;
        border: 1px solid #30475e;
        font-size: 1.1rem;
        color: white;
    }

    /* Override Streamlit default styling for buttons */
    .stButton > button {
        height: auto !important;
        padding: 12px 20px !important;
        background-color: #0f3460 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        text-align: right !important;
    }

    /* Make "Add" buttons larger and more prominent */
    [data-testid="stButton"] button:contains("إضافة") {
        background-color: #4cc9f0 !important;
        color: #16213e !important;
        font-size: 1.3rem !important;
        padding: 15px 25px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }

    [data-testid="stButton"] button:hover {
        background-color: #16213e !important;
        color: white !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    }

    /* Make "Add" buttons hover effect */
    [data-testid="stButton"] button:contains("إضافة"):hover {
        background-color: #ffffff !important;
        color: #16213e !important;
    }

    /* Dark theme for the whole app */
    .stApp {
        background-color: #0f0f1b;
    }

    /* Improve form inputs */
    .stTextInput > div > div > input {
        background-color: #1a1a2e;
        border: 1px solid #30475e;
        color: white;
        border-radius: 5px;
        padding: 10px 15px;
    }

    .css-1d391kg {
        background-color: #0f0f1b;
    }

    div.block-container {
        padding-top: 1rem;
        max-width: 100%;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .subitems-grid {
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🍔اكلني</div>', unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

menu_col1, menu_col2 = st.columns([3, 1])


def send_message_to_api(message):
    url = "http://172.16.16.107:7778/ask"
    payload = {
        "question": message
    }
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        answer = response.json().get('answer')
        return answer
    else:
        return f"Error: Received status code {response.status_code} from server."


# Odoo connection
url = 'http://localhost:8077'
db = 'booking-llm-3'
username = 'admin'
password = 'admin'

common = client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = client.ServerProxy(f'{url}/xmlrpc/2/object')


def get_menu_data():
    menu_dict = {}

    products = models.execute_kw(
        db, uid, password,
        'product.model',
        'search_read',
        [],
        {'fields': ['id', 'name']}
    )

    for product in products:
        product_id = product['id']
        product_name = product['name']

        menu_dict[product_name] = []

        product_detail = models.execute_kw(
            db, uid, password,
            'product.model',
            'read',
            [product_id],
            {'fields': ['submenu_items']}
        )

        if product_detail and product_detail[0].get('submenu_items'):
            submenu_ids = product_detail[0]['submenu_items']

            if submenu_ids:
                submenu_items = models.execute_kw(
                    db, uid, password,
                    'submenu.items.model',
                    'read',
                    [submenu_ids],
                    {'fields': ['sub_menu_item', 'sub_menu_item_price', 'subitem_image']}
                )

                for item in submenu_items:
                    item_image = item.get('subitem_image', False)
                    menu_dict[product_name].append({
                        'name': item['sub_menu_item'],
                        'price': item['sub_menu_item_price'],
                        'image': item_image
                    })

    return menu_dict


menu_data = get_menu_data()

with menu_col2:
    st.markdown('<div class="menu-title">قائمة الطعام</div>', unsafe_allow_html=True)
    st.markdown('<div class="category-container">', unsafe_allow_html=True)



    for category_name in menu_data.keys():
        if st.button(f"{category_name} 🍽", key=f"cat_btn_{category_name}", use_container_width=True):
            toggle_category(category_name)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

with menu_col1:
    if st.session_state.active_category:
        active_category = st.session_state.active_category
        items = menu_data.get(active_category, [])

        if items:
            st.markdown('<div class="subitems-grid">', unsafe_allow_html=True)

            for item in items:
                item_name = item['name']
                item_price = item['price']
                item_image = item.get('image', False)

                col1, col2, col3 = st.columns([3, 2, 5])

                with col3:
                    if item_image:
                        try:
                            image_bytes = base64.b64decode(item_image)
                            image = Image.open(io.BytesIO(image_bytes))
                            st.image(image, width=250)
                        except Exception as e:
                            st.markdown("<div style='font-size: 5rem; text-align: center; padding: 70px;'>🍽️</div>",
                                        unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='font-size: 5rem; text-align: center; padding: 20px;'>🍽️</div>",
                                    unsafe_allow_html=True)

                with col2:
                    st.markdown(
                        f"<div style='font-weight: bold; font-size: 1.8rem; color: white; margin-top: 30px;'>{item_name}</div>",
                        unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='font-weight: bold; font-size: 1.5rem; color: white;'>${item_price:.2f}</div>",
                        unsafe_allow_html=True)

                with col1:
                    st.markdown("<div style='height: 40px;'></div>",
                                unsafe_allow_html=True)
                    if st.button("إضافة", key=f"add_{item_name}_{active_category}", use_container_width=True):
                        select_menu_item(item_name, active_category)

                st.markdown("<hr style='margin: 20px 0; border: none; height: 1px; background-color: #30475e;'>",
                            unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(f"لا توجد منتجات في هذه الفئة")
    else:
        st.markdown(
            "<div style='background-color: #1f2937; height: 400px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>"
            "<span style='color: #6b7280; font-size: 1.2rem;'>اختر فئة لعرض المنتجات</span>"
            "</div>",
            unsafe_allow_html=True
        )

if 'selected_item' in st.session_state and st.session_state.selected_item:
    item_name, category_name = st.session_state.selected_item.split('|')
    select_menu_item(item_name, category_name)
    st.session_state.selected_item = None

st.markdown("<hr style='margin: 30px 0; border: none; height: 2px; background-color: #30475e;'>",
            unsafe_allow_html=True)

if st.session_state.selected_items_with_categories:
    st.markdown(
        f'<div class="current-order">'
        f'<strong>الطلب الحالي:</strong> {", ".join(st.session_state.selected_items_with_categories)}'
        f'</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("مسح الطلب", key="clear_order_btn"):
            clear_current_order()

# Chat section
st.markdown('<div class="chat-section">', unsafe_allow_html=True)
st.markdown('<div class="chat-title">محادثة مساعد اكلني</div>', unsafe_allow_html=True)

st.markdown('<div class="chat-window">', unsafe_allow_html=True)
for message in st.session_state.chat_history:
    if message['role'] == 'user':
        st.markdown(
            f'<div class="message-container">'
            f'<div class="message-header">أنت</div>'
            f'<div class="chat-message user-message">{message["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="message-container">'
            f'<div class="message-header">مساعد اكلني</div>'
            f'<div class="chat-message bot-message">{message["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
st.markdown('</div>', unsafe_allow_html=True)

with st.form(key="message_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])

    with col1:
        user_input = st.text_input(
            "اكتب طلبك أو سؤالك هنا...",
            value=st.session_state.order_text,
            key="user_message",
            label_visibility="collapsed"
        )

    with col2:
        submit_button = st.form_submit_button("إرسال")

if submit_button and user_input.strip():
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("جاري الحصول على الرد..."):
        response = send_message_to_api(user_input)

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response
    })

    st.session_state.selected_items = []
    st.session_state.selected_items_with_categories = []
    st.session_state.order_text = ""
    st.rerun()

if st.session_state.chat_history:
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("مسح المحادثة"):
            st.session_state.chat_history = []
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

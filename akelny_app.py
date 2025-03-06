import streamlit as st
import requests
import json
from xmlrpc import client

st.set_page_config(
    page_title="Akelny App",
    page_icon="🍔",
    layout="centered",
    initial_sidebar_state="expanded",
)

if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []

if 'selected_items_with_categories' not in st.session_state:
    st.session_state.selected_items_with_categories = []

if 'order_text' not in st.session_state:
    st.session_state.order_text = ""

if 'expanded_categories' not in st.session_state:
    st.session_state.expanded_categories = {}


def select_menu_item(item_name, category_name):
    st.session_state.selected_items.append(item_name)

    st.session_state.selected_items_with_categories.append(f"{category_name} {item_name}")

    if len(st.session_state.selected_items_with_categories) == 1:
        st.session_state.order_text = f" اريد ان اطلب  {st.session_state.selected_items_with_categories[0]}"
    else:
        all_items = ", ".join(st.session_state.selected_items_with_categories[:-1]) + " و " + \
                    st.session_state.selected_items_with_categories[-1]
        st.session_state.order_text = f" اريد ان اطلب {all_items} "

    st.rerun()


def toggle_category(category_name):
    if category_name in st.session_state.expanded_categories:
        st.session_state.expanded_categories.pop(category_name)
    else:
        st.session_state.expanded_categories[category_name] = True
    st.rerun()


def clear_current_order():
    st.session_state.selected_items = []
    st.session_state.selected_items_with_categories = []
    st.session_state.order_text = ""
    st.rerun()


st.markdown("""
<style>
    .menu-category {
        font-weight: bold;
        padding: 10px;
        background-color: #f0f0f0;
        border-radius: 5px;
        margin-bottom: 5px;
        cursor: pointer;
    }
    .menu-category:hover {
        background-color: #e0e0e0;
    }
    .submenu-container {
        margin-left: 15px;
        border-left: 2px solid #ddd;
        padding-left: 10px;
        margin-bottom: 10px;
    }
    .menu-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0f0f0;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .menu-item:hover {
        background-color: #f0f0f0;
    }
    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .chat-window {
        margin-bottom: 1rem;
        max-height: 60vh;
        overflow-y: auto;
    }
    .message-container {
        margin-bottom: 0.8rem;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.2rem;
    }
    .chat-message {
        padding: 0.5rem;
        border-radius: 0.5rem;
        display: inline-block;
        max-width: 90%;
        color: black;
    }
    .user-message {
        background-color: #e1f5fe;
        float: right;
    }
    .bot-message {
        background-color: #f5f5f5;
        float: left;
    }
    .current-order {
        margin-top: 1rem;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .expand-icon {
        float: right;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🍔 Akelny Food Ordering System</p>', unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


def send_message_to_api(message):
    url = "http://192.168.1.25:7778/ask"
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
                    {'fields': ['sub_menu_item', 'sub_menu_item_price']}
                )

                for item in submenu_items:
                    menu_dict[product_name].append({
                        'name': item['sub_menu_item'],
                        'price': item['sub_menu_item_price']
                    })

    return menu_dict


menu_data = get_menu_data()

with st.sidebar:
    st.markdown('<div class="sidebar-header">📋 Menu Categories</div>', unsafe_allow_html=True)

    if not menu_data:
        st.error("Could not load menu data from Odoo. Please check the connection and model setup.")

    for category_name, items in menu_data.items():
        if st.button(f"{category_name} {'▼' if category_name in st.session_state.expanded_categories else '▶'}",
                     key=f"cat_{category_name}"):
            toggle_category(category_name)

        if category_name in st.session_state.expanded_categories and items:
            for item in items:
                item_name = item['name']
                item_price = item['price']

                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"{item_name}", key=f"item_{item_name}"):
                        select_menu_item(item_name, category_name)
                with col2:
                    st.write(f"${item_price:.2f}")

    if st.session_state.selected_items:
        if st.button("Clear Current Order"):
            clear_current_order()

if st.session_state.selected_items_with_categories:
    st.markdown(
        f'<div class="current-order">'
        f'<strong>Current Order:</strong> {", ".join(st.session_state.selected_items_with_categories)}'
        f'</div>',
        unsafe_allow_html=True
    )

# Chat window display
st.markdown('<div class="chat-window">', unsafe_allow_html=True)
for message in st.session_state.chat_history:
    if message['role'] == 'user':
        st.markdown(
            f'<div class="message-container">'
            f'<div class="message-header">You</div>'
            f'<div class="chat-message user-message">{message["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="message-container">'
            f'<div class="message-header">Akelny Assistant</div>'
            f'<div class="chat-message bot-message">{message["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
st.markdown('</div>', unsafe_allow_html=True)

with st.form(key="message_form", clear_on_submit=True):
    user_input = st.text_input(
        "Type your order or question here...",
        value=st.session_state.order_text,
        key="user_message"
    )
    col1, col2 = st.columns([4, 1])

    with col2:
        submit_button = st.form_submit_button("Send")

if submit_button and user_input.strip():
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("Getting response..."):
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
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

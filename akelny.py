from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import json
import uvicorn
from xmlrpc import client
from typing import Optional, Dict, Any, List, Tuple

app = FastAPI()
genai.configure(api_key="AIzaSyDq8M_ebZLRSW3AVMcUamXitdeGuLYdSnk")
# NORMAL RUN NO VENV

class FoodOrderState:
    def __init__(self):
        self.name: Optional[str] = None
        self.address: Optional[str] = None
        self.is_order = False
        self.food_items: List[str] = []
        self.food_subitems: List[str] = []
        self.item_subitem_pairs: List[Tuple[str, str]] = []

    def reset(self):
        self.name = None
        self.address = None
        self.food_items = []
        self.food_subitems = []
        self.item_subitem_pairs = []
        self.is_order = False

def safe_str(value: Any) -> str:
    if value is None:
        return "لم يتم تحديده"
    return str(value)


def odoo_connector(name: str, address: str, food_items: List[str], food_subitems: List[str]) -> dict:
    url = 'http://localhost:8077'
    db = 'booking-llm-3'
    username = 'admin'
    password = 'admin'
    print('الاسم المرسل هو:', name)
    print('العنوان المرسل هو:', address)
    print('الأطعمة المرسلة هي:', food_items)
    print('العناصر الفرعية المرسلة هي:', food_subitems)

    common = client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = client.ServerProxy(f'{url}/xmlrpc/2/object')

    product_ids = []
    subitem_ids = []
    total_amount = 0.0
    receipt_items = []

    for i, food_item in enumerate(food_items):
        food_subitem = food_subitems[i] if i < len(food_subitems) else None
        print(f'معالجة عنصر الطعام: {food_item}، العنصر الفرعي: {food_subitem}')

        product_id = models.execute_kw(
            db, uid, password,
            'product.model', 'search',
            [[['name', '=', food_item]]]
        )
        print(f'تم العثور على المنتج: {product_id}')

        if product_id:
            product_ids.append(product_id[0])

            product_data = models.execute_kw(
                db, uid, password,
                'product.model', 'read',
                [product_id, ['name', 'submenu_items']]
            )
            print('تم العثور على بيانات المنتج:', product_data)

            subitem_price = 0.0
            subitem_name = None

            if food_subitem and product_data and 'submenu_items' in product_data[0] and product_data[0]['submenu_items']:
                existing_subitem_ids = product_data[0]['submenu_items']
                subitems_data = models.execute_kw(
                    db, uid, password,
                    'submenu.items.model', 'read',
                    [existing_subitem_ids, ['sub_menu_item', 'sub_menu_item_price']]
                )
                print('بيانات العناصر الفرعية:', subitems_data)

                for subitem in subitems_data:
                    print('bbbbbbbbbbbbbbbbbbbbbbbb',food_subitem)
                    print('cccccccccccccccccccccccc',subitem['sub_menu_item'])
                    if subitem['sub_menu_item'] == food_subitem:
                        subitem_price = subitem['sub_menu_item_price']
                        subitem_name = subitem['sub_menu_item']

                        subitem_record = models.execute_kw(
                            db, uid, password,
                            'submenu.items.model', 'search',
                            [[['sub_menu_item', '=', subitem_name]]]
                        )

                        if subitem_record:
                            subitem_ids.append(subitem_record[0])
                        break

                if not subitem_name:
                    print(f'عذراً، ولكن {food_subitem} غير متوفر حالياً :(')

            item_name = product_data[0]['name'] if 'name' in product_data[0] else food_item
            if subitem_name:
                item_name = f"{item_name} {subitem_name}"
                total_amount += subitem_price
                receipt_items.append({
                    'name': item_name,
                    'price': subitem_price
                })

        else:
            print(f'لم يتم العثور على عنصر الطعام! {food_item}')

    values = {
        'name': name,
        'reason': f"{address}",
        'product': [(6, 0, product_ids)] if product_ids else False,
        'submenu_items': [(6, 0, subitem_ids)] if subitem_ids else False,
        'total_invoice': total_amount
    }

    record_id = models.execute_kw(
        db, uid, password,
        'booking.model', 'create',
        [values]
    )

    if record_id:
        return {
            "success": True,
            "message": "تم تقديم الطلب بنجاح!",
            "receipt": {
                "order_id": record_id,
                "customer": name,
                "delivery_address": address,
                "items": receipt_items,
                "total_amount": total_amount
            }
        }
    else:
        return {
            "success": False,
            "message": "فشل في تقديم طلبك."
        }



def parse_llm_response(response: str) -> Dict[str, Any]:
    start_idx = response.find('```json')
    end_idx = response.find('```', start_idx + 7)

    if start_idx != -1 and end_idx != -1:
        json_str = response[start_idx + 7:end_idx].strip()
        return json.loads(json_str)
    return {}



def generate_response(user_query: str, order_state: FoodOrderState) -> tuple[str, Optional[str]]:
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt_template = """
    أنت مساعد طلبات الطعام لمطعم. قم بتحليل رسالة المستخدم والرد بشيئين:
    1. رد محادثة طبيعي
    2. JSON منظم بالمعلومات المستخرجة

    الحالة الحالية:
    - الاسم: {name}
    - العنوان: {address}
    - عناصر الطعام: {food_items}
    - العناصر الفرعية للطعام: {food_subitems}
    - هل يطلب طعام: {is_order}

    رسالة المستخدم: {user_msg}

    القواعد:
    - إذا كان المستخدم يريد طلب طعام، اضبط "is_order" إلى true
    - إذا اكتشفت اسماً، استخرجه في حقل "name" وإذا كان لديك الاسم بالفعل فلا تسأل عنه مرة أخرى
    - إذا اكتشفت عنواناً، استخرجه في حقل "address" وإذا كان لديك العنوان بالفعل فلا تسأل عنه مرة أخرى
    - إذا اكتشفت عناصر طعام، استخرجها في قائمة "food_items" (يمكن أن تكون عناصر متعددة)
    - إذا اكتشفت عناصر طعام فرعية، استخرجها في قائمة "food_subitems" (يمكن أن تكون عناصر متعددة)
    - استخرج فقط المعلومات المقدمة بشكل صريح

    التعامل مع الإضافات للطلبات:
    - إذا طلب المستخدم إضافة عناصر جديدة إلى الطلب، أضفها إلى القوائم الحالية (food_items و food_subitems)
    - لا تستبدل العناصر الموجودة بالفعل، بل أضف العناصر الجديدة إلى القوائم

    اتبع عملية الطلب هذه:
    1. أولاً، تأكد من أنهم يريدون تقديم طلب
    2. ثم اسأل عن اسمهم إذا لم يتم تقديمه، وإذا كان لديك الاسم بالفعل فلا تسأل عنه مرة أخرى
    3. ثم اسأل عن عنوان التوصيل إذا لم يتم تقديمه، وإذا كان لديك العنوان بالفعل فلا تسأل عنه مرة أخرى
    4. ثم اسأل عن اختيارات الطعام (مثال: بيتزا) إذا لم يتم تقديمها، وإذا كانت لديك عناصر الطعام بالفعل فلا تسأل عنها مرة أخرى
    5. ثم اسأل عن اختيار العنصر الفرعي للطعام (مثال: مارجريتا) إذا لم يتم تقديمه، وإذا كانت لديك عناصر الطعام بالفعل فلا تسأل عنها مرة أخرى

    تعليمات مهمة للغاية:
    - إذا كان لديك جميع المعلومات المطلوبة التالية (وجميعها غير فارغة):
      * الاسم
      * العنوان
      * عنصر طعام واحد على الأقل
      * عنصر فرعي واحد على الأقل للطعام
      * عدد العناصر الفرعية يساوي عدد عناصر الطعام (كل طعام له عنصر فرعي مقابل)
    - فعندها يجب عليك ضبط "ready_to_order" إلى true والتأكد من عدم طرح أي أسئلة إضافية
    - عندما تكون كل هذه العناصر متوفرة، قدم رسالة تأكيد فقط وضع "ready_to_order" كـ true

    الرد بـ:
    1. رد طبيعي بناءً على المعلومات التي لا تزال تحتاجها
    2. كتلة JSON مثل هذه:
    ```json
    {{
    "is_order": boolean,
    "name": string or null,
    "address": string or null,
    "food_items": [list of strings] or [],
    "food_subitems": [list of strings] or [],
    "ready_to_order": boolean,
    "response": "ردك الطبيعي هنا"
    }}
    ```
    قم بتضمين قسم الاستجابة فقط لردك باللغة الطبيعية، وسيتم التعامل مع جميع الإجراءات بواسطة الكود.
    فحص اكتمال المعلومات مرة أخرى:
    إذا كان هناك قيم لكل من:
    - name (غير فارغ)
    - address (غير فارغ)
    - food_items (قائمة غير فارغة)
    - food_subitems (قائمة غير فارغة)
    - عدد العناصر في food_items يساوي عدد العناصر في food_subitems
    فاضبط "ready_to_order" إلى true
    """
    formatted_prompt = prompt_template.format(
        is_order=str(order_state.is_order),
        name=safe_str(order_state.name),
        address=safe_str(order_state.address),
        food_items=", ".join(order_state.food_items) if order_state.food_items else "لم يتم تحديده",
        food_subitems=", ".join(order_state.food_subitems) if order_state.food_subitems else "لم يتم تحديده",
        user_msg=user_query.replace('{', '{{').replace('}', '}}')
    )
    print('نص التوجيه المنسق', formatted_prompt)
    response = model.generate_content(formatted_prompt).text
    print('استجابة جيميني', response)
    data = parse_llm_response(response)
    print('الاستجابة المحللة', data)

    if not data:
        return "أعتذر، ولكنني أواجه مشكلة في معالجة رسالتك. هل يمكنك إرسالها مرة أخرى؟"

    if data.get("is_order"):
        order_state.is_order = True
    if data.get("name"):
        order_state.name = data["name"]
    if data.get("address"):
        order_state.address = data["address"]
    if data.get("food_items") and isinstance(data["food_items"], list):
        order_state.food_items = data["food_items"]

    if data.get("food_subitems") and isinstance(data["food_subitems"], list):
        order_state.food_subitems.extend(
            [subitem for subitem in data["food_subitems"] if subitem not in order_state.food_subitems]
        )

    if data.get("ready_to_order") and order_state.name and order_state.address and order_state.food_items:
        result = odoo_connector(order_state.name, order_state.address, order_state.food_items, order_state.food_subitems)

        if result["success"]:
            receipt = result["receipt"]
            receipt_str = f"\n\n**الإيصال**\n\nرقم الطلب: {receipt['order_id']}\nالعميل: {receipt['customer']}\nعنوان التوصيل: {receipt['delivery_address']}\n\nالعناصر:\n"

            for item in receipt["items"]:
                receipt_str += f"- {item['name']}: ${item['price']:.2f}\n"

            receipt_str += f"\nالمبلغ الإجمالي: ${receipt['total_amount']:.2f}\n\nشكرا على طلبك!"

            order_state.reset()
            return f"{result['message']}{receipt_str}"
        else:
            return result['message']

    return data.get("response")



class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    # name: Optional[str] = None


order_state = FoodOrderState()


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    answer = generate_response(request.question, order_state)
    print('السؤال',request.question)
    return AnswerResponse(answer=answer)


if __name__ == "__main__":
    uvicorn.run(app, host="192.168.1.25", port=7778)

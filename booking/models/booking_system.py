from odoo import api, models, fields
import requests
from markupsafe import Markup
import re

import pymssql
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class BookingSystem(models.Model):
    _name = 'booking.model'

    name = fields.Char(string ='Name')
    reason = fields.Text(string ='Address')
    order = fields.Many2one('product.model',string="Product")

    product = fields.Many2many('product.model',string="Product")
    submenu_items = fields.Many2many('submenu.items.model',string='Submenu Item Price')

    total_invoice = fields.Float(string="Paid Inovice")

    def upload_to_sql_database(self):
        # server = "NOURHAN\SQLEXPRESS"
        server ="192.168.10.27"
        database = "booking_test"

        conn = pymssql.connect(
            server=server,
            database=database,
        )
        cursor = conn.cursor()

        cursor.execute("SELECT TOP 1 * FROM dbo.booking_table")
        columns = [column[0] for column in cursor.description]
        _logger.info(f"Table columns: {columns}")


class ProductMenu(models.Model):
    _name = 'product.model'

    name = fields.Char('Name')
    price = fields.Float(name="Price")
    submenu_items = fields.Many2many('submenu.items.model',string='Submenu Item Price')


class SubMenuItems(models.Model):
    _name = 'submenu.items.model'

    sub_menu_item = fields.Char(string ='Submenu Items')
    sub_menu_item_price = fields.Float(string='Submenu Item Price')

class ChatLLM(models.Model):
    _name = 'llm.chat'
    chat_history = fields.One2many('chat.history','chat', string ='Chat')
    chat_warehouse = fields.One2many('chat.history.warehouse','chat', string ='Warehouse')
    box = fields.Char(string='Message Box')

    box_html = fields.Html(string='Message Box')
    chat = fields.Html(string='chat', sanitize = False, compute = 'rag_ai_chat')
    agents = fields.Selection([('booking','Booking Agent'),('analyst','Analyst Agent')],default='analyst')
    invisible_button = fields.Boolean(string='invisible',default=True)
    def clear_chat(self):
        for rec in self:
            for msg in rec.chat_history:
                self.env['chat.history.warehouse'].create({
                    'user':msg.user,
                    'ai': msg.ai
                    })
                msg.unlink()

    def format_text(self,text):
        print('into formatting',text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = text.replace('\n', '<br>')
        text = re.sub(r'\*\s+(.*?)(?:\n|$)', r'<li>\1</li>', text)
        text = re.sub(r'\#\#(.*?)\s', r'<h1>\1</h1>', text)
        print('foormatted',text)
        return text

    def booking_agent(self):
        if self.box_html:
            # url = "http://smart.nextasolutions.net:8887/ask"
            # url = "http://192.168.1.10:7771/ask"
            url = "http://172.16.16.107:7776/ask"
            # url = "http://192.168.10.27:7777/ask"
            print('--------------------into ask ai')
            payload = {
                "question": self.box_html
            }
            print('ask aiiii q payload', payload)
            response = requests.post(url, json=payload)
            response.raise_for_status()

            answer = response.json().get('answer')
            print('answer',answer)

            if answer:
                formatted_answer = self.format_text(answer)

                self.write({
                    'chat_history': [(0, 0, {
                        'user_html': self.box_html,
                        'ai_html': formatted_answer,
                    })]
                })
            self.box_html = ""


    def analyst_agent(self):
        if self.box_html:
            url = "http://11.11.11.9:7770/ask"
            # url = "http://154.239.10.5:7777/ask"
            print('--------------------into ask ai')
            payload = {
                "question": self.box_html
            }
            print('ask aiiii q payload', payload)
            response = requests.post(url, json=payload)
            response.raise_for_status()

            answer = response.json().get('answer')
            source = response.json().get('source')
            print('answer',answer)
            print('source',source)

            if answer:
                formatted_answer = self.format_text(answer)

                self.write({
                    'chat_history': [(0, 0, {
                        'user_html': self.box_html,
                        'ai_html': formatted_answer,
                    })]
                })
            self.box_html = ""


    def rag_ai_chat(self):
        for record in self:
            html = ['''
                <div class="chat-interface">
                    <div class="chat-header">
                        <div class="header-avatar">
                            <img src="/booking/static/src/img/bot-avatar.png" alt="Medical Assistant"/>
                        </div>
                        <div class="header-info">
                            <h3>Medical Assistant</h3>
                            <span class="status">Online</span>
                        </div>
                    </div>
                    <div class="chat-messages" id="chat-messages">
            ''']

            for msg in record.chat_history:
                if msg.user_html:
                    html.append(f'''
                        <div class="message-wrapper user-message">
                            <div class="message">
                                <div class="message-content">{msg.user_html}</div>
                                <div class="message-meta">
                                    <span class="time">{msg.create_date.strftime('%I:%M %p')}</span>
                                    <span class="status">✓</span>
                                </div>
                            </div>
                        </div>
                    ''')
                if msg.ai_html:
                    html.append(f'''
                        <div class="message-wrapper assistant-message">
                            <div class="avatar">
                                <img src="/booking/static/src/img/bot-avatar.png" alt="Assistant"/>
                            </div>
                            <div class="message">
                                <div class="message-content">{msg.ai_html}</div>
                                <div class="message-meta">
                                    <span class="time">{msg.create_date.strftime('%I:%M %p')}</span>
                                </div>
                            </div>
                        </div>
                    ''')

            html.append('''
                    </div>

                </div>
            ''')
            record.chat = Markup(''.join(html))


    @api.model
    def create(self, vals):
        result = super(ChatLLM, self).create(vals)
        result.invisible_button =False

        return result

class ChatHistory(models.Model):
    _name = "chat.history"

    user = fields.Char(string= 'User')
    ai = fields.Char(string= 'AI')
    user_html = fields.Html(string= 'User')
    ai_html = fields.Html(string= 'AI')
    # ai_res = fields.Text(string= 'AI')
    chat = fields.Many2one('llm.chat')
    subject = fields.Char(string= 'Course')

    @api.model
    def create(self, vals):
        result = super(ChatHistory, self).create(vals)

        return result


class ChatHistoryWarehouse(models.Model):
    _name = "chat.history.warehouse"

    user = fields.Char(string= 'User')
    ai = fields.Char(string= 'AI')
    subject = fields.Char(string= 'Course')
    chat = fields.Many2one('llm.chat')

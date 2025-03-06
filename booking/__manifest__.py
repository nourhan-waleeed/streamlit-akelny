# -*- coding: utf-8 -*-
{
    'name': "booking",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'depends': ['base', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'views/chat_llm.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'booking/static/src/css/chat_styles.css',
            'booking/static/src/css/style.scss',
            'booking/static/src/img/send.png',
            'booking/static/src/js/msg_formatting.js',

        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,

}

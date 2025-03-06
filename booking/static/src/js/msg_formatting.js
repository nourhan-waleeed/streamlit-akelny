/** @odoo-module **/

import { registry } from "@web/core/registry";

console.log("msg formatting loaded and executed!");
let typing = false;
registry.category("services").add("formatting_sheet_handler", {
    dependencies: ["action"],
    start(env) {
    msgFormatting();
        env.bus.addEventListener("ACTION_MANAGER:UI-UPDATED", () => {
            console.log('------------------')
                setTimeout(initializeObservers, 100);

                    });
    }
});


function startObserving() {
    console.log('start observing');

    const sendButton = document.querySelector('.send_message');
    const msgs = document.querySelectorAll('.message_content');


    if(sendButton){
    console.log('button found');
        sendButton.addEventListener('click', () => {
            console.log('send button clicked');
            if (msgs) {
                setTimeout(() => {
                    console.log('Msgs found',msgs);
                    msgFormatting(); }, 5000);
            }
});



    }

};





function initializeObservers() {
    setTimeout(() => {
        startObserving();
    }, 500);
}




window.msgFormatting = msgFormatting;
window.msgFormattingOnchange = msgFormattingOnchange;

function msgFormattingOnchange(msg){
    console.log('onnchangeeee',msg);

}
function msgFormatting(){
    console.log('into formatting');
    const chatContainer = document.querySelector('.chat-container');
    const msgs = document.querySelectorAll('.message_content');
    console.log('chat',chatContainer);
    if (msgs) {
        console.log('there are messages',msgs);
        msgs.forEach((msg, index) => {
            console.log(`msg ${index + 1}:`, msg.textContent);
            msg.innerHTML = styleMsgs(msg.textContent);

            });
}
}

function styleMsgs(msg){
    console.log('into style');
    let formattedText = msg.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedText = formattedText.replace(/\n/g, '<br>');
    formattedText = formattedText.replace(/\*\s+(.*?)(?:\n|$)/g, '<li>$1</li>');
    formattedText = formattedText.replace(/\#\#(.*?) /g, '<h1>$1</h1>');


    return formattedText;

}



// 全局变量
let sessionId = null;
let isDeepThink = false;
let isWebSearch = false;

// DOM 元素（将在DOMContentLoaded中初始化）
let chatContainer, messageInput, sendBtn, attachBtn, deepThinkBtn, webSearchBtn;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 获取DOM元素
    chatContainer = document.getElementById('chatContainer');
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    attachBtn = document.getElementById('attachBtn');
    deepThinkBtn = document.getElementById('deepThinkBtn');
    webSearchBtn = document.getElementById('webSearchBtn');
    
    // 检查元素是否存在
    if (!chatContainer || !messageInput || !sendBtn) {
        console.error('无法找到必要的DOM元素');
        return;
    }
    
    // 创建新会话
    createNewSession();
    
    // 绑定事件
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 自动调整输入框高度
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
    
    // 选项按钮
    if (deepThinkBtn) {
        deepThinkBtn.addEventListener('click', () => {
            isDeepThink = !isDeepThink;
            deepThinkBtn.classList.toggle('active', isDeepThink);
        });
    }
    
    if (webSearchBtn) {
        webSearchBtn.addEventListener('click', () => {
            isWebSearch = !isWebSearch;
            webSearchBtn.classList.toggle('active', isWebSearch);
        });
    }
    
    // 附件按钮（暂时不实现功能）
    if (attachBtn) {
        attachBtn.addEventListener('click', () => {
            alert('附件功能暂未实现');
        });
    }
});

// 创建新会话
async function createNewSession() {
    try {
        const response = await fetch('/api/session/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        sessionId = data.session_id;
    } catch (error) {
        console.error('创建会话失败:', error);
    }
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // 禁用输入和发送按钮
    messageInput.disabled = true;
    sendBtn.disabled = true;
    
    // 添加用户消息到界面
    addMessage(message, 'user');
    
    // 清空输入框
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // 显示加载动画
    const loadingId = addLoadingMessage();
    
    try {
        // 构建请求体
        const requestBody = {
            message: message,
            session_id: sessionId
        };
        
        // 如果选择了深度思考或联网搜索，可以在这里添加参数
        if (isDeepThink) {
            requestBody.deep_think = true;
        }
        if (isWebSearch) {
            requestBody.web_search = true;
        }
        
        // 发送请求
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        // 移除加载动画
        removeLoadingMessage(loadingId);
        
        // 添加AI回复
        if (data.response) {
            addMessage(data.response, 'ai');
        } else if (data.error) {
            addMessage('抱歉，发生了错误：' + data.error, 'ai');
        } else {
            addMessage('抱歉，没有收到回复', 'ai');
        }
        
        // 更新会话ID（如果返回了新的）
        if (data.session_id) {
            sessionId = data.session_id;
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        removeLoadingMessage(loadingId);
        addMessage('抱歉，网络错误，请稍后重试', 'ai');
    } finally {
        // 恢复输入和发送按钮
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// 添加消息到界面
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;
    
    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = getCurrentTime();
    
    messageDiv.appendChild(bubble);
    messageDiv.appendChild(time);
    
    chatContainer.appendChild(messageDiv);
    
    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageDiv;
}

// 添加加载动画
function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    messageDiv.id = 'loading-' + Date.now();
    
    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.innerHTML = `
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
    `;
    
    messageDiv.appendChild(loading);
    chatContainer.appendChild(messageDiv);
    
    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageDiv.id;
}

// 移除加载动画
function removeLoadingMessage(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

// 获取当前时间
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

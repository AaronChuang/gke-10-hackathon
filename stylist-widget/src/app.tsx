import { useState, useEffect, useRef } from 'preact/hooks';
import { initializeApp } from "firebase/app";
import { getFirestore, doc, onSnapshot, Firestore } from "firebase/firestore";
import { marked } from 'marked';
import { FC } from 'preact/compat';
import { firebaseConfig } from './firebaseConfig';

function generateUUIDv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0,
          v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

const getOrSetUserId = (): string => {
    const STORAGE_KEY = 'ai_stylist_user_id';
    let userId = localStorage.getItem(STORAGE_KEY);
    if (!userId) {
        userId = typeof crypto.randomUUID === 'function'
            ? crypto.randomUUID()
            : generateUUIDv4();
        localStorage.setItem(STORAGE_KEY, userId);
    }
    return userId;
};

// 訊息類型定義
interface Message {
    id: string;
    type: 'user' | 'ai' | 'system';
    content: string;
    timestamp: Date;
    isLoading?: boolean;
}

// 快捷按鈕定義
const QUICK_ACTIONS = [
    '換個休閒風',
    '適合上班的搭配',
    '有其他鞋子建議嗎？',
    '適合約會的造型',
    '換個顏色搭配'
];


interface FloatingButtonProps {
    onClick: () => void;
    isOpen: boolean;
    hasUnread?: boolean;
}

const FloatingButton: FC<FloatingButtonProps> = ({ onClick, isOpen, hasUnread }) => (
    <button onClick={onClick} className={`ai-widget-fab ${hasUnread ? 'has-unread' : ''}`}>
        {isOpen ? (
            <svg className="ai-widget-fab-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        ) : (
            <svg className="ai-widget-fab-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
        )}
    </button>
);

// 訊息氣泡組件
interface MessageBubbleProps {
    message: Message;
}

const MessageBubble: FC<MessageBubbleProps> = ({ message }) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    
    return (
        <div className={`message-bubble ${isUser ? 'user' : isSystem ? 'system' : 'ai'}`}>
            <div className="message-content">
                {message.isLoading ? (
                    <div className="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                ) : (
                    <div dangerouslySetInnerHTML={{ __html: message.content }} />
                )}
            </div>
            <div className="message-time">
                {message.timestamp.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}
            </div>
        </div>
    );
};

// 快捷按鈕組件
interface QuickActionsProps {
    onActionClick: (action: string) => void;
    disabled: boolean;
}

const QuickActions: FC<QuickActionsProps> = ({ onActionClick, disabled }) => (
    <div className="quick-actions">
        {QUICK_ACTIONS.map((action, index) => (
            <button 
                key={index}
                className="quick-action-btn"
                onClick={() => onActionClick(action)}
                disabled={disabled}
            >
                {action}
            </button>
        ))}
    </div>
);

// 輸入框組件
interface ChatInputProps {
    onSendMessage: (message: string) => void;
    disabled: boolean;
}

const ChatInput: FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
    const [inputValue, setInputValue] = useState('');
    
    const handleSend = () => {
        if (inputValue.trim() && !disabled) {
            onSendMessage(inputValue.trim());
            setInputValue('');
        }
    };
    
    const handleKeyPress = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };
    
    return (
        <div className="chat-input-container">
            <div className="input-wrapper">
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue((e.target as HTMLInputElement).value)}
                    onKeyPress={handleKeyPress}
                    placeholder="輸入您的問題..."
                    disabled={disabled}
                    className="chat-input"
                />
                <button 
                    onClick={handleSend}
                    disabled={disabled || !inputValue.trim()}
                    className="send-btn"
                >
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                </button>
            </div>
        </div>
    );
};

// 主對話視窗組件
interface ChatWindowProps {
    isOpen: boolean;
    messages: Message[];
    productTitle: string;
    onClose: () => void;
    onSendMessage: (message: string) => void;
    isProcessing: boolean;
}

const ChatWindow: FC<ChatWindowProps> = ({ 
    isOpen, 
    messages, 
    productTitle, 
    onClose, 
    onSendMessage,
    isProcessing 
}) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
    
    if (!isOpen) return null;

    return (
        <div className="ai-widget-window">
            <header className="ai-widget-header">
                <div className="header-info">
                    <div className="ai-avatar">🤖</div>
                    <div>
                        <h3 className="ai-widget-header-title">AI 造型師</h3>
                        <div className="product-info">{productTitle}</div>
                    </div>
                </div>
                <button onClick={onClose} className="ai-widget-close-btn">&times;</button>
            </header>
            
            <div className="chat-messages">
                {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
            </div>
            
            <QuickActions 
                onActionClick={onSendMessage} 
                disabled={isProcessing}
            />
            
            <ChatInput 
                onSendMessage={onSendMessage}
                disabled={isProcessing}
            />
        </div>
    );
};




export const App: FC = () => {
    const [isOpen, setIsOpen] = useState<boolean>(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [productTitle, setProductTitle] = useState<string>('');
    const [isProcessing, setIsProcessing] = useState<boolean>(false);
    const [hasUnread, setHasUnread] = useState<boolean>(false);

    const [userId] = useState<string>(getOrSetUserId());
    const unsubscribeRef = useRef<() => void | null>(null);
    const dbRef = useRef<Firestore | null>(null);
    const currentTaskId = useRef<string | null>(null);

    useEffect(() => {
        try {
            const app = initializeApp(firebaseConfig);
            dbRef.current = getFirestore(app);
        } catch (e) {
            console.error("Firebase init failed:", e);
            addMessage('system', '無法初始化 AI 服務，請重新整理頁面。');
        }
    }, [firebaseConfig]);

    // 添加訊息的輔助函數
    const addMessage = (type: 'user' | 'ai' | 'system', content: string, isLoading = false): string => {
        const messageId = generateUUIDv4();
        const newMessage: Message = {
            id: messageId,
            type,
            content,
            timestamp: new Date(),
            isLoading
        };
        
        setMessages(prev => [...prev, newMessage]);
        
        if (type === 'ai' && !isOpen) {
            setHasUnread(true);
        }
        
        return messageId;
    };
    
    // 更新訊息的輔助函數
    const updateMessage = (messageId: string, content: string, isLoading = false) => {
        setMessages(prev => prev.map(msg => 
            msg.id === messageId 
                ? { ...msg, content, isLoading }
                : msg
        ));
    };
    
    useEffect(() => {
        // 更全面的產品標題檢測
        const selectors = [
            'h1.product-name',
            'h1.product-title', 
            '.product-name',
            '.product-title',
            'h1',
            '[data-product-title]',
            '.pdp-product-name',
            '.item-title'
        ];
        
        let productName = '未知商品';
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent?.trim()) {
                productName = element.textContent.trim();
                break;
            }
        }
        
        // 如果還是找不到，嘗試從 meta 標籤或 title 取得
        if (productName === '未知商品') {
            const metaTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content');
            const pageTitle = document.title;
            
            if (metaTitle) {
                productName = metaTitle;
            } else if (pageTitle && !pageTitle.includes('首頁') && !pageTitle.includes('Home')) {
                productName = pageTitle.split('|')[0].split('-')[0].trim();
            }
        }
        
        setProductTitle(productName);
        
        // 添加初始問候語
        setTimeout(() => {
            addMessage('ai', `嗨！我是您的專屬 AI 造型師 👋<br/>我可以為這件「${productName}」提供什麼樣的搭配建議呢？`);
        }, 500);
    }, []);

    const handleToggle = () => {
        setIsOpen(!isOpen);
        if (!isOpen) {
            setHasUnread(false);
        }
    };

    const handleSendMessage = async (userMessage: string) => {
        // 添加用戶訊息
        addMessage('user', userMessage);
        
        // 添加 AI 載入中訊息
        const loadingMessageId = addMessage('ai', '', true);
        
        setIsProcessing(true);
        
        try {
            // 取消之前的訂閱
            if (unsubscribeRef.current) unsubscribeRef.current();
            
            // 構建對話歷史
            const conversationHistory = messages
                .filter(msg => msg.type !== 'system' && !msg.isLoading)
                .map(msg => ({
                    sender: msg.type === 'user' ? 'user' : 'ai',
                    text: msg.content.replace(/<[^>]*>/g, '') // 移除 HTML 標籤
                }));
            
            // 使用新的對話式 API
            const response = await fetch('http://34.160.253.241:8000/api/conversation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    user_prompt: userMessage,
                    conversation_history: conversationHistory,
                    product_context: {
                        name: productTitle,
                        description: `用戶正在瀏覽的商品：${productTitle}`
                    }
                })
            });

            if (!response.ok) throw new Error(`API 請求失敗: ${response.statusText}`);

            const data = await response.json();
            const taskId = data.task_id;
            const agentResponse = data.agent_response;
            const action = data.action;
            
            currentTaskId.current = taskId;

            // 如果是直接回覆，立即顯示結果
            if (action === 'DIRECT_REPLY') {
                setIsProcessing(false);
                const htmlResult = await marked.parse(agentResponse || '');
                updateMessage(loadingMessageId, htmlResult);
                return;
            }

            // 如果是委派，先顯示安撫性回應，然後監聽任務狀態
            if (action === 'DELEGATED') {
                const htmlResult = await marked.parse(agentResponse || '');
                updateMessage(loadingMessageId, htmlResult);
                
                const taskDocRef = doc(dbRef.current!, "tasks", taskId);

                unsubscribeRef.current = onSnapshot(taskDocRef, async (doc) => {
                    if (doc.exists()) {
                        const task = doc.data();
                        if (task.status === 'COMPLETED' && task.stylist_output) {
                            setIsProcessing(false);
                            const finalResult = await marked.parse(task.stylist_output || '');
                            // 添加新的 AI 回應而不是更新載入訊息
                            addMessage('ai', finalResult);
                            if (unsubscribeRef.current) unsubscribeRef.current();
                        } else if (task.status === 'FAILED') {
                            setIsProcessing(false);
                            addMessage('ai', `抱歉，處理您的請求時發生錯誤：${task.error_message || '未知錯誤'}`);
                            if (unsubscribeRef.current) unsubscribeRef.current();
                        }
                    }
                });
            }

        } catch (err: any) {
            setIsProcessing(false);
            const errorMessage = err.message || '網路連線錯誤，請稍後再試';
            updateMessage(loadingMessageId, `抱歉，發生了錯誤：${errorMessage}`);
            console.error('Widget API Error:', err);
        }
    };

    return (
        <div className="ai-widget-container">
            <ChatWindow 
                isOpen={isOpen}
                messages={messages}
                productTitle={productTitle}
                onClose={() => setIsOpen(false)}
                onSendMessage={handleSendMessage}
                isProcessing={isProcessing}
            />
            <FloatingButton 
                onClick={handleToggle} 
                isOpen={isOpen}
                hasUnread={hasUnread}
            />
        </div>
    );
}

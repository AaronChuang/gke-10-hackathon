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
    const STORAGE_KEY = 'ai_user_id';
    let userId = localStorage.getItem(STORAGE_KEY);
    if (!userId) {
        userId = typeof crypto.randomUUID === 'function'
            ? crypto.randomUUID()
            : generateUUIDv4();
        localStorage.setItem(STORAGE_KEY, userId);
    }
    return userId;
};

// Message type definition
interface Message {
    id: string;
    type: 'user' | 'ai' | 'system';
    content: string;
    timestamp: Date;
    isLoading?: boolean;
}

// Quick action buttons definition
const QUICK_ACTIONS = [
    'Tell me about this product',
    'What are the key features?',
    'How does this compare to alternatives?',
    'Is this suitable for my needs?',
    'What should I consider before buying?'
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

// Message bubble component
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

// Quick actions component
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

// Chat input component
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
                    placeholder="Type your question..."
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

// Main chat window component
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
                        <h3 className="ai-widget-header-title">AI Assistant</h3>
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
            addMessage('system', 'Unable to initialize AI service. Please refresh the page.');
        }
    }, [firebaseConfig]);

    // Helper function to add messages
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
    
    // Helper function to update messages
    const updateMessage = (messageId: string, content: string, isLoading = false) => {
        setMessages(prev => prev.map(msg => 
            msg.id === messageId 
                ? { ...msg, content, isLoading }
                : msg
        ));
    };
    
    useEffect(() => {
        // Comprehensive product title detection
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
        
        let productName = 'Unknown Product';
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent?.trim()) {
                productName = element.textContent.trim();
                break;
            }
        }
        
        // If still not found, try to get from meta tags or title
        if (productName === 'Unknown Product') {
            const metaTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content');
            const pageTitle = document.title;
            
            if (metaTitle) {
                productName = metaTitle;
            } else if (pageTitle && !pageTitle.includes('Home') && !pageTitle.includes('首頁')) {
                productName = pageTitle.split('|')[0].split('-')[0].trim();
            }
        }
        
        setProductTitle(productName);
        
        // Add initial greeting
        setTimeout(() => {
            addMessage('ai', `Hi! I'm your AI Assistant 👋<br/>I'm here to help you learn more about "${productName}". What would you like to know?`);
        }, 500);
    }, []);

    const handleToggle = () => {
        setIsOpen(!isOpen);
        if (!isOpen) {
            setHasUnread(false);
        }
    };

    const handleSendMessage = async (userMessage: string) => {
        // Add user message
        addMessage('user', userMessage);
        
        // Add AI loading message
        const loadingMessageId = addMessage('ai', '', true);
        
        setIsProcessing(true);
        
        try {
            // Cancel previous subscription
            if (unsubscribeRef.current) unsubscribeRef.current();
            
            // Build conversation history - corrected field name to text
            const conversationHistory = messages
                .filter(msg => msg.type !== 'system' && !msg.isLoading)
                .map(msg => ({
                    sender: msg.type === 'user' ? 'user' : 'ai',
                    text: msg.content.replace(/<[^>]*>/g, '') // Remove HTML tags
                }));
            
            // Use GKE ingress endpoint for conversation API
            const response = await fetch('http://104.155.232.179/conversation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    user_prompt: userMessage,
                    conversation_history: conversationHistory,
                    product_context: {
                        name: productTitle,
                        description: `Product the user is browsing: ${productTitle}`
                    }
                })
            });

            if (!response.ok) throw new Error(`API request failed: ${response.statusText}`);

            const data = await response.json();
            const taskId = data.task_id;
            const agentResponse = data.agent_response;
            const action = data.action;
            
            currentTaskId.current = taskId;

            // If direct reply, show result immediately
            if (action === 'DIRECT_REPLY') {
                setIsProcessing(false);
                const htmlResult = await marked.parse(agentResponse || '');
                updateMessage(loadingMessageId, htmlResult);
                return;
            }

            // If task delegated, show reassuring response first, then monitor task status
            if (action === 'TASK_DELEGATED') {
                const htmlResult = await marked.parse(agentResponse || '');
                updateMessage(loadingMessageId, htmlResult);
                
                const taskDocRef = doc(dbRef.current!, "tasks", taskId);

                unsubscribeRef.current = onSnapshot(taskDocRef, async (doc) => {
                    if (doc.exists()) {
                        const task = doc.data();
                        if (task.status === 'COMPLETED' && task.stylist_output) {
                            setIsProcessing(false);
                            const finalResult = await marked.parse(task.stylist_output || '');
                            // Add new AI response instead of updating loading message
                            addMessage('ai', finalResult);
                            if (unsubscribeRef.current) unsubscribeRef.current();
                        } else if (task.status === 'FAILED') {
                            setIsProcessing(false);
                            addMessage('ai', `Sorry, an error occurred while processing your request: ${task.error_message || 'Unknown error'}`);
                            if (unsubscribeRef.current) unsubscribeRef.current();
                        }
                    }
                });
            }

        } catch (err: any) {
            setIsProcessing(false);
            const errorMessage = err.message || 'Network connection error, please try again later';
            updateMessage(loadingMessageId, `Sorry, an error occurred: ${errorMessage}`);
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

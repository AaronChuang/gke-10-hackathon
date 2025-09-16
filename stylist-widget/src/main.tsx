import { render } from 'preact';
import { App } from './app';
import customWidgetStyles from './widget.css?inline';

declare global {
    interface Window {
        aiStylistWidgetInitialized?: boolean;
    }
}

class AIStylistWidget {
    private container: HTMLElement | null = null;
    private shadowRoot: ShadowRoot | null = null;
    private isInitialized = false;

    constructor() {
        this.init();
    }

    private init() {
        if (this.isInitialized || window.aiStylistWidgetInitialized) {
            console.log("AI Stylist Widget has already been initialized.");
            return;
        }

        window.aiStylistWidgetInitialized = true;
        this.isInitialized = true;

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createWidget());
        } else {
            this.createWidget();
        }
    }

    private createWidget() {
        try {
            // 創建容器
            this.container = document.createElement('div');
            this.container.id = 'ai-stylist-widget-root';
            this.container.style.cssText = `
                position: fixed;
                bottom: 0;
                right: 0;
                z-index: 2147483647;
                pointer-events: none;
            `;
            
            // 創建 Shadow DOM
            this.shadowRoot = this.container.attachShadow({ mode: 'open' });
            
            // 添加樣式到 Shadow DOM
            const styleElement = document.createElement('style');
            styleElement.textContent = customWidgetStyles;
            this.shadowRoot.appendChild(styleElement);
            
            // 創建掛載點
            const mountPoint = document.createElement('div');
            mountPoint.style.cssText = 'pointer-events: auto;';
            this.shadowRoot.appendChild(mountPoint);
            
            // 掛載到頁面
            document.body.appendChild(this.container);
            
            // 渲染 React 組件
            render(<App />, mountPoint);
            
            console.log('AI Stylist Widget initialized successfully');
        } catch (error) {
            console.error('Failed to initialize AI Stylist Widget:', error);
        }
    }

    public destroy() {
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
            this.container = null;
            this.shadowRoot = null;
            this.isInitialized = false;
            window.aiStylistWidgetInitialized = false;
        }
    }
}

// 初始化 widget
new AIStylistWidget();

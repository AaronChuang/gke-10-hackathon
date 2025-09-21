import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zhTW from './locales/zh-TW.json'

const messages = {
  en,
  'zh-TW': zhTW
}

const i18n = createI18n({
  legacy: false,
  locale: 'en', // 預設語言為英文
  fallbackLocale: 'en',
  messages,
  globalInjection: true
})

export default i18n

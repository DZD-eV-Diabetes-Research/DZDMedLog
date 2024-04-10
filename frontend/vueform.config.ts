import de from '@vueform/vueform/locales/de'
import vueform from '@vueform/vueform/dist/vueform'
import { defineConfig } from '@vueform/vueform'
import axios from 'axios'


axios.defaults.headers.post = {
  'Content-Type': 'application/json'
}

import '@vueform/vueform/dist/vueform.css';

export default defineConfig({
  theme: vueform,
  locales: { de },
  locale: 'de',
  axios
})
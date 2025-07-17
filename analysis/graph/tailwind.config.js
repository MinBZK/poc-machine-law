/** @type {import('tailwindcss').Config} */

import forms from '@tailwindcss/forms';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  safelist: [],
  theme: {
    extend: {},
  },
  plugins: [forms],
};

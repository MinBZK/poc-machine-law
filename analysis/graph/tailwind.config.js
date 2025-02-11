/** @type {import('tailwindcss').Config} */

import forms from '@tailwindcss/forms';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  safelist: [
    // See Dropdown.svelte and routes/+page.svelte
    {
      pattern: /text-(slate|emerald|rose|blue|amber|teal|violet|cyan|indigo)-600/,
    },
    {
      pattern: /text-(slate|emerald|rose)-700/,
      variants: ['hover'],
    },
    {
      pattern: /bg-(slate|emerald|rose)-50/,
      variants: ['hover'],
    },
    {
      pattern: /border-(slate|emerald|rose|blue|amber|teal|violet|cyan|indigo)-300/,
    },
    {
      pattern: /border-(slate|emerald|rose)-400/,
      variants: ['hover'],
    },
  ],
  theme: {
    extend: {},
  },
  plugins: [forms],
};

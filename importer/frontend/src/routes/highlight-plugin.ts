import rehypeHighlight from 'rehype-highlight';
import yaml from 'highlight.js/lib/languages/yaml';
import type { Plugin } from 'svelte-exmarkdown/types';

export const highlightPlugin: Plugin = {
    rehypePlugin: [rehypeHighlight, { languages: { yaml } }],
};

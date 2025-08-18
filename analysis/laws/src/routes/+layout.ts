export const ssr = false;
export const prerender = false;

import type { LayoutLoad } from './$types';
import { resolve } from '$app/paths';
import type { Law } from '../app';
import yaml from 'js-yaml';

export const load: LayoutLoad = async ({ fetch }) => {
  const res = await fetch('/laws/list');
  const urls = await res.json() as string[];

  // Fetching laws from the provided URLs
  const laws: Law[] = await Promise.all(
    urls.map(async (url: string) => {
      const lawRes = await fetch(resolve(`/law/${url}`));
      if (!lawRes.ok) {
        throw new Error(`Failed to fetch law from ${url}`);
      }
      const text = await lawRes.text();
      const law = yaml.load(text) as Law;
      law.source = text; // Store the original YAML source
      return law;
    })
  );

  return { laws };
};

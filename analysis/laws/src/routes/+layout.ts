export const ssr = false;
export const prerender = false;

import type { LayoutLoad } from './$types';
import { resolve } from '$app/paths';
import type { Law } from '../app';
import yaml from 'js-yaml';

export const load: LayoutLoad = async ({ fetch }) => {
  const res = await fetch('/laws/list');
  const paths = await res.json() as string[];

  // Fetching laws from the provided paths
  const laws: Law[] = await Promise.all(
    paths.map(async (path: string) => {
      const lawRes = await fetch(resolve(`/law/${path}`));
      if (!lawRes.ok) {
        throw new Error(`Failed to fetch law from ${path}`);
      }
      const text = await lawRes.text();
      const law = yaml.load(text) as Law;
      law.path = path; // Store the path to the law file
      law.source = text; // Store the original YAML source
      return law;
    })
  );

  return { laws };
};

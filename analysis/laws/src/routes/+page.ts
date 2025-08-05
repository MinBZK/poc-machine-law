import type { PageLoad } from './$types';
import { resolve } from '$app/paths';
import type { Law } from '../app';
import yaml from 'js-yaml';

export const load: PageLoad = async ({ fetch }) => {
	// @ts-expect-error ts(2345) // The type definition for `resolve` seems incorrect
	const res = await fetch(resolve('/temp.json'));
	const urls = await res.json() as string[];

  // Fetching laws from the provided URLs
  const laws: Law[] = await Promise.all(
    urls.map(async (url: string) => {
	    // @ts-expect-error ts(2345) // The type definition for `resolve` seems incorrect
      const lawRes = await fetch(resolve(`/law/${url}`));
      if (!lawRes.ok) {
        throw new Error(`Failed to fetch law from ${url}`);
      }
      const text = await lawRes.text();
      return yaml.load(text) as Law;
    })
  );

	return { laws };
};

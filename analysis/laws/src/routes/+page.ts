import { resolve } from '$app/paths';
import type { PageData } from './$types';

export const load: PageData = async ({ fetch }: { fetch: any }) => {
	// @ts-expect-error ts(2345) // The type definition for `resolve` seems incorrect
	const res = await fetch(resolve('/temp.json'));
	const laws = await res.json();
	return { laws };
};

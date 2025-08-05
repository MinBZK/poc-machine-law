<script lang="ts">
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';
	import type { Law } from '../app';

	export let data: PageData;
	const laws: Law[] = data.laws;
	
	// Group laws by name
	const lawsByName: Record<string, Law[]> = {};
	laws.forEach(law => {
		if (!lawsByName[law.name]) {
			lawsByName[law.name] = [];
		}
		lawsByName[law.name].push(law);
	});

	// Sort laws within each group by valid_from date
	Object.values(lawsByName).forEach(versions => {
		versions.sort((a, b) => new Date(b.valid_from).getTime() - new Date(a.valid_from).getTime());
	});
</script>

<svelte:head>
	<title>Law inspector — Burger.nl</title>
</svelte:head>

<h1>Available laws</h1>

<ul>
	{#each Object.entries(lawsByName) as [name, versions]}
		<li>
			<span class="font-semibold">{name}</span>
			<ul class="ml-3 mt-1 mb-3">
				{#each versions as version}
					<li>
            {/* @ts-ignore: ts(2345) since the type definition for `resolve` seems incorrect */ null}
						<a href={resolve(`/law/${version.uuid}`)}>
							{new Date(version.valid_from).toLocaleDateString('nl-NL')} ({version.service})
						</a>
					</li>
				{/each}
			</ul>
		</li>
	{/each}
</ul>

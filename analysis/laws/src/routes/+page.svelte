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

<div class="max-w-6xl mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Available laws</h1>

	<div class="grid gap-6">
		{#each Object.entries(lawsByName) as [name, versions]}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h2 class="text-xl font-bold mb-2">{name}</h2>
				{#if versions[0]?.description}
					<p class="text-gray-600 mb-4">{versions[0].description}</p>
				{/if}
				
				<div class="space-y-3">
					{#each versions as version}
						{/* @ts-ignore: ts(2345) since the type definition for `resolve` seems incorrect */ null}
						<a 
							href={resolve(`/law/${version.uuid}`)}
							class="block p-4 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
						>
							<div class="flex items-center justify-between">
								<div>
									<span class="font-medium">{version.service}</span>
									<div class="text-sm text-gray-500">
										Geldig vanaf: {new Date(version.valid_from).toLocaleDateString('nl-NL')}
									</div>
									{#if version.legal_basis}
										<div class="text-sm text-gray-500 mt-1">
											Wettelijke basis: {version.legal_basis.law} {version.legal_basis.article}
										</div>
									{/if}
								</div>
								<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
								</svg>
							</div>
						</a>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>

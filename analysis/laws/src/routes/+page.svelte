<script lang="ts">
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';
	import type { Law } from '../app';

	export let data: PageData;
	const laws: Law[] = data.laws;
</script>

<svelte:head>
	<title>Law inspector — Burger.nl</title>
</svelte:head>

<h1>Available laws</h1>

<ul>
	{#each laws as law}
    {/* @ts-ignore: ts(2345) since the type definition for `resolve` seems incorrect */ null}
		<li><a href={resolve(`/law/${law.uuid}`)}>{law.name}</a></li>
	{/each}
</ul>

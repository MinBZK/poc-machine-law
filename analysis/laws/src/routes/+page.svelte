<script lang="ts">
    import { resolve } from '$app/paths';
	import type { PageData } from './$types';

	export let data: PageData;
</script>

<svelte:head>
	<title>Law inspector — Burger.nl</title>
</svelte:head>

<h1>Available laws</h1>

<ul>
	{#each data.laws as law}
    {/* @ts-ignore: ts(2345) since the type definition for `resolve` seems incorrect */ null}
		<li><a href="{resolve(`/law/${law}`)}">{law}</a></li>
	{/each}
</ul>

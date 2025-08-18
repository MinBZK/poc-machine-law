<script lang="ts">
  import { page } from '$app/state';
  import type { PageData } from './$types';
  import Prism from 'prismjs';
  const { highlight, languages } = Prism;
  import 'prismjs/components/prism-yaml';
  import 'prismjs/themes/prism-coy.css'; // IMPROVE: use some theme from https://github.com/PrismJS/prism-themes instead?
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import Dropdown from '$lib/Dropdown.svelte';

  let { data }: { data: PageData } = $props();
  const { id } = page.params;

  const law = data.laws.find((law) => law.uuid === id);

  if (!law) {
    throw new Error(`Law with id ${id} not found`);
  }

  // Create the options for the dropdown
  const dropdownOptions = [
    { label: '- Kies een wet -', isHidden: true },
    ...data.laws.map((law) => ({
      value: law.uuid,
      label: `${law.name} (${law.service}), geldig vanaf ${new Date(law.valid_from).toLocaleDateString('nl-NL')}`,
    })),
  ];

  let selectedLaw: string | undefined = $state();

  $effect(() => {
    // Navigate to the selected law comparison when selected
    if (selectedLaw) {
      goto(resolve(`/details/${id}/compare/${selectedLaw}`));
    }
  });
</script>

<svelte:head>
  <title>{law.name} — Law inspector — Burger.nl</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
  <h1 class="mb-2 text-3xl font-bold">{law.name}</h1>

  <a href={resolve('/')} class="mb-6 inline-flex items-center text-blue-600 hover:text-blue-800">
    <svg class="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    Terug naar alle wetten
  </a>

  <p>
    Vergelijk met andere wet: <Dropdown
      options={dropdownOptions}
      bind:value={selectedLaw}
      extraMenuClasses="text-sm"
    />
  </p>

  <div class="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <div class="grid gap-6">
      {#if law.description}
        <div>
          <h2 class="mb-2 text-lg font-semibold">Omschrijving</h2>
          <p>{law.description}</p>
        </div>
      {/if}

      <div>
        <h2 class="mb-2 text-lg font-semibold">Details</h2>
        <dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm font-medium text-gray-500">Dienst</dt>
            <dd class="mt-1">{law.service}</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-gray-500">Geldig vanaf</dt>
            <dd class="mt-1">
              {new Date(law.valid_from).toLocaleDateString('nl-NL')}
            </dd>
          </div>
          {#if law.legal_basis}
            <div class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Wettelijke basis</dt>
              <dd class="mt-1">
                {law.legal_basis.law}
                {law.legal_basis.article}
                {#if law.legal_basis.paragraph}
                  paragraaf {law.legal_basis.paragraph}
                {/if}
                {#if law.legal_basis.url}
                  <a
                    href={law.legal_basis.url}
                    target="_blank"
                    rel="nofollow noopener noreferrer"
                    class="ml-2 text-blue-600 hover:text-blue-800">(link)</a
                  >
                {/if}
              </dd>
            </div>
          {/if}
        </dl>
      </div>

      {#if law.properties?.parameters?.length || law.properties?.sources?.length || law.properties?.input?.length || law.properties?.output?.length}
        <h2 class="mb-2 text-lg font-semibold">Eigenschappen</h2>
        <div class="grid gap-6 sm:grid-cols-2">
          {#if law.properties.parameters?.length}
            <div>
              <h3 class="mb-2 text-base font-medium">Parameters</h3>
              <ul class="space-y-3">
                {#each law.properties.parameters as param}
                  <li class="rounded-md bg-gray-50 p-3">
                    <div class="flex items-start justify-between">
                      <div>
                        <p class="font-medium">{param.name}</p>
                        <p class="text-sm text-gray-600">{param.description}</p>
                        <div class="mt-1 flex gap-3 text-xs text-gray-500">
                          <span>Type: {param.type}</span>
                          <span>{param.required ? 'Vereist' : 'Optioneel'}</span>
                        </div>
                      </div>
                    </div>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}

          {#if law.properties.sources?.length}
            <div>
              <h3 class="mb-2 text-base font-medium">Sources</h3>
              <ul class="space-y-3">
                {#each law.properties.sources as source}
                  <li class="rounded-md bg-gray-50 p-3">
                    <div class="flex items-start justify-between">
                      <div>
                        <p class="font-medium">{source.name}</p>
                        <p class="text-sm text-gray-600">{source.description}</p>
                        <div class="mt-1 flex gap-3 text-xs text-gray-500">
                          <span>Type: {source.type}</span>
                          <span>Tijdseenheid: {source.temporal?.type || 'geen'}</span>
                        </div>
                      </div>
                    </div>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}

          {#if law.properties.input?.length}
            <div>
              <h3 class="mb-2 text-base font-medium">Inputs</h3>
              <ul class="space-y-3">
                {#each law.properties.input as input}
                  <li class="rounded-md bg-gray-50 p-3">
                    <div class="flex items-start justify-between">
                      <div>
                        <p class="font-medium">{input.name}</p>
                        <p class="text-sm text-gray-600">{input.description}</p>
                        <div class="mt-1 flex gap-3 text-xs text-gray-500">
                          <span>Type: {input.type}</span>
                          <span>Tijdseenheid: {input.temporal?.type || 'geen'}</span>
                        </div>
                      </div>
                    </div>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}

          {#if law.properties.output?.length}
            <div>
              <h3 class="mb-2 text-base font-medium">Outputs</h3>
              <ul class="space-y-3">
                {#each law.properties.output as output}
                  <li class="rounded-md bg-gray-50 p-3">
                    <div class="flex items-start justify-between">
                      <div>
                        <p class="font-medium">{output.name}</p>
                        <p class="text-sm text-gray-600">{output.description}</p>
                        <div class="mt-1 flex gap-3 text-xs text-gray-500">
                          <span>Type: {output.type}</span>
                          <span>Tijdseenheid: {output.temporal?.type || 'geen'}</span>
                        </div>
                      </div>
                    </div>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      {/if}

      <h2 class="mb-2 text-lg font-semibold">Code</h2>
      <pre class="!rounded-md !bg-gray-50 !px-4 !py-3 !text-sm/6 whitespace-pre-wrap"><code
          >{@html highlight(law.source, languages.yaml, 'yaml')}</code
        ></pre>
    </div>
  </div>
</div>

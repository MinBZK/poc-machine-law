<script lang="ts">
  import { resolve } from '$app/paths';
  import type { LayoutData } from './$types';
  import type { Law } from '../app';

  export let data: LayoutData;
  const laws: Law[] = data.laws;

  // Group laws by name
  const lawsByName: Record<string, Law[]> = {};
  laws.forEach((law) => {
    if (!lawsByName[law.name]) {
      lawsByName[law.name] = [];
    }
    lawsByName[law.name].push(law);
  });

  // Sort laws within each group by valid_from date
  Object.values(lawsByName).forEach((versions) => {
    versions.sort((a, b) => new Date(b.valid_from).getTime() - new Date(a.valid_from).getTime());
  });
</script>

<svelte:head>
  <title>Law inspector — Burger.nl</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
  <h1 class="mb-8 text-3xl font-bold">Beschikbare wetten</h1>

  <div class="grid gap-6">
    {#each Object.entries(lawsByName) as [name, versions]}
      <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 class="mb-2 text-xl font-bold">{name}</h2>
        {#if versions[0]?.description}
          <p class="mb-4 text-gray-600">{versions[0].description}</p>
        {/if}

        <div class="space-y-3">
          {#each versions as version}
            <a
              href={resolve(`/law/${version.uuid}`)}
              class="block rounded-md bg-gray-50 p-4 transition-colors hover:bg-gray-100"
            >
              <div class="flex items-center justify-between">
                <div>
                  <span class="font-medium">{version.service}</span>
                  <div class="text-sm text-gray-500">
                    Geldig vanaf: {new Date(version.valid_from).toLocaleDateString('nl-NL')}
                  </div>
                  {#if version.legal_basis}
                    <div class="mt-1 text-sm text-gray-500">
                      Wettelijke basis: {version.legal_basis.law}
                      {version.legal_basis.article}
                    </div>
                  {/if}
                </div>
                <svg
                  class="h-5 w-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </a>
          {/each}
        </div>
      </div>
    {/each}
  </div>
</div>

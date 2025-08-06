<script lang="ts">
  import { page } from '$app/state';
  import type { PageData } from './$types';
  import Prism from 'prismjs';
  const { highlight, languages } = Prism;
  import 'prismjs/components/prism-yaml';
  import 'prismjs/themes/prism-coy.css';

  export let data: PageData;
  const id = page.params.id;

  const law = data.laws.find((law) => law.uuid === id);

  if (!law) {
    throw new Error(`Law with id ${id} not found`);
  }
</script>

<svelte:head>
  <title>{law.name} — Law inspector — Burger.nl</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
  <h1 class="mb-2 text-3xl font-bold">{law.name}</h1>

  <a href="/" class="mb-6 inline-flex items-center text-blue-600 hover:text-blue-800">
    <svg class="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    Terug naar alle wetten
  </a>

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
            <dt class="text-sm font-medium text-gray-500">Service</dt>
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

      <div>
        <h2 class="mb-2 text-lg font-semibold">Bron</h2>
        <pre class="!rounded-md !bg-gray-50 !px-4 !py-3 !text-sm/6 whitespace-pre-wrap"><code
            >{@html highlight(law.source, languages.yaml, 'yaml')}</code
          ></pre>
      </div>
    </div>
  </div>
</div>

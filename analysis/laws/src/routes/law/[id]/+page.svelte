<script lang="ts">
  import { page } from '$app/state';
  import type { PageData } from './$types';

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
  <h1 class="mb-2 text-3xl font-bold text-gray-800">{law.name}</h1>

  <div class="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <div class="grid gap-6">
      {#if law.description}
        <div>
          <h2 class="mb-2 text-lg font-semibold text-gray-700">Description</h2>
          <p class="text-gray-600">{law.description}</p>
        </div>
      {/if}

      <div>
        <h2 class="mb-2 text-lg font-semibold text-gray-700">Details</h2>
        <dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm font-medium text-gray-500">Service</dt>
            <dd class="mt-1 text-gray-900">{law.service}</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-gray-500">Valid from</dt>
            <dd class="mt-1 text-gray-900">
              {new Date(law.valid_from).toLocaleDateString('nl-NL')}
            </dd>
          </div>
          {#if law.legal_basis}
            <div class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Legal basis</dt>
              <dd class="mt-1 text-gray-900">
                {law.legal_basis.law}
                {law.legal_basis.article}
                {#if law.legal_basis.paragraph}
                  paragraph {law.legal_basis.paragraph}
                {/if}
                {#if law.legal_basis.url}
                  <a
                    href={law.legal_basis.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="ml-2 text-blue-600 hover:text-blue-800">(link)</a
                  >
                {/if}
              </dd>
            </div>
          {/if}
        </dl>
      </div>
    </div>
  </div>
</div>

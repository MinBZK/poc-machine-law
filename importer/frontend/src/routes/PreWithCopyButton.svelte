<script lang="ts">
  let pre: HTMLPreElement;
</script>

<div>
  <button
    class="float-right inline-flex cursor-pointer items-center rounded-sm rounded-b-none bg-gray-800/90 px-1 py-0.5 text-sm text-gray-200 hover:bg-gray-800 hover:text-white"
    type="button"
    on:click={() => navigator.clipboard.writeText(pre.textContent || '')}
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="mr-1.5 h-4 w-4" viewBox="0 0 24 24"
      ><g
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        ><path
          d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3m9-9V7a2 2 0 0 0-2-2h-2m-2 12v-1a1 1 0 0 1 1-1h1m3 0h1a1 1 0 0 1 1 1v1m0 3v1a1 1 0 0 1-1 1h-1m-3 0h-1a1 1 0 0 1-1-1v-1"
        /><path d="M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2" /></g
      ></svg
    > Kopiëren
  </button>
  <pre
    class="clear-right overflow-x-auto rounded-sm rounded-tr-none bg-gray-900 px-3 py-2 text-sm text-white"
    bind:this={pre}><slot /></pre>
</div>

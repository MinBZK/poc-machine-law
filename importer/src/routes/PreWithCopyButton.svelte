<script lang="ts">
  let { children } = $props();

  let pre: HTMLPreElement;

  // Function to download the file
  function downloadFile() {
    // Get the filename from the resourceURL or use a default name
    const filename = 'wet.yaml';

    // Gerenate a blob and create a link to download it
    const blob = new Blob([pre.textContent || ''], { type: 'application/yaml' }); // See e.g. https://httptoolkit.com/blog/yaml-media-type-rfc/ about the media type
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
</script>

<div>
  <button
    class="float-right inline-flex cursor-pointer items-center rounded-tr-sm bg-gray-800/90 px-1.5 py-1 text-sm text-gray-200 hover:bg-gray-800 hover:text-white"
    onclick={downloadFile}
    type="button"
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="mr-1.5 h-5 w-5" viewBox="0 0 24 24"
      ><path
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2M7 11l5 5l5-5m-5-7v12"
      /></svg
    >
    Download
  </button>

  <button
    class="border-r-1 float-right inline-flex cursor-pointer items-center rounded-tl-sm border-gray-500 bg-gray-800/90 px-1.5 py-1 text-sm text-gray-200 hover:bg-gray-800 hover:text-white"
    type="button"
    onclick={() => navigator.clipboard.writeText(pre.textContent || '')}
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="mr-1.5 h-4 w-4" viewBox="0 0 24 24"
      ><g
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        ><path
          d="M7 9.667A2.667 2.667 0 0 1 9.667 7h8.666A2.667 2.667 0 0 1 21 9.667v8.666A2.667 2.667 0 0 1 18.333 21H9.667A2.667 2.667 0 0 1 7 18.333z"
        /><path d="M4.012 16.737A2 2 0 0 1 3 15V5c0-1.1.9-2 2-2h10c.75 0 1.158.385 1.5 1" /></g
      ></svg
    > Kopieer
  </button>
  <pre
    class="clear-right overflow-x-auto whitespace-pre-wrap rounded-sm rounded-tr-none bg-gray-900 px-3 py-2 text-sm text-white"
    bind:this={pre}>{@render children()}</pre>
</div>

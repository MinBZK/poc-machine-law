<script lang="ts">
  import { type NodeProps } from '@xyflow/svelte';

  type $$Props = NodeProps & { data: { label: string } };

  let { data }: $$Props = $props();
</script>

<button
  type="button"
  class="close float-right cursor-pointer rounded-md bg-slate-600 p-1 text-white"
  aria-label="Close"
>
  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
    ><path
      fill="none"
      stroke="currentColor"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M18 6L6 18M6 6l12 12"
    /></svg
  >
</button>

<div class="text-center">{data.label}</div>
